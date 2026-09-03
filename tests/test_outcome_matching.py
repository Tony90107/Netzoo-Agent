from __future__ import annotations

import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.contracts import (  # noqa: E402
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
)
from netzoo_agent_core.routing.outcome_matching import (  # noqa: E402
    has_granularity_only_ambiguity,
    match_outcome_hypotheses,
    match_registry_guidance_features,
    match_semantic_request,
    guidance_actions_for,
    match_requested_outcome,
)


def outcome(**updates) -> RequestedOutcome:
    values = {
        "operation": "infer",
        "artifact_type": "regulatory_network",
        "entity_types": ["mirna", "gene"],
        "display_entities": ["miRNA", "gene"],
        "regulator_types": ["mirna"],
        "target_types": ["gene"],
        "granularity": "sample_specific",
        "unresolved_dimensions": [],
    }
    values.update(updates)
    return RequestedOutcome(**values)


def advisory_hypothesis(
    requested: RequestedOutcome,
    *evidence: OutcomeEvidence,
    assumptions: list[str] | None = None,
) -> OutcomeHypothesis:
    return OutcomeHypothesis(
        outcome=requested,
        confidence=0.9,
        evidence=list(evidence),
        assumptions=assumptions or ["One outcome dimension remains unconfirmed."],
    )


@pytest.mark.parametrize("inputs", [
    ["mutation_matrix", "expression_matrix"],
    ["mutation_matrix", "bipartite_edge_list"],
])
def test_guidance_fallback_cannot_bypass_typed_input_contract(inputs):
    result = match_registry_guidance_features(
        "Gene length normalization and pathway scores for somatic mutations",
        input_artifacts=inputs,
    )

    assert result is None


def test_different_current_inputs_are_not_only_a_granularity_question():
    hypotheses = [
        advisory_hypothesis(outcome(input_artifacts=[artifact], granularity=granularity))
        for artifact, granularity in (
            ("expression_matrix", "aggregate"),
            ("mutation_matrix", "sample_specific"),
        )
    ]

    assert not has_granularity_only_ambiguity(hypotheses)


def test_sample_specific_mirna_regulatory_network_matches_lioness_puma():
    result = match_requested_outcome(outcome())

    assert result.status == "exact"
    assert result.matched_actions == ["run_lioness_puma"]
    assert result.alternative_actions == []
    assert guidance_actions_for("run_lioness_puma") == [
        "run_puma",
        "run_lioness_puma",
    ]


def test_guidance_operation_is_not_required_for_registry_candidate_matching():
    result = match_semantic_request(
        "Which tools can produce a sample-specific miRNA regulatory network?",
        [
            advisory_hypothesis(
                outcome(operation="explain"),
                OutcomeEvidence(
                    dimension="artifact_type",
                    value="regulatory_network",
                    source="explicit",
                    rationale="The requested result is a regulatory network.",
                ),
                OutcomeEvidence(
                    dimension="regulator_type",
                    value="mirna",
                    source="explicit",
                    rationale="The request names miRNA regulators.",
                ),
                OutcomeEvidence(
                    dimension="granularity",
                    value="sample_specific",
                    source="explicit",
                    rationale="The request asks for sample-specific output.",
                ),
            )
        ],
        request_mode="guidance",
    )

    assert result.status == "exact"
    assert result.matched_actions == ["run_lioness_puma"]
    assert result.hypothesis_actions == []


def test_guidance_promotes_one_advisory_candidate_to_an_exact_registry_match():
    result = match_semantic_request(
        "If I want a sample-specific miRNA regulatory network, what tools do I need?",
        [
            OutcomeHypothesis(
                outcome=outcome(operation="unknown"),
                confidence=0.9,
                evidence=[],
                assumptions=["The request is asking for workflow guidance."],
            )
        ],
        request_mode="guidance",
    )

    assert result.status == "exact"
    assert result.matched_actions == ["run_lioness_puma"]
    assert result.hypothesis_actions == []


def test_optional_registry_tags_do_not_make_a_known_scientific_result_ambiguous():
    requested = outcome(unresolved_dimensions=["selection_tag", "registry_tags"])

    result = match_requested_outcome(requested)

    assert result.status == "exact"
    assert result.matched_actions == ["run_lioness_puma"]
    unknown = outcome(granularity="unknown", unresolved_dimensions=["selection_tags", "granularity"])
    assert unknown.unresolved_dimensions == ["granularity"]
    assert match_requested_outcome(unknown).status == "ambiguous"


def test_guidance_stays_ambiguous_when_semantic_roles_are_omitted():
    incomplete = OutcomeHypothesis(
        outcome=outcome(
            operation="unknown",
            entity_types=[],
            display_entities=[],
            regulator_types=[],
        ),
        confidence=0.9,
        evidence=[],
        assumptions=["The semantic model omitted the explicit regulator role."],
    )

    result = match_semantic_request(
        "If I want a sample-specific mi-RNA regulator network, what tools do I need?",
        [incomplete],
        request_mode="guidance",
    )

    assert result.status == "ambiguous"
    assert result.matched_actions == []
    assert result.hypothesis_actions == ["run_lioness_panda", "run_lioness_puma"]


def test_questioned_panda_mention_does_not_override_somatic_mutation_subtyping():
    task = (
        "我剛剛成功用 RNA-Seq 資料跑完了 PANDA。現在拿到 WES 體細胞突變矩陣，"
        "是不是也應該把這份充滿 0 的突變矩陣丟進 PANDA 跟 LIONESS，"
        "來幫病患做亞型分群？"
    )
    requested = RequestedOutcome(
        operation="analyze",
        artifact_type="sample_cluster_assignment",
        entity_types=["sample"],
        granularity="aggregate",
    )

    result = match_semantic_request(
        task,
        [OutcomeHypothesis(outcome=requested, confidence=0.95, evidence=[])],
        request_mode="guidance",
    )

    assert result.status == "exact"
    assert result.matched_actions == ["run_sambar"]


@pytest.mark.parametrize(("task", "inputs", "artifact", "granularity", "expected"), [
    (
        "Previously used SAMBAR on somatic mutations; now infer patient-specific "
        "TF networks from my RNA-Seq expression matrix.",
        ["expression_matrix"], "regulatory_network", "sample_specific", "run_lioness_panda",
    ),
    (
        "Previously used PANDA on RNA-Seq expression; now cluster WES mutation patients.",
        ["mutation_matrix"], "sample_cluster_assignment", "aggregate", "run_sambar",
    ),
])
def test_current_typed_input_is_distinct_from_historical_method_and_data(
    task, inputs, artifact, granularity, expected,
):
    is_network = artifact == "regulatory_network"
    requested = RequestedOutcome(
        operation="infer" if is_network else "analyze",
        input_artifacts=inputs,
        artifact_type=artifact,
        entity_types=["tf", "gene"] if is_network else ["sample"],
        regulator_types=["tf"] if is_network else [],
        target_types=["gene"] if is_network else [],
        granularity=granularity,
    )

    result = match_semantic_request(
        task, [OutcomeHypothesis(outcome=requested, confidence=0.9, evidence=[])],
        request_mode="guidance",
    )

    assert result.status == "exact"
    assert result.matched_actions == [expected]


@pytest.mark.parametrize(("artifact", "inputs", "entities", "regulators", "granularity"), [
    ("sample_cluster_assignment", ["expression_matrix"], ["sample"], [], "aggregate"),
    ("regulatory_network", ["mutation_matrix"], ["tf", "gene"], ["tf"], "sample_specific"),
])
def test_typed_outcome_matching_rejects_incompatible_input_contracts(
    artifact, inputs, entities, regulators, granularity,
):
    result = match_requested_outcome(RequestedOutcome(
        operation="infer" if regulators else "analyze",
        input_artifacts=inputs, artifact_type=artifact, entity_types=entities,
        regulator_types=regulators, granularity=granularity,
    ))

    assert result.status == "unsupported"
    assert result.matched_actions == []
    assert "input_artifacts" in result.mismatch_dimensions


def test_named_method_cannot_override_an_unsupported_scientific_result():
    requested = RequestedOutcome(
        operation="acquire", artifact_type="measurement_dataset",
        entity_types=["protein"], granularity="aggregate",
    )
    result = match_semantic_request(
        "Previously used PANDA. Now download the protein measurement dataset.",
        [OutcomeHypothesis(outcome=requested, confidence=0.95, evidence=[])],
        request_mode="execute",
    )

    assert result.status == "unsupported"
    assert result.matched_actions == []


def test_named_method_cannot_bypass_its_declared_input_contract():
    requested = RequestedOutcome(
        operation="infer", input_artifacts=["mutation_matrix"],
        artifact_type="regulatory_network", entity_types=["tf", "gene"],
        regulator_types=["tf"], target_types=["gene"], granularity="aggregate",
    )
    result = match_semantic_request(
        "Run OTTER directly on this mutation matrix.",
        [OutcomeHypothesis(outcome=requested, confidence=0.95, evidence=[])],
        request_mode="execute",
    )

    assert result.status == "unsupported"
    assert result.matched_actions == []


@pytest.mark.parametrize(("task", "operation", "artifact", "entities", "roles", "granularity", "expected"), [
    ("Previously PANDA; now analyze cohort covariate-adjusted coexpression.", "analyze", "coexpression_network", ["gene"], [], "aggregate", "run_cobra"),
    ("Previously SAMBAR; now analyze bipartite network communities.", "analyze", "community_assignment", ["gene"], [], "not_applicable", "run_condor"),
    ("Previously PUMA; now infer an aggregate two-layer omic network.", "infer", "multi_omic_network", ["omics_layer_1_feature", "omics_layer_2_feature"], [], "aggregate", "run_dragon"),
    ("Previously SAMBAR; now infer patient-specific miRNA regulatory networks.", "infer", "regulatory_network", ["mirna", "gene"], ["mirna"], "sample_specific", "run_lioness_puma"),
    ("Use OTTER for an aggregate TF-to-gene network.", "infer", "regulatory_network", ["tf", "gene"], ["tf"], "aggregate", "run_otter"),
    ("Use PANDA for an aggregate TF-to-gene network.", "infer", "regulatory_network", ["tf", "gene"], ["tf"], "aggregate", "run_panda"),
    ("Use PUMA for an aggregate miRNA-to-gene network.", "infer", "regulatory_network", ["mirna", "gene"], ["mirna"], "aggregate", "run_puma"),
    ("Use BONOBO for sample-specific gene coexpression.", "infer", "coexpression_network", ["gene"], [], "sample_specific", "run_bonobo"),
    ("Use LIONESS-COEXPRESSION for sample-specific gene coexpression.", "infer", "coexpression_network", ["gene"], [], "sample_specific", "run_lioness_coexpression"),
    ("Previously PANDA; now infer TF regulation and sample activity.", "infer", "regulatory_network", ["tf", "gene", "sample"], ["tf"], "aggregate", "run_giraffe"),
])
def test_scientific_goal_and_compatible_name_disambiguation_are_shared_across_workflows(
    task, operation, artifact, entities, roles, granularity, expected,
):
    requested = RequestedOutcome(
        operation=operation, artifact_type=artifact, entity_types=entities,
        regulator_types=roles, target_types=["gene"] if roles else [],
        granularity=granularity,
    )
    result = match_semantic_request(
        task, [OutcomeHypothesis(outcome=requested, confidence=0.95, evidence=[])],
        request_mode="execute",
    )

    assert result.status == "exact"
    assert result.matched_actions == [expected]


def test_incompatible_panda_semantics_cannot_override_mutation_guidance():
    task = (
        "我已經用 RNA-Seq 跑完 PANDA；現在是否能把 WES 體細胞突變矩陣"
        "丟進 PANDA 與 LIONESS，建立病患特異網路並做亞型分群？"
    )
    confused = RequestedOutcome(
        operation="infer",
        artifact_type="regulatory_network",
        entity_types=["tf", "gene"],
        regulator_types=["tf"],
        target_types=["gene"],
        granularity="sample_specific",
    )

    result = match_semantic_request(
        task,
        [OutcomeHypothesis(outcome=confused, confidence=0.9, evidence=[])],
        request_mode="guidance",
    )

    assert result.status == "exact"
    assert result.matched_actions == ["run_sambar"]


def test_sparse_somatic_mutation_guidance_recovers_from_input_output_confusion():
    task = (
        "我手邊有一份 200 個肺癌病患的體細胞突變 (Somatic mutations) 矩陣，"
        "99% 的格子都是 0。我想對病患進行亞型分群 (Subtyping)，"
        "有沒有哪個工具專門處理高度稀疏的 DNA 突變矩陣並進行病患分群？"
    )
    confused = RequestedOutcome(
        operation="analyze",
        artifact_type="mutation_matrix",
        entity_types=["gene", "sample"],
        granularity="sample_specific",
        unresolved_dimensions=["selection_tag"],
    )

    result = match_semantic_request(
        task,
        [OutcomeHypothesis(outcome=confused, confidence=0.9, evidence=[])],
        request_mode="guidance",
    )

    assert result.status == "exact"
    assert result.matched_actions == ["run_sambar"]


def test_execution_matching_does_not_promote_one_advisory_candidate():
    result = match_semantic_request(
        "Build a sample-specific miRNA regulatory network.",
        [
            OutcomeHypothesis(
                outcome=outcome(operation="infer"),
                confidence=0.9,
                evidence=[],
                assumptions=["The input files have not been supplied yet."],
            )
        ],
        request_mode="execute",
    )

    assert result.status == "ambiguous"
    assert result.matched_actions == []
    assert result.hypothesis_actions == ["run_lioness_puma"]


def test_sample_specific_mirna_measurements_are_not_a_workflow_match():
    result = match_requested_outcome(
        outcome(
            operation="acquire",
            artifact_type="measurement_dataset",
            regulator_types=[],
            target_types=[],
        )
    )

    assert result.status == "unsupported"
    assert result.matched_actions == []
    assert result.alternative_actions[0] == "run_lioness_puma"
    assert "operation" in result.mismatch_dimensions
    assert "artifact_type" in result.mismatch_dimensions


def test_unknown_artifact_stays_ambiguous_instead_of_matching():
    result = match_requested_outcome(
        outcome(
            artifact_type="unknown",
            unresolved_dimensions=["requested artifact"],
        )
    )

    assert result.status == "ambiguous"
    assert result.matched_actions == []
    assert result.clarification_question is not None


def test_multiple_end_to_end_matches_require_a_selection_dimension():
    result = match_requested_outcome(
        outcome(
            entity_types=["gene"],
            display_entities=["gene"],
            regulator_types=[],
        )
    )

    assert result.status == "ambiguous"
    assert result.matched_actions == []
    assert "regulator type" in result.clarification_question


def test_unrelated_entity_has_no_suggested_alternative():
    result = match_requested_outcome(
        outcome(
            operation="acquire",
            artifact_type="measurement_dataset",
            entity_types=["protein"],
            display_entities=["protein abundance"],
            regulator_types=[],
            target_types=[],
        )
    )

    assert result.status == "unsupported"
    assert result.alternative_actions == []


def test_unknown_entity_dimension_cannot_match_exactly():
    result = match_requested_outcome(
        outcome(
            entity_types=["unknown"],
            display_entities=[],
            regulator_types=[],
        )
    )

    assert result.status == "ambiguous"
    assert result.matched_actions == []


def test_partial_mirna_sample_network_uniquely_suggests_lioness_puma():
    result = match_outcome_hypotheses(
        [
            advisory_hypothesis(
                outcome(
                    operation="unknown",
                    artifact_type="regulatory_network",
                    entity_types=["mirna"],
                    regulator_types=["mirna"],
                    target_types=[],
                    granularity="sample_specific",
                    unresolved_dimensions=["operation", "target type"],
                ),
                OutcomeEvidence(
                    dimension="regulator_type",
                    value="mirna",
                    source="explicit",
                    rationale="The request explicitly names miRNA.",
                ),
                OutcomeEvidence(
                    dimension="granularity",
                    value="sample_specific",
                    source="explicit",
                    rationale="The request explicitly asks for one network per sample.",
                ),
            )
        ]
    )

    assert result.status == "ambiguous"
    assert result.matched_actions == []
    assert result.hypothesis_actions == ["run_lioness_puma"]


def test_explicit_outcome_evidence_outranks_a_conflicting_inferred_operation():
    result = match_outcome_hypotheses(
        [
            OutcomeHypothesis(
                outcome=outcome(
                    operation="acquire",
                    entity_types=["mirna"],
                    target_types=["unknown"],
                ),
                confidence=0.9,
                evidence=[
                    OutcomeEvidence(
                        dimension="operation",
                        value="acquire",
                        source="inferred",
                        rationale="The surface verb was interpreted as acquisition.",
                    ),
                    OutcomeEvidence(
                        dimension="artifact_type",
                        value="regulatory_network",
                        source="explicit",
                        text_span="regulator network",
                        rationale="The artifact is named by the user.",
                    ),
                    OutcomeEvidence(
                        dimension="regulator_type",
                        value="mirna",
                        source="explicit",
                        text_span="mi-RNA",
                        rationale="The regulator type is named by the user.",
                    ),
                    OutcomeEvidence(
                        dimension="granularity",
                        value="sample_specific",
                        source="explicit",
                        text_span="sample specific",
                        rationale="The granularity is named by the user.",
                    ),
                ],
                assumptions=[],
            )
        ]
    )

    assert result.status == "exact"
    assert result.matched_actions == ["run_lioness_puma"]


def test_explicit_evidence_fallback_stays_ambiguous_when_multiple_workflows_fit():
    result = match_outcome_hypotheses(
        [
            OutcomeHypothesis(
                outcome=outcome(
                    operation="acquire",
                    entity_types=[],
                    regulator_types=[],
                    target_types=[],
                    granularity="aggregate",
                ),
                confidence=0.9,
                evidence=[
                    OutcomeEvidence(
                        dimension="artifact_type",
                        value="regulatory_network",
                        source="explicit",
                        text_span="regulatory network",
                        rationale="Only the artifact family is explicit.",
                    ),
                ],
                assumptions=[],
            )
        ]
    )

    assert result.status == "ambiguous"
    assert result.matched_actions == []


def test_generic_sample_network_keeps_all_lioness_families_tied():
    result = match_outcome_hypotheses(
        [
            advisory_hypothesis(
                outcome(
                    operation="infer",
                    artifact_type="unknown",
                    entity_types=[],
                    display_entities=[],
                    regulator_types=[],
                    target_types=[],
                    granularity="sample_specific",
                    unresolved_dimensions=["network type"],
                ),
                OutcomeEvidence(
                    dimension="granularity",
                    value="sample_specific",
                    source="explicit",
                    rationale="The request explicitly asks for a sample-specific result.",
                ),
            )
        ]
    )

    assert result.status == "ambiguous"
    assert set(result.hypothesis_actions) == {
        "run_lioness_panda",
        "run_lioness_puma",
        "run_lioness_coexpression",
        "run_bonobo",
    }


def test_measurement_artifact_conflicts_with_every_network_hypothesis():
    result = match_outcome_hypotheses(
        [
            advisory_hypothesis(
                outcome(
                    operation="acquire",
                    artifact_type="measurement_dataset",
                    regulator_types=[],
                    target_types=[],
                ),
                OutcomeEvidence(
                    dimension="artifact_type",
                    value="measurement_dataset",
                    source="explicit",
                    rationale="The request asks for measured miRNA values.",
                ),
            )
        ]
    )

    assert result.matched_actions == []
    assert result.hypothesis_actions == []
    assert result.status == "unsupported"


def test_registry_identifier_matches_supporting_action_without_intent_authority():
    not_applicable = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="unknown",
            artifact_type="unknown",
            entity_types=[],
            regulator_types=[],
            target_types=[],
            granularity="not_applicable",
            unresolved_dimensions=[],
        ),
        confidence=0.99,
        evidence=[],
        assumptions=[],
    )

    result = match_semantic_request(
        "Search the web with WEB-SEARCH for current PANDA references.",
        [not_applicable],
    )

    assert result.status == "exact"
    assert result.matched_actions == ["web_search"]
