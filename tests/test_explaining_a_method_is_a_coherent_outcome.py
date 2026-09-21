"""A conceptual question had no legal shape in the outcome contract.

Observed live on "Explain the difference between PANDA and PUMA. Do not run
anything.": the interpreter returned `request_mode=guidance`,
`operation=explain` grounded on an explicit span, `artifact_type=unknown` and
`granularity=not_applicable` — which is what both field descriptions ask for.
`inconsistent_not_applicable_outcome` rejected it twice and the turn ended in
`semantic_interpreter_failed`, selecting no workflow.

The only shape that passed was `operation=unknown` with no evidence at all, so
the contract's own rules could only be satisfied by discarding a correct,
explicitly grounded reading. The research log measured this issue at 28
occurrences and a 0% pass rate.

These tests pin the two halves: `explain` is coherent with a not-applicable
outcome, and the rule still fires on the contradictions it exists for.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
)
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    validate_outcome_hypotheses,
)

TASK = "Explain the difference between PANDA and PUMA. Do not run anything."
SPAN = "Explain the difference between PANDA and PUMA."
ISSUE = "hypothesis[0].inconsistent_not_applicable_outcome"


def _hypothesis(outcome: RequestedOutcome, evidence=()) -> OutcomeHypothesis:
    return OutcomeHypothesis(
        confidence=1.0, evidence=list(evidence), outcome=outcome
    )


def _explain_evidence() -> OutcomeEvidence:
    return OutcomeEvidence(
        dimension="operation",
        source="explicit",
        value="explain",
        text_span=SPAN,
        rationale="The user asks for an explanation of two methods.",
    )


def test_the_live_interpretation_of_a_concept_question_is_accepted():
    """The exact hypothesis the model returned, from the recorded trace."""
    validation = validate_outcome_hypotheses(
        TASK,
        [
            _hypothesis(
                RequestedOutcome(
                    operation="explain",
                    artifact_type="unknown",
                    granularity="not_applicable",
                ),
                [_explain_evidence()],
            )
        ],
    )

    assert validation.valid, list(validation.issues)


def test_an_unknown_operation_is_still_accepted():
    """The shape that already passed must keep passing."""
    validation = validate_outcome_hypotheses(
        TASK,
        [
            _hypothesis(
                RequestedOutcome(
                    operation="unknown",
                    artifact_type="unknown",
                    granularity="not_applicable",
                )
            )
        ],
    )

    assert validation.valid, list(validation.issues)


@pytest.mark.parametrize("operation", ["acquire", "prepare", "validate", "infer", "analyze"])
def test_an_operation_that_produces_something_still_contradicts_not_applicable(operation):
    """Claiming to infer, and that nothing applies, remains a contradiction."""
    validation = validate_outcome_hypotheses(
        TASK,
        [
            _hypothesis(
                RequestedOutcome(
                    operation=operation,
                    artifact_type="unknown",
                    granularity="not_applicable",
                )
            )
        ],
    )

    assert ISSUE in validation.issues


def test_explaining_does_not_license_claiming_scientific_content():
    """`explain` widens one field, not the rule.

    An outcome that says nothing applies while naming regulators is still
    inconsistent, whichever operation it carries.
    """
    validation = validate_outcome_hypotheses(
        "explain the mi-RNA regulator result",
        [
            _hypothesis(
                RequestedOutcome(
                    operation="explain",
                    artifact_type="unknown",
                    granularity="not_applicable",
                    entity_types=["mirna"],
                    regulator_types=["mirna"],
                    target_types=["unknown"],
                    unresolved_dimensions=["artifact_type"],
                ),
                [
                    OutcomeEvidence(
                        dimension="regulator_type",
                        source="explicit",
                        value="mirna",
                        text_span="mi-RNA regulator",
                        rationale="The regulator is explicit.",
                    )
                ],
            )
        ],
    )

    assert ISSUE in validation.issues
