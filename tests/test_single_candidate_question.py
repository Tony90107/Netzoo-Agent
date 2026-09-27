"""Log 194: a one-candidate tie with no routing question still gets a deterministic reply."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
)
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()


def _tie(actions, question=None, **outcome) -> TaskDecision:
    fields = dict(operation="infer", artifact_type="community_assignment", granularity="aggregate")
    fields.update(outcome)
    requested = RequestedOutcome(**fields)
    evidence = [OutcomeEvidence(
        dimension="artifact_type", value=requested.artifact_type, source="inferred", rationale="t",
    )]
    return TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question",
        confidence=0.9, reason="guidance", requested_outcome=requested,
        outcome_hypotheses=[OutcomeHypothesis(outcome=requested, confidence=0.9, evidence=evidence)],
        hypothesis_actions=list(actions), capability_match_status="ambiguous",
        clarification_question=question,
    )


def test_case_9_shape_says_what_differs_and_asks_to_confirm():
    answer = render_outcome_clarification(_tie(["run_condor"]), POLICY)

    assert answer is not None
    assert "**Community assignments — CONDOR**" in answer
    assert (
        "The only registered workflow compatible with this request is **CONDOR**, but it analyzes "
        "an existing regulatory network, while your request reads as asking to infer a new result."
    ) in answer
    assert "Is CONDOR the analysis you want?" in answer
    assert answer.endswith("No files were inspected and no analysis ran.")


def test_an_unsettled_granularity_is_named():
    decision = _tie(["run_lioness_panda"], operation="infer", artifact_type="regulatory_network",
                    granularity="unknown", regulator_types=["tf"], target_types=["gene"])

    answer = render_outcome_clarification(decision, POLICY)

    assert "does not settle whether one cohort-wide result or one result per sample is wanted" in answer


def test_a_routing_question_is_kept_as_it_was():
    answer = render_outcome_clarification(_tie(["run_condor"], question="Which network should I use?"), POLICY)

    assert "Which network should I use?" in answer
    assert "The only registered workflow compatible" not in answer


def test_a_tie_of_several_without_a_question_is_still_left_alone():
    assert render_outcome_clarification(_tie(["run_panda", "run_otter"]), POLICY) is None
