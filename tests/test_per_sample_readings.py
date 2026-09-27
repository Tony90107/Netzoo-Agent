"""Log 219: a LIONESS or GIRAFFE reply names the other per-sample reading and the difference.

TEST_PROMPTS Case 4 ("each person's per-TF regulatory strength over its
targets ... survival"): per-sample out-degree from LIONESS-PANDA measures
wiring, GIRAFFE's TFA measures activity, and either is acceptable; what loses
marks is giving one path without saying how the two readings differ. Case 4
and its variants were answered with one exact workflow in 10 of 12 trials
(Log 201), and those replies named only that workflow.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis, RequestedOutcome  # noqa: E402
from netzoo_agent_core.graph.response_context import validated_workflow_context  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import render_workflow_composition_guidance  # noqa: E402
from netzoo_agent_core.interpretation.verified_guidance import render_verified_guidance  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()


def _lioness(final: str, aggregate: str, regulators: list[str]) -> str:
    outcome = RequestedOutcome(
        operation="infer", artifact_type="regulatory_network", granularity="sample_specific",
        regulator_types=regulators, target_types=["gene"], entity_types=[*regulators, "gene"],
    )
    decision = TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question",
        confidence=1.0, reason="guidance", requested_outcome=outcome,
        outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=0.9)],
        capability_match_status="exact", matched_actions=[final], recommended_actions=[aggregate, final],
    )
    return render_workflow_composition_guidance(decision, POLICY)


@pytest.mark.parametrize("final, aggregate, regulators", [
    ("run_lioness_panda", "run_panda", ["tf"]),
    ("run_lioness_puma", "run_puma", ["tf", "mirna"]),
])
def test_a_lioness_reply_names_tf_activity_as_the_other_reading(final, aggregate, regulators):
    answer = _lioness(final, aggregate, regulators)

    assert "Out-degree measures how strongly a TF is wired to its targets" in answer
    assert "GIRAFFE's TF-by-sample activity matrix is the other reading" in answer
    assert answer.index("outdegree") < answer.index("GIRAFFE") < answer.index("clinical table")


def test_a_giraffe_reply_names_lioness_wiring_as_the_other_reading():
    decision = TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question",
        confidence=1.0, reason="guidance", capability_match_status="exact",
        matched_actions=["run_giraffe"], recommended_actions=["run_giraffe"],
    )

    answer = render_verified_guidance(decision, validated_workflow_context(decision, POLICY))

    assert "TF activity is how active a TF is in each sample" in answer
    assert "out-degree in LIONESS-PANDA's per-sample networks is the other reading" in answer
    assert answer.index("activity matrix (TFA)") < answer.index("LIONESS-PANDA")
