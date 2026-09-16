from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
)
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    validate_outcome_hypotheses,
)

_TASK = "Run PANDA with data/expression.tsv for human, output to outputs/p.tsv"


def _hypothesis(*, input_artifacts, evidence):
    return OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer",
            input_artifacts=input_artifacts,
            artifact_type="regulatory_network",
            granularity="aggregate",
        ),
        confidence=1.0,
        evidence=evidence,
    )


def _grounded(dimension, value, span):
    return OutcomeEvidence(
        dimension=dimension, value=value, source="explicit",
        text_span=span, rationale="stated in the request",
    )


def _inferred(dimension, value):
    return OutcomeEvidence(
        dimension=dimension, value=value, source="inferred", rationale="implied",
    )


def _base_evidence():
    return [
        _grounded("input_artifact", "expression_matrix", "data/expression.tsv"),
        _grounded("operation", "infer", "Run PANDA"),
        _inferred("artifact_type", "regulatory_network"),
        _inferred("granularity", "aggregate"),
    ]


def test_an_outcome_gap_is_closed_from_its_own_grounded_evidence():
    """Writing the same fact twice is the contract's demand, not the user's."""
    hypothesis = _hypothesis(input_artifacts=[], evidence=_base_evidence())

    result = validate_outcome_hypotheses(_TASK, [hypothesis])

    assert result.valid, result.issues
    assert hypothesis.outcome.input_artifacts == ["expression_matrix"]


def test_a_real_disagreement_is_still_reported():
    """Only a gap is closed. A field holding something else is a conflict."""
    hypothesis = _hypothesis(
        input_artifacts=["mutation_matrix"], evidence=_base_evidence()
    )

    result = validate_outcome_hypotheses(_TASK, [hypothesis])

    assert not result.valid
    assert any("conflicting_evidence:input_artifact=expression_matrix" in issue
               for issue in result.issues)
    assert hypothesis.outcome.input_artifacts == ["mutation_matrix"]


def test_an_inferred_entry_cannot_complete_the_outcome():
    """A value with no quote is the model's own claim, not the user's."""
    evidence = [
        _inferred("input_artifact", "expression_matrix"),
        _grounded("operation", "infer", "Run PANDA"),
        _inferred("artifact_type", "regulatory_network"),
        _inferred("granularity", "aggregate"),
    ]
    hypothesis = _hypothesis(input_artifacts=[], evidence=evidence)

    validate_outcome_hypotheses(_TASK, [hypothesis])

    assert hypothesis.outcome.input_artifacts == []


def test_an_ungrounded_quote_cannot_complete_the_outcome():
    evidence = [
        _grounded("input_artifact", "expression_matrix", "data/not-in-the-request.tsv"),
        _grounded("operation", "infer", "Run PANDA"),
        _inferred("artifact_type", "regulatory_network"),
        _inferred("granularity", "aggregate"),
    ]
    hypothesis = _hypothesis(input_artifacts=[], evidence=evidence)

    validate_outcome_hypotheses(_TASK, [hypothesis])

    assert hypothesis.outcome.input_artifacts == []


def test_declining_to_commit_is_not_a_contradiction():
    """"unknown" is how this vocabulary says nothing, on either side."""
    evidence = _base_evidence() + [
        _grounded("input_artifact", "unknown", "data/expression.tsv"),
    ]
    hypothesis = _hypothesis(input_artifacts=[], evidence=evidence)

    result = validate_outcome_hypotheses(_TASK, [hypothesis])

    assert result.valid, result.issues


def test_an_unsupported_outcome_value_is_still_missing_evidence():
    """The reconciliation must not become a way to skip justifying a choice."""
    evidence = [
        _grounded("input_artifact", "expression_matrix", "data/expression.tsv"),
        _inferred("artifact_type", "regulatory_network"),
        _inferred("granularity", "aggregate"),
    ]
    hypothesis = _hypothesis(input_artifacts=[], evidence=evidence)

    result = validate_outcome_hypotheses(_TASK, [hypothesis])

    assert not result.valid
    assert any("missing_evidence:operation=infer" in issue for issue in result.issues)
