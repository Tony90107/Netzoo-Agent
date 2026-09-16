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
    # artifact_type, not operation: infer is entailed for a regulatory network,
    # so it is no longer the dimension that proves the point.
    evidence = [
        _grounded("input_artifact", "expression_matrix", "data/expression.tsv"),
        _inferred("granularity", "aggregate"),
    ]
    hypothesis = _hypothesis(input_artifacts=[], evidence=evidence)

    result = validate_outcome_hypotheses(_TASK, [hypothesis])

    assert not result.valid
    assert any(
        "missing_evidence:artifact_type=regulatory_network" in issue
        for issue in result.issues
    )


def test_the_operation_that_builds_the_artifact_needs_no_separate_evidence():
    """Naming infer for a regulatory network repeats the artifact choice."""
    evidence = [
        _grounded("input_artifact", "expression_matrix", "data/expression.tsv"),
        _inferred("artifact_type", "regulatory_network"),
        _inferred("granularity", "aggregate"),
    ]
    hypothesis = _hypothesis(input_artifacts=[], evidence=evidence)

    result = validate_outcome_hypotheses(_TASK, [hypothesis])

    assert result.valid, result.issues


def test_asking_about_an_artifact_is_still_a_choice_that_needs_evidence():
    """"Which tools produce a regulatory network?" is explain, not infer."""
    for operation in ("explain", "analyze", "acquire"):
        hypothesis = OutcomeHypothesis(
            outcome=RequestedOutcome(
                operation=operation,
                input_artifacts=["expression_matrix"],
                artifact_type="regulatory_network",
                granularity="aggregate",
            ),
            confidence=1.0,
            evidence=[
                _grounded("input_artifact", "expression_matrix", "data/expression.tsv"),
                _inferred("granularity", "aggregate"),
                _inferred("artifact_type", "regulatory_network"),
            ],
        )

        result = validate_outcome_hypotheses(_TASK, [hypothesis])

        assert any(
            f"missing_evidence:operation={operation}" in issue
            for issue in result.issues
        ), operation


def test_an_artifact_without_a_declared_producer_still_needs_evidence():
    from netzoo_agent_core.contracts.artifact_semantics import ARTIFACT_SEMANTICS

    undeclared = next(
        artifact
        for artifact, rule in ARTIFACT_SEMANTICS.items()
        if rule.produced_by is None and artifact != "unknown"
    )
    hypothesis = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer", artifact_type=undeclared, granularity="aggregate"
        ),
        confidence=1.0,
        evidence=[_inferred("artifact_type", undeclared)],
    )

    result = validate_outcome_hypotheses(_TASK, [hypothesis])

    assert any("missing_evidence:operation=infer" in issue for issue in result.issues)


def test_produced_by_does_not_constrain_what_a_request_may_ask():
    """It answers what builds the artifact, never what may be asked of it."""
    from netzoo_agent_core.contracts.artifact_semantics import (
        ARTIFACT_SEMANTICS,
        artifact_field_constraints,
    )

    assert ARTIFACT_SEMANTICS["regulatory_network"].operations is None
    assert "operation" not in artifact_field_constraints("regulatory_network")
