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
    task = "Use a somatic mutation matrix to cluster patients."
    missing = validate_outcome_hypotheses(task, [hypothesis])
    assert "hypothesis[0].missing_evidence:input_artifact=mutation_matrix" in missing.issues

    supported = hypothesis.model_copy(update={"evidence": [
        *hypothesis.evidence,
        evidence("input_artifact", "mutation_matrix", text_span="somatic mutation matrix"),
    ]})
    assert validate_outcome_hypotheses(task, [supported]).valid
    conflicting = supported.model_copy(update={"evidence": [
        *hypothesis.evidence,
        evidence("input_artifact", "expression_matrix", source="inferred"),
    ]})
    assert not validate_outcome_hypotheses(task, [conflicting]).valid


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
            artifact_type="expression_matrix",
            entity_types=["gene"],
            granularity="aggregate",
        ),
        confidence=0.9,
        evidence=[
            evidence("operation", "explain", source="inferred"),
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
            granularity="not_applicable",
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
