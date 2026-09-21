"""The class of request that asks what something means.

A concept question names no data, wants no result, and must not be turned
into a tool recommendation. The corpus had none of them, so the class went
unmeasured -- and the validator governing it required the interpreter to
report that it had understood nothing, which no correct reading of
"explain X" would say. These tests keep the class present and, more
importantly, keep the answer the corpus writes down the same answer the
capability matcher actually produces for that shape.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.contracts.outcomes import RequestedOutcome  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import (  # noqa: E402
    match_requested_outcome,
)

CORPUS = json.loads(
    (Path(__file__).parents[1] / "tests" / "routing_scenarios.json").read_text(
        encoding="utf-8"
    )
)
CONCEPT = [case for case in CORPUS if case["id"].startswith("concept-")]
CONCEPT_IDS = [case["id"] for case in CONCEPT]


def test_the_class_that_was_missing_is_now_in_the_corpus():
    assert len(CONCEPT) >= 6, "a single example cannot show a class is handled"
    assert {case["language"] for case in CONCEPT} >= {"en", "zh", "mixed"}


@pytest.mark.parametrize("case", CONCEPT, ids=CONCEPT_IDS)
class TestEveryConceptCase:
    def test_expects_no_tool_and_no_result(self, case):
        expected = case["expected"]
        assert expected["status"] == "not_applicable"
        assert expected["actions"] == []
        assert expected["artifact_type"] == "unknown"
        assert expected["granularity"] == "not_applicable"
        assert expected["input_artifacts"] == []
        assert expected["entity_types"] == []

    def test_names_the_tools_it_must_not_be_turned_into(self, case):
        """Without this the case passes by accident on an empty match."""
        assert case["expected"]["forbidden_actions"]

    def test_states_no_data_the_user_already_holds(self, case):
        """Anything that reads as held input makes it a workflow request."""
        from netzoo_agent_core.interpretation.request_integrity import (
            confirmed_current_inputs,
        )

        assert not confirmed_current_inputs(case["prompt"]), case["id"]

    def test_claims_no_answer_the_evaluator_cannot_score(self, case):
        """A not_applicable decision is out of scope for answer scoring.

        Writing `answer_required` here would make the case fail on every run
        for a reason that has nothing to do with routing.
        """
        assert not case["expected"].get("answer_required")
        assert not case["expected"].get("answer_forbidden")

    @pytest.mark.parametrize("operation", ["explain", "unknown"])
    def test_the_stated_answer_is_the_one_the_matcher_gives(self, case, operation):
        """The corpus must not assert an outcome the contract disagrees with."""
        outcome = RequestedOutcome(
            operation=operation,
            artifact_type=case["expected"]["artifact_type"],
            granularity=case["expected"]["granularity"],
            input_artifacts=case["expected"]["input_artifacts"],
            entity_types=case["expected"]["entity_types"],
        )

        match = match_requested_outcome(outcome)

        assert match.status == case["expected"]["status"]
        assert list(match.matched_actions) == case["expected"]["actions"]
