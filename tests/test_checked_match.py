"""Log 405: when routing made no claim and the confirmed check credited one workflow for every result,
that workflow is the match, so the understanding lines, the body and the card say the same thing.

heldout12 b12 KP2 (6 of 6 sessions): "available from DRAGON" above "Fallback recommendation: BONOBO";
BP1: "available from CONDOR" above "Semantic routing output failed validation, so no workflow was
selected". Replayed from the stored decisions; nothing calls a model.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_routing import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.cli.follow_up import build_next_turn_prompt  # noqa: E402
from netzoo_agent_core.contracts import HumanMessage, TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement  # noqa: E402
from netzoo_agent_core.graph.response import respond  # noqa: E402
from netzoo_agent_core.interpretation.checked_match import CHECK_MATCH_BASIS, checked_match  # noqa: E402
from netzoo_agent_core.reply_cards import build_reply_card  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
RECORDED = json.loads((ROOT / "tests" / "log405_decisions.json").read_text())["decisions"]


def _replay(task: str, decision: TaskDecision):
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task, decision=decision.model_dump(), status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None}
    out = respond(SimpleNamespace(project_policy=POLICY), state)
    result = {**state, "messages": [HumanMessage(content=task), out["messages"][-1]], "reply_kind": out["reply_kind"]}
    return str(out["messages"][-1].content), build_reply_card(result, build_next_turn_prompt(result), POLICY, task=task)


@pytest.mark.parametrize("item,workflow,routing_said", [
    ("KP2", "DRAGON", "BONOBO"),
    ("BP1", "CONDOR", "no workflow was selected"),
])
def test_the_checks_single_workflow_is_the_match_when_routing_made_no_claim(item, workflow, routing_said):
    recorded = RECORDED[item]
    stored = TaskDecision.model_validate(recorded["decision"])
    before, _ = _replay(recorded["task"], stored)
    assert routing_said in before  # the recorded contradiction

    decision = checked_match(stored, POLICY.workflows)
    assert decision.capability_match_status == "exact" and decision.match_basis == CHECK_MATCH_BASIS
    reply, card = _replay(recorded["task"], decision)

    assert routing_said not in reply and f"Selected path: **{workflow}**" in reply
    assert workflow in card.headline and "not a verified match" not in card.headline
    assert any(step.resolution == "plan_workflow" and workflow in step.label for step in card.next_steps)


def _check(*results, **extra) -> CapabilityCheck:
    return CapabilityCheck(requirements=[CheckedRequirement(quote=quote, kind="result", status=status,
                                                            delivered_by=list(keys)) for quote, status, keys in results],
                           **extra)


def _decision(check, **extra) -> TaskDecision:
    return TaskDecision.model_validate({"action": "no_tool", "in_scope": True, "should_execute": False,
                                        "confidence": 0.5, "reason": "r", "capability_match_status": "fallback",
                                        "match_basis": "partial_evidence", "matched_actions": ["run_bonobo"],
                                        "capability_check": check.model_dump(), **extra})


DRAGON_BOTH = (("a network linking the layers", "available", ["dragon.two_layer_network"]),
               ("a p-value for each edge", "available", ["dragon.edge_pvalues"]))


def test_one_workflow_for_every_result_is_adopted_and_a_step_outside_counts():
    adopted = checked_match(_decision(_check(*DRAGON_BOTH)), POLICY.workflows)
    assert adopted.matched_actions == ["run_dragon"] and adopted.recommended_actions == ["run_dragon"]
    with_step = _check(("subtypes", "available", ["sambar.subtypes"]),
                       ("survival", "with_step", ["sambar.clinical_comparison"]))
    assert checked_match(_decision(with_step), POLICY.workflows).matched_actions == ["run_sambar"]


@pytest.mark.parametrize("decision", [
    # routing's own exact match or tie is never replaced (n11 VT1-2: routing right, the check wrong)
    _decision(_check(*DRAGON_BOTH), capability_match_status="exact"),
    _decision(_check(*DRAGON_BOTH), capability_match_status="ambiguous", hypothesis_actions=["run_bonobo", "run_cobra"]),
    # two workflows deliver every result: no single verdict to adopt
    _decision(_check(("one TF-gene network", "available", ["panda.tf_gene_network", "otter.tf_gene_network"]))),
    # a result the check did not credit
    _decision(_check(DRAGON_BOTH[0], ("the causal direction of each link", "not_available", []))),
    # different workflows for different results
    _decision(_check(DRAGON_BOTH[0], ("subtypes", "available", ["sambar.subtypes"]))),
    # the check did not confirm it, or left a sentence unread
    _decision(_check(*DRAGON_BOTH, provisional=True)),
    _decision(_check(*DRAGON_BOTH, unchecked=["We also want a dashboard."])),
    # the user stated hypotheses
    _decision(_check(*DRAGON_BOTH), stated_hypotheses=[{"axis": "a", "basis": "run_dragon", "text_span": "h"}]),
])
def test_nothing_is_adopted_otherwise(decision):
    assert checked_match(decision, POLICY.workflows) is decision


def test_routing_records_the_adopted_match_and_its_candidates(monkeypatch):
    from netzoo_agent_core.graph import router_invocation

    events = []
    monkeypatch.setattr(router_invocation, "record_event", lambda *args: events.append(args[2:4]))
    stored = TaskDecision.model_validate(RECORDED["KP2"]["decision"])
    invocation = router_invocation._RouterInvocation(
        decision=stored, routing_state={"semantic_goal": {"goal": "p-values", "candidates": ["run_bonobo"]}},
        usage=None, budget_warnings=[], reason_code=None)

    result = router_invocation._with_checked_match(SimpleNamespace(project_policy=POLICY), {}, invocation)

    assert result.decision.matched_actions == ["run_dragon"]
    assert result.routing_state["semantic_goal"] == {"goal": "p-values", "candidates": ["run_dragon"],
                                                     "relationship": "single", "match_status": "exact",
                                                     "match_basis": CHECK_MATCH_BASIS}
    assert events == [("routing.check_match_adopted", "classify")]
    assert router_invocation._with_checked_match(SimpleNamespace(project_policy=POLICY), {}, result) is result
