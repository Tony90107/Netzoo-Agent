from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.contracts import (  # noqa: E402
    IntentDecision,
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
)
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    SemanticInterpretation,
    SemanticReview,
)
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    evidence_census,
    validate_outcome_hypotheses,
)
from netzoo_agent_core.llm import build_semantic_interpreter_prompt  # noqa: E402
from netzoo_agent_core.llm import build_intent_router_prompt  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import (  # noqa: E402
    match_outcome_hypotheses,
)


def evidence(
    dimension: str,
    value: str,
    *,
    source: str = "explicit",
    text_span: str | None = None,
) -> OutcomeEvidence:
    return OutcomeEvidence(
        dimension=dimension,
        value=value,
        source=source,
        text_span=text_span,
        rationale=f"Evidence for {dimension}.",
    )


@pytest.mark.parametrize(
    ("task", "outcome", "items", "expected_action"),
    [
        (
            "What tools infer a sample-specific miRNA regulatory network?",
            RequestedOutcome(
                operation="infer",
                artifact_type="regulatory_network",
                entity_types=["mirna"],
                display_entities=["miRNA"],
                regulator_types=["mirna"],
                target_types=[],
                granularity="sample_specific",
                unresolved_dimensions=[],
            ),
            [
                evidence("operation", "infer", text_span="infer"),
                evidence(
                    "artifact_type",
                    "regulatory_network",
                    text_span="regulatory network",
                ),
                evidence("regulator_type", "mirna", text_span="miRNA"),
                evidence(
                    "granularity",
                    "sample_specific",
                    text_span="sample-specific",
                ),
            ],
            "run_lioness_puma",
        ),
        (
            "Infer an aggregate TF regulatory network.",
            RequestedOutcome(
                operation="infer",
                artifact_type="regulatory_network",
                entity_types=["tf"],
                display_entities=["TF"],
                regulator_types=["tf"],
                target_types=[],
                granularity="aggregate",
                unresolved_dimensions=[],
            ),
            [
                evidence("operation", "infer", text_span="Infer"),
                evidence(
                    "artifact_type",
                    "regulatory_network",
                    text_span="regulatory network",
                ),
                evidence("regulator_type", "tf", text_span="TF"),
                evidence("granularity", "aggregate", text_span="aggregate"),
            ],
            None,
        ),
        (
            "Which method builds a sample-specific gene coexpression network?",
            RequestedOutcome(
                operation="infer",
                artifact_type="coexpression_network",
                entity_types=["gene"],
                display_entities=["gene"],
                regulator_types=[],
                target_types=[],
                granularity="sample_specific",
                unresolved_dimensions=[],
            ),
            [
                evidence(
                    "operation",
                    "infer",
                    source="inferred",
                ),
                evidence(
                    "artifact_type",
                    "coexpression_network",
                    text_span="coexpression network",
                ),
                evidence("entity_type", "gene", text_span="gene"),
                evidence(
                    "granularity",
                    "sample_specific",
                    text_span="sample-specific",
                ),
            ],
        None,
        ),
    ],
)
def test_generic_evidence_validation_precedes_registry_matching(
    task: str,
    outcome: RequestedOutcome,
    items: list[OutcomeEvidence],
    expected_action: str | None,
):
    hypotheses = [
        OutcomeHypothesis(
            outcome=outcome,
            confidence=0.95,
            evidence=items,
            assumptions=[],
        )
    ]

    validation = validate_outcome_hypotheses(task, hypotheses)
    match = match_outcome_hypotheses(hypotheses)

    assert validation.valid is True
    assert validation.issues == ()
    if expected_action is None:
        assert match.status == "ambiguous"
        assert match.matched_actions == []
    else:
        assert match.status == "exact"
        assert match.matched_actions == [expected_action]


def test_evidence_validator_rejects_missing_dimension_evidence():
    task = "Infer a sample-specific miRNA regulatory network."
    hypothesis = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=["mirna"],
            regulator_types=["mirna"],
            granularity="sample_specific",
        ),
        confidence=0.9,
        evidence=[
            evidence("operation", "infer", text_span="Infer"),
            evidence("regulator_type", "mirna", text_span="miRNA"),
            evidence(
                "granularity",
                "sample_specific",
                text_span="sample-specific",
            ),
        ],
    )

    result = validate_outcome_hypotheses(task, [hypothesis])

    assert result.valid is False
    assert "hypothesis[0].missing_evidence:artifact_type=regulatory_network" in (
        result.issues
    )


def test_current_input_artifact_requires_its_own_consistent_evidence():
    hypothesis = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="analyze", input_artifacts=["mutation_matrix"],
            artifact_type="sample_cluster_assignment", entity_types=["sample"],
            granularity="aggregate",
        ),
        confidence=0.9,
        evidence=[evidence(dimension, value, source="inferred") for dimension, value in (
            ("operation", "analyze"), ("artifact_type", "sample_cluster_assignment"),
            ("entity_type", "sample"), ("granularity", "aggregate"),
        )],
    )
    # The request no longer names the input: where the request witnesses locate
    # it themselves, that grounding stands in for the model's evidence entry,
    # and tests/test_entailed_evidence.py pins both sides of that boundary.
    task = "Cluster my patients into subtypes."
    missing = validate_outcome_hypotheses(task, [hypothesis])
    assert "hypothesis[0].missing_evidence:input_artifact=mutation_matrix" in missing.issues

    supported = hypothesis.model_copy(update={"evidence": [
        *hypothesis.evidence,
        evidence("input_artifact", "mutation_matrix", source="inferred"),
    ]})
    assert validate_outcome_hypotheses(task, [supported]).valid
    conflicting = supported.model_copy(update={"evidence": [
        *hypothesis.evidence,
        evidence("input_artifact", "expression_matrix", source="inferred"),
    ]})
    assert not validate_outcome_hypotheses(task, [conflicting]).valid


def test_explicit_input_evidence_must_use_the_canonical_artifact_in_its_quote():
    task = "I have expression, TF motif prior, and PPI inputs."
    hypothesis = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer",
            input_artifacts=[
                "expression_matrix",
                "tf_activity_matrix",
                "regulatory_network",
            ],
            artifact_type="regulatory_network",
            entity_types=["tf", "gene"],
            regulator_types=["tf"],
            target_types=["gene"],
            granularity="aggregate",
        ),
        confidence=0.9,
        evidence=[
            evidence("operation", "infer", source="inferred"),
            evidence("artifact_type", "regulatory_network", source="inferred"),
            evidence("entity_type", "tf", source="inferred"),
            evidence("entity_type", "gene", source="inferred"),
            evidence("regulator_type", "tf", source="inferred"),
            evidence("target_type", "gene", source="inferred"),
            evidence("granularity", "aggregate", source="inferred"),
            evidence(
                "input_artifact",
                "expression_matrix",
                text_span="expression, TF motif prior, and PPI inputs",
            ),
            evidence(
                "input_artifact",
                "tf_activity_matrix",
                text_span="expression, TF motif prior, and PPI inputs",
            ),
            evidence(
                "input_artifact",
                "regulatory_network",
                text_span="expression, TF motif prior, and PPI inputs",
            ),
        ],
    )

    result = validate_outcome_hypotheses(task, [hypothesis])

    assert result.valid is False
    assert (
        "hypothesis[0].conflicting_evidence:input_artifact=tf_activity_matrix"
        in result.issues
    )
    assert (
        "hypothesis[0].conflicting_evidence:input_artifact=regulatory_network"
        in result.issues
    )


def test_evidence_validator_rejects_an_ungrounded_explicit_span():
    task = "Infer a sample-specific miRNA regulatory network."
    hypothesis = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=["mirna"],
            regulator_types=["mirna"],
            granularity="sample_specific",
        ),
        confidence=0.9,
        evidence=[
            evidence("operation", "infer", text_span="Infer"),
            evidence(
                "artifact_type",
                "regulatory_network",
                text_span="regulatory network",
            ),
            evidence("regulator_type", "mirna", text_span="microRNA regulators"),
            evidence(
                "granularity",
                "sample_specific",
                text_span="sample-specific",
            ),
        ],
    )

    result = validate_outcome_hypotheses(task, [hypothesis])

    assert result.valid is False
    assert "hypothesis[0].ungrounded_evidence:regulator_type=mirna" in result.issues


def test_evidence_validator_marks_translation_mismatch_as_recoverable():
    task = "我有一份基因表現量矩陣，想了解它的用途。"
    hypothesis = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="explain",
            input_artifacts=["expression_matrix"],
            artifact_type="expression_matrix",
            entity_types=["gene"],
            granularity="aggregate",
        ),
        confidence=0.9,
        evidence=[
            evidence("operation", "explain", source="inferred"),
            evidence("input_artifact", "expression_matrix", text_span="基因表現量矩陣"),
            evidence("artifact_type", "expression_matrix", source="inferred"),
            evidence("entity_type", "gene", text_span="gene"),
            evidence("granularity", "aggregate", source="inferred"),
        ],
    )

    result = validate_outcome_hypotheses(task, [hypothesis])

    assert result.valid is False
    assert result.recoverable is True
    assert "hypothesis[0].ungrounded_evidence:entity_type=gene" in result.issues


@pytest.mark.parametrize(
    ("task", "span", "valid"),
    [
        ("分析基\n因表現量", "基因", True),
        ("Analyze ＧＥＮＥ expression", "gene", True),
        ("Analyze genetic variation", "gene", False),
        ("分析基因表現量", "gene", False),
    ],
)
def test_evidence_grounding_normalizes_unicode_but_not_translation_or_substrings(
    task, span, valid,
):
    hypothesis = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="explain", artifact_type="expression_matrix",
            entity_types=["gene"], granularity="aggregate",
        ),
        confidence=0.9,
        evidence=[
            evidence("operation", "explain", source="inferred"),
            evidence("artifact_type", "expression_matrix", source="inferred"),
            evidence("granularity", "aggregate", source="inferred"),
            evidence("entity_type", "gene", text_span=span),
        ],
    )

    result = validate_outcome_hypotheses(task, [hypothesis])

    assert result.valid is valid


def test_registry_selection_signal_has_a_generic_evidence_boundary():
    task = "Different hospitals and sequencing batches affect the regulatory modules."
    hypothesis = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="analyze",
            artifact_type="community_assignment",
            entity_types=["gene"],
            regulator_types=[],
            target_types=[],
            selection_tags=["hospital_effect_assessment"],
            # 2026-09-06: was not_applicable, which community_assignment no longer
            # permits. This test is about the selection_tag evidence dimension, so
            # the granularity is rewritten to the artifact's single legal value;
            # being ontology-entailed it needs no evidence of its own.
            granularity="aggregate",
        ),
        confidence=0.9,
        evidence=[
            evidence("operation", "analyze", source="inferred"),
            evidence(
                "artifact_type",
                "community_assignment",
                text_span="regulatory modules",
            ),
            evidence("entity_type", "gene", source="inferred"),
            evidence(
                "selection_tag",
                "hospital_effect_assessment",
                source="inferred",
            ),
        ],
    )

    result = validate_outcome_hypotheses(task, [hypothesis])

    assert result.valid is True
    assert result.issues == ()
    assert hypothesis.evidence[-1].dimension == "selection_tag"

    provider_alias = OutcomeHypothesis.model_validate(
        {
            "outcome": hypothesis.outcome.model_dump(),
            "confidence": 0.9,
            "evidence": [
                {
                    **hypothesis.evidence[-1].model_dump(),
                    "dimension": "hospital_effect_assessment",
                }
            ],
        }
    )
    assert provider_alias.evidence[0].dimension == "selection_tag"
    assert provider_alias.evidence[0].value == "hospital_effect_assessment"


def test_semantic_interpretation_schema_forbids_an_empty_result():
    with pytest.raises(ValidationError):
        SemanticInterpretation(
            semantic_goal="No outcome",
            outcome_hypotheses=[],
        )


def test_review_normalizes_misplaced_hypothesis_metadata_without_losing_evidence():
    payload = {
        "request_mode": "guidance",
        "semantic_goal": "Explain cohort clustering",
        "outcome_hypothesis": {
            "operation": "analyze",
            "artifact_type": "sample_cluster_assignment",
            "entity_types": ["sample"],
            "granularity": "aggregate",
        },
        "confidence": 0.9,
        "evidence": [evidence("entity_type", "sample", text_span="patients").model_dump()],
        "assumptions": [],
    }

    review = SemanticReview.model_validate(payload)

    assert review.outcome_hypothesis.confidence == 0.9
    assert review.outcome_hypothesis.outcome.artifact_type == "sample_cluster_assignment"
    assert review.outcome_hypothesis.evidence[0].text_span == "patients"
    assert "confidence" in payload  # Do not mutate provider data.

    conflicting = {**payload, "outcome_hypothesis": {
        **payload["outcome_hypothesis"], "confidence": 0.2,
    }}
    with pytest.raises(ValidationError):
        SemanticReview.model_validate(conflicting)
    with pytest.raises(ValidationError):
        SemanticReview.model_validate({**payload, "action": "run_sambar"})


def test_non_scientific_request_has_a_valid_not_applicable_outcome():
    hypothesis = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="unknown",
            artifact_type="unknown",
            entity_types=[],
            regulator_types=[],
            target_types=[],
            granularity="not_applicable",
            unresolved_dimensions=[],
        ),
        confidence=0.95,
        evidence=[],
        assumptions=[],
    )

    validation = validate_outcome_hypotheses(
        "Remember that you may reuse my last inputs.",
        [hypothesis],
    )
    match = match_outcome_hypotheses([hypothesis])

    assert validation.valid is True
    assert match.status == "not_applicable"
    assert match.matched_actions == []


def test_scientific_outcome_cannot_mix_not_applicable_with_typed_dimensions():
    task = (
        "if i want to get sample specific mi-RNA regulator network,"
        "what tools do i need?"
    )
    hypothesis = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="unknown",
            artifact_type="unknown",
            entity_types=["mirna"],
            regulator_types=["mirna"],
            target_types=["unknown"],
            granularity="not_applicable",
            unresolved_dimensions=["artifact_type", "operation"],
        ),
        confidence=0.8,
        evidence=[
            evidence(
                "granularity",
                "not_applicable",
                text_span="sample specific",
            ),
            evidence(
                "regulator_type",
                "mirna",
                text_span="mi-RNA regulator",
            ),
        ],
    )

    validation = validate_outcome_hypotheses(task, [hypothesis])

    assert validation.valid is False
    assert "hypothesis[0].inconsistent_not_applicable_outcome" in validation.issues


def test_semantic_interpreter_prompt_has_no_workflow_selection_authority():
    prompt = build_semantic_interpreter_prompt()

    assert "Never select a workflow or action" in prompt
    assert "candidate_actions" not in prompt
    assert "run_puma" not in prompt
    assert "PUMA" not in prompt
    assert "text_span" in prompt
    assert "estimating each patient's network" in prompt
    assert "Do not select a workflow from a fixed keyword-to-tool table" in prompt
    assert "request_mode" in prompt
    assert "complete request" in prompt
    assert "keyword or a fixed phrase" in prompt
    assert "not in scientific evidence" in prompt
    assert "generic dimension selection_tag" in prompt


def test_intent_router_contract_can_only_choose_answer_or_execute():
    schema = IntentDecision.model_json_schema()

    assert set(schema["properties"]) == {"mode", "confidence", "reason"}
    assert schema["properties"]["mode"]["enum"] == ["answer", "execute"]
    assert "action" not in schema["properties"]
    assert "outcome_hypotheses" not in schema["properties"]
    assert "clarification_question" not in schema["properties"]


def test_intent_router_prompt_has_no_semantic_or_workflow_authority():
    prompt = build_intent_router_prompt()

    assert "Choose only whether" in prompt
    assert "Never select or name a workflow" in prompt
    assert "outcome_hypotheses" not in prompt
    assert "candidate_actions" not in prompt
    assert "run_puma" not in prompt


REVERSE_HISTORY_TASK = (
    "Previously I used SAMBAR for somatic mutations. That analysis is finished. "
    "Now I have a gene expression matrix, TF motif priors and PPI data. Which "
    "workflow can infer a separate TF-to-gene regulatory network for each "
    "patient? Advice only."
)


def _reverse_history_hypothesis(items: list[OutcomeEvidence]) -> OutcomeHypothesis:
    return OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer",
            input_artifacts=["expression_matrix"],
            artifact_type="regulatory_network",
            regulator_types=["tf"],
            target_types=["gene"],
            granularity="sample_specific",
        ),
        confidence=0.9,
        evidence=items,
    )


def test_ungrounded_shapes_separate_an_absent_quote_from_an_unmatched_one():
    """Validate the instrument against data whose shape is known by construction.

    `ungrounded_evidence` is the largest issue family in the live record, and
    the two shapes it conflates call for opposite responses. Nothing recorded
    before this reported which one occurred, so the classifier is pinned here
    against entries whose shape the fixture fixes.
    """
    hypothesis = _reverse_history_hypothesis([
        # A quote with characters but no words. Since the contract began
        # requiring `explicit` entries to carry a quote, this is the only way
        # left to reach `absent` -- the common shape it used to describe, an
        # entry claiming an explicit source and supplying nothing, no longer
        # parses. The classifier is kept because a count pinned at zero is what
        # shows the contract still holding.
        evidence("operation", "infer", text_span="---"),
        # Supplies a quote the request does not contain.
        evidence("granularity", "sample_specific", text_span="sample-specific"),
        # Quotes the request's own wording.
        evidence("artifact_type", "regulatory_network", text_span="regulatory network"),
        evidence("input_artifact", "expression_matrix", text_span="gene expression matrix"),
        # Inference is never asked for a quote, so it never has a shape.
        evidence("regulator_type", "tf", source="inferred"),
        evidence("target_type", "gene", source="inferred"),
    ])

    result = validate_outcome_hypotheses(REVERSE_HISTORY_TASK, [hypothesis])

    assert [
        (item["dimension"], item["span"]) for item in result.evidence_shapes
    ] == [("operation", "absent"), ("granularity", "unmatched")]
    assert all(item["hypothesis"] == 0 for item in result.evidence_shapes)
    # The strings the next attempt is shown stay exactly as they were.
    assert {issue for issue in result.issues if "ungrounded_evidence" in issue} == {
        "hypothesis[0].ungrounded_evidence:operation=infer",
        "hypothesis[0].ungrounded_evidence:granularity=sample_specific",
    }


def test_ungrounded_shapes_are_empty_when_every_explicit_quote_is_grounded():
    hypothesis = _reverse_history_hypothesis([
        evidence("operation", "infer", text_span="infer"),
        evidence("input_artifact", "expression_matrix", text_span="gene expression matrix"),
        evidence("artifact_type", "regulatory_network", text_span="regulatory network"),
        evidence("granularity", "sample_specific", text_span="for each patient"),
        evidence("regulator_type", "tf", source="inferred"),
        evidence("target_type", "gene", source="inferred"),
    ])

    result = validate_outcome_hypotheses(REVERSE_HISTORY_TASK, [hypothesis])

    assert result.evidence_shapes == ()
    assert not [issue for issue in result.issues if "ungrounded_evidence" in issue]


def test_evidence_census_counts_sourcing_before_any_grounding_check():
    """The base rate the rejection record cannot supply, pinned by construction.

    A quote the request does not contain still counts as a quote here: this
    census answers whether the entry claimed a source it supplied, not whether
    the claim held up.

    `explicit_without_span` is 0 by construction now, and cannot be otherwise:
    the census reads the same emptiness the contract rejects. It is kept, and
    pinned, because this census is what measured whether the contract could be
    tightened at all (1057/1138 hypotheses already complied), and a counter that
    stays at zero is the evidence that it took.
    """
    hypothesis = _reverse_history_hypothesis([
        evidence("operation", "infer", text_span="infer"),
        evidence("artifact_type", "regulatory_network", text_span="absent from the request"),
        evidence("granularity", "sample_specific", text_span="one network per patient"),
        evidence("input_artifact", "expression_matrix", source="inferred"),
    ])
    empty = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="unknown", artifact_type="unknown", granularity="not_applicable",
        ),
        confidence=0.1,
    )

    census = evidence_census([hypothesis, empty])

    assert census == (
        {"hypothesis": 0, "explicit_with_span": 3, "explicit_without_span": 0, "inferred": 1},
        {"hypothesis": 1, "explicit_with_span": 0, "explicit_without_span": 0, "inferred": 0},
    )


def test_a_blank_span_no_longer_reaches_the_census_because_the_contract_rejects_it():
    """Where "explicit with no quote" is now stopped.

    The census used to count this shape; it counted 281 of them across the live
    record, and 79% of the entries in that family cost the whole interpretation.
    The rule was in the prompt all along and in no contract, so the schema kept
    inviting it. It is refused at parse time now, which is why the counter above
    can only be zero.
    """
    with pytest.raises(ValidationError):
        evidence("operation", "infer", text_span="   ")
    with pytest.raises(ValidationError):
        evidence("operation", "infer")

    # Inference is never asked for a quote, and is untouched.
    assert evidence("operation", "infer", source="inferred").text_span is None
