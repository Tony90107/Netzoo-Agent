"""Log 207: model-written text in another language never reaches the reply.

Under the claims contract the model wrote `assumptions` and `display_entities`
in Chinese for Chinese requests; the tie reply put them into a template checked
by `_ui_text` and crashed (39 of 563 recorded tie replies). Agent output is
English, so such text is left out, and entities fall back to their labels.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis, RequestedOutcome  # noqa: E402
from netzoo_agent_core.graph.response_context import validated_workflow_context  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification  # noqa: E402
from netzoo_agent_core.interpretation.verified_guidance import render_verified_guidance  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
ASSUMPTIONS = ["需要推斷轉錄因子與基因之間的關聯性。", "The whole cohort shares one network."]


def _decision(status, actions, **fields) -> TaskDecision:
    outcome = RequestedOutcome(operation="infer", artifact_type="regulatory_network", granularity="aggregate",
                               regulator_types=["tf"], target_types=["gene"],
                               display_entities=["轉錄因子", "基因"])
    return TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question",
        confidence=0.9, reason="guidance", requested_outcome=outcome,
        outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=0.9, assumptions=ASSUMPTIONS)],
        capability_match_status=status, **fields, **actions,
    )


def test_a_tie_reply_leaves_out_non_english_model_text_and_keeps_the_rest():
    decision = _decision("ambiguous", {"hypothesis_actions": ["run_panda", "run_otter", "run_giraffe"]},
                         clarification_question="Is memory or runtime a concern?")

    answer = render_outcome_clarification(decision, POLICY)

    assert "需要推斷" not in answer and "轉錄因子" not in answer
    assert "- The whole cohort shares one network." in answer
    assert "Is memory or runtime a concern?" in answer


def test_a_one_candidate_reply_falls_back_to_entity_labels():
    decision = _decision("ambiguous", {"hypothesis_actions": ["run_panda"]},
                         clarification_question="Is this the network you want?")

    answer = render_outcome_clarification(decision, POLICY)

    assert "It sounds like you want aggregate regulatory networks." in answer


def test_verified_guidance_leaves_out_non_english_assumptions():
    decision = _decision("exact", {"matched_actions": ["run_panda"], "recommended_actions": ["run_panda"]})

    answer = render_verified_guidance(decision, validated_workflow_context(decision, POLICY))

    assert "需要推斷" not in answer
    assert "- The whole cohort shares one network." in answer
