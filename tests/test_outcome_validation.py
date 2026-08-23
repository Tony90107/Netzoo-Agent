from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.contracts import (  # noqa: E402
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
)
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    validate_outcome_hypotheses,
)
from netzoo_agent_core.llm import build_semantic_interpreter_prompt  # noqa: E402
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
            "run_panda",
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
            "run_lioness_coexpression",
        ),
    ],
)
def test_generic_evidence_validation_precedes_registry_matching(
    task: str,
    outcome: RequestedOutcome,
    items: list[OutcomeEvidence],
    expected_action: str,
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


def test_semantic_interpretation_schema_forbids_an_empty_result():
    with pytest.raises(ValidationError):
        SemanticInterpretation(
            semantic_goal="No outcome",
            outcome_hypotheses=[],
        )


def test_semantic_interpreter_prompt_has_no_workflow_selection_authority():
    prompt = build_semantic_interpreter_prompt()

    assert "Never select a workflow or action" in prompt
    assert "candidate_actions" not in prompt
    assert "run_puma" not in prompt
    assert "PUMA" not in prompt
    assert "text_span" in prompt
