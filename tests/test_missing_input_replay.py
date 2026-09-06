"""A replay suite for the failure that actually dominates the live record.

`cross-field` and `missing-required` reconstruct cross-field and schema errors.
Neither samples the class that is 112 of 131 recorded first attempts: a
schema-valid proposal that simply does not list a current input the harness's
own witnesses already located, with no other defect in 31 of those trials.

A repair-replay round is the cleanest control available -- same injected first
pass, same issue codes, only the review contract differs -- so it has to be able
to sample that class. These tests pin the reconstruction to exactly the issues
it declares, so a drifting fixture cannot quietly change what a round measures.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    validate_outcome_hypotheses,
)

from evaluate_routing import DEFAULT_SCENARIOS, load_scenarios  # noqa: E402
from routing_repair_replay import (  # noqa: E402
    MISSING_INPUT_ISSUES, REPLAY_SUITES, reconstructed_proposal,
)

CASES = {case.id: case for case in load_scenarios(DEFAULT_SCENARIOS)}


def parsed(case_id: str) -> SemanticInterpretation:
    return SemanticInterpretation.model_validate(
        reconstructed_proposal(case_id, "missing-input")
    )


def test_the_suite_is_selectable_by_name():
    assert REPLAY_SUITES["missing-input"] is MISSING_INPUT_ISSUES


@pytest.mark.parametrize("case_id", sorted(MISSING_INPUT_ISSUES))
def test_the_reconstruction_parses_so_the_review_has_something_to_repair(case_id):
    """A patch is merged onto the first pass, so the first pass must parse."""
    assert parsed(case_id).outcome_hypotheses


@pytest.mark.parametrize("case_id", sorted(MISSING_INPUT_ISSUES))
def test_the_reconstruction_raises_exactly_the_issues_it_declares(case_id):
    result = validate_outcome_hypotheses(CASES[case_id].prompt, parsed(case_id).outcome_hypotheses)

    assert not result.valid
    assert [issue.split(".", 1)[-1] for issue in result.issues] == MISSING_INPUT_ISSUES[case_id]


@pytest.mark.parametrize("case_id", sorted(MISSING_INPUT_ISSUES))
def test_the_omitted_input_is_one_the_witnesses_already_located(case_id):
    """The repair is one field: the fact is in the request and we already found it."""
    from netzoo_agent_core.interpretation.request_integrity import confirmed_current_inputs

    outcome = parsed(case_id).outcome_hypotheses[0].outcome

    assert outcome.input_artifacts == []
    assert "mutation_matrix" in confirmed_current_inputs(CASES[case_id].prompt)


def test_the_suite_carries_no_expected_answer_to_the_reviewer():
    """Q1 and Q2 differ from the corpus expectation only by the omitted input."""
    for case_id in ("original-q1", "original-q2"):
        outcome = parsed(case_id).outcome_hypotheses[0].outcome
        expected = CASES[case_id].expected

        assert outcome.artifact_type == expected.artifact_type
        assert outcome.granularity == expected.granularity
        assert outcome.input_artifacts == []
