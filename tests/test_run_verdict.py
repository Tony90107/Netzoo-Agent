"""Verdict layer items 1-2 (2026-10-14): a run the capability check did not approve is never an approved plan.

Item 1: the run routing selected goes ahead only under an approving verdict; a run of another workflow than the one
the check credits, or of one that gives only part of what was asked, is held, said and offered (engineering review of
923e493: both kept their run). Item 2: the Plan Evaluator requires that verdict, for the plan's workflow and the
current request, and the executor checks it once more; injected states that lack it never reach the executor.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_routing import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.cli.follow_up import build_next_turn_prompt  # noqa: E402
from netzoo_agent_core.contracts import HumanMessage, TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.contracts.capability_check import RunVerdict, proposal_model  # noqa: E402
from netzoo_agent_core.graph import execution as graph_execution  # noqa: E402
from netzoo_agent_core.graph import router_invocation  # noqa: E402
from netzoo_agent_core.graph.response import respond  # noqa: E402
from netzoo_agent_core.graph.transitions import route_plan_evaluation  # noqa: E402
from netzoo_agent_core.interpretation.run_check import request_sha256, run_check_verdict  # noqa: E402
from netzoo_agent_core.planning import build_workflow_plan  # noqa: E402
from netzoo_agent_core.reply_cards import build_reply_card  # noqa: E402
from run_approval import approved  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
NAMED = "Run PANDA to build one TF-gene network for each patient."
UNNAMED = "Compute it now: one TF-gene network for each of our 40 patients."
UPLOAD = "Run it now: build TF-gene networks per sample and upload them to a public database."
STEP = "Go ahead and run it: compute TF activity per sample and compare it between tumor and normal."


def _ask(quote, delivered, **attrs):
    return {"quote": quote, "delivered_by": list(delivered), "not_by": [], "scale": "unstated", "omics_layers": 0,
            "data_unit": "not_stated", "regulator_kinds": [], "needs_sign": False, "input_network": "none",
            "group_membership": "not_about_groups", "time_model": "not_dynamic", "spatial": "not_spatial",
            "asked_as": "request", **attrs}


def _proposal(*asks):
    return proposal_model(1).model_validate({"s1": {"role": "asks", "has": [], "about_methods": [], "asks": list(asks)}})


PER_PATIENT = _ask("one TF-gene network for each patient", ["lioness_panda.per_sample_networks"], scale="per_sample")


def _route(task, action, proposal, monkeypatch, *, basis="semantic", status="ok"):
    events = []
    monkeypatch.setattr(router_invocation, "record_event", lambda *args: events.append(args))
    decision = TaskDecision(action=action, in_scope=True, should_execute=True, confidence=0.9, reason="r",
                            intent_type="run_analysis", capability_match_status="exact", match_basis=basis,
                            matched_actions=[action], execution_requested=True)
    invocation = router_invocation._RouterInvocation(decision=decision, routing_state={}, usage=None,
                                                     budget_warnings=[], reason_code=None)
    result = router_invocation._with_run_check(SimpleNamespace(project_policy=POLICY), {}, task, invocation,
                                               proposal, status)
    return result.decision, [event[2] for event in events]


# Item 1: routing --------------------------------------------------------------------------------------------------


def test_a_named_workflow_the_check_finds_another_for_is_held_never_replaced(monkeypatch):
    decision, events = _route(NAMED, "run_panda", _proposal(PER_PATIENT), monkeypatch, basis="workflow_name")
    assert decision.action == "no_tool" and not decision.should_execute
    assert decision.run_verdict.verdict == "other_workflow" and decision.run_verdict.held and decision.run_verdict.named
    assert decision.recommended_actions == ["run_lioness_panda", "run_panda"]
    assert "routing.run_held" in events and "routing.requested_run_adopted" not in events


def test_a_workflow_the_user_did_not_name_is_replanned_as_the_check_credits(monkeypatch):
    task = UNNAMED
    ask = _ask("one TF-gene network for each of our 40 patients", ["lioness_panda.per_sample_networks"],
               scale="per_sample")
    decision, events = _route(task, "run_panda", _proposal(ask), monkeypatch)
    assert decision.action == "run_lioness_panda" and decision.should_execute
    assert decision.run_verdict.verdict == "agrees" and decision.run_verdict.action == "run_lioness_panda"
    assert events[-1] == "routing.run_replanned"


def test_a_run_giving_only_part_of_the_request_is_held_not_narrowed(monkeypatch):
    """User decision 2026-10-14: a part of the task is never run in place of the whole."""
    proposal = _proposal(_ask("build TF-gene networks per sample", ["lioness_panda.per_sample_networks"],
                              scale="per_sample"), _ask("upload them to a public database", []))
    decision, _ = _route(UPLOAD, "run_lioness_panda", proposal, monkeypatch)
    assert decision.action == "no_tool" and decision.run_verdict.verdict == "partial_gap" and decision.run_verdict.held
    assert decision.recommended_actions == ["run_lioness_panda"]


def test_a_run_needing_a_step_outside_netzoo_is_held(monkeypatch):
    """r17 PS1: GIRAFFE's activity matrix plus a test outside NetZoo was planned as the whole request."""
    proposal = _proposal(_ask("compute TF activity per sample", ["giraffe.tf_activity"]),
                         _ask("compare it between tumor and normal", ["giraffe.activity_tests"]))
    decision, _ = _route(STEP, "run_giraffe", proposal, monkeypatch)
    assert decision.run_verdict.verdict == "outside_step" and decision.run_verdict.held


def test_sentences_the_check_did_not_read_hold_the_run():
    check_task = "Run LIONESS-PANDA now. Then upload everything."
    proposal = proposal_model(2).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": [
            _ask("Run LIONESS-PANDA", ["lioness_panda.per_sample_networks"])]},
        "s2": {"role": "asks", "has": [], "about_methods": [], "asks": []}})
    from netzoo_agent_core.interpretation.capability_check import build_capability_check

    check = build_capability_check(check_task, proposal)[0]
    assert check.unchecked == ["Then upload everything."]
    assert run_check_verdict(check, "run_lioness_panda")["verdict"] == "unread"
    assert run_check_verdict(check.model_copy(update={"requirements": []}), "run_lioness_panda")["verdict"] == "unread"


# The reply, the next prompt and the card --------------------------------------------------------------------------


def _held_state(task, decision):
    plan = WorkflowPlan(workflow="none", objective="reply", decision=decision.model_dump(), status="respond_only")
    return {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
            "plan_evaluation": None, "tool_results": []}


def test_a_held_run_says_why_and_offers_each_workflow_for_the_user_to_confirm(monkeypatch):
    decision, _ = _route(NAMED, "run_panda", _proposal(PER_PATIENT), monkeypatch, basis="workflow_name")
    state = _held_state(NAMED, decision)
    reply = respond(SimpleNamespace(project_policy=POLICY), state)
    text = reply["messages"][-1].content
    assert reply["reply_kind"] == "run_held"
    assert 'PANDA does not cover "one TF-gene network for each patient"; LIONESS-PANDA does' in text
    assert "Tell me which one to run, LIONESS-PANDA or PANDA" in text
    assert text.endswith("No files were inspected and no analysis ran.")
    prompt = build_next_turn_prompt(state)
    assert prompt.kind == "recommended_workflow" and prompt.continuation_action == "run_lioness_panda"
    card = build_reply_card({**state, "reply_kind": "run_held"}, prompt, POLICY, task=NAMED)
    assert [step.action for step in card.next_steps if step.resolution == "plan_workflow"] == [
        "run_lioness_panda", "run_panda"]


def test_an_unconfirmed_check_is_said_as_such(monkeypatch):
    decision, _ = _route(NAMED, "run_panda", None, monkeypatch, basis="workflow_name", status="failed")
    text = respond(SimpleNamespace(project_policy=POLICY), _held_state(NAMED, decision))["messages"][-1].content
    assert "the capability check could not confirm this turn that PANDA gives what you asked for" in text
    assert "Tell me to run PANDA anyway" in text


# Item 2: the Plan Evaluator and the executor gate ----------------------------------------------------------------

PANDA_TASK = ("Run PANDA with expression_file=data/lioness-toy/expression.tsv motif_file=data/lioness-toy/motif-panda.tsv "
              "ppi_file=data/lioness-toy/ppi.tsv output_file=out.tsv")


def _panda(**update):
    return TaskDecision(action="run_panda", in_scope=True, should_execute=True, confidence=0.95, reason="run PANDA",
                        intent_type="run_analysis", matched_actions=["run_panda"],
                        expression_file="data/lioness-toy/expression.tsv",
                        motif_file="data/lioness-toy/motif-panda.tsv", ppi_file="data/lioness-toy/ppi.tsv",
                        output_file="out.tsv", **update)


def _verdict(verdict="agrees", *, action="run_panda", task=PANDA_TASK, held=False):
    return RunVerdict(action=action, verdict=verdict, request_sha256=request_sha256(task), held=held)


INJECTED = {
    "no verdict": None,
    "unconfirmed": _verdict("unconfirmed", held=True),
    "another workflow gives it": _verdict("other_workflow", held=True),
    "part of the request": _verdict("partial_gap", held=True),
    "held although agrees": _verdict("agrees", held=True),
    "the request changed": _verdict(task="Run PANDA on my other files."),
    "another workflow's verdict": _verdict(action="run_lioness_panda"),
}


def _ready_plan(run_verdict):
    with patch("netzoo_agent_core.planning.evidence.PROJECT_ROOT", ROOT):
        plan = build_workflow_plan(_panda(), PANDA_TASK)
    assert plan.status == "ready"
    decision = TaskDecision.model_validate(plan.decision).model_copy(update={"run_verdict": run_verdict})
    return plan.model_copy(update={"decision": decision.model_dump()})


def _evaluate(plan, task=PANDA_TASK):
    context = SimpleNamespace(recorder=MagicMock())
    state = {"plan": plan.model_dump(), "messages": [HumanMessage(content=task)]}
    with patch.object(graph_execution, "record_event"):
        return {**state, **graph_execution.evaluate_plan(context, state)}


def _execute(state):
    calls = []
    with patch.object(graph_execution, "execute_selected_tool", side_effect=lambda decision: calls.append(decision)
                      or "ok"), patch.object(graph_execution, "record_event"), \
            patch.object(graph_execution, "structure_tool_result",
                         side_effect=lambda action, decision, raw, **kwargs: SimpleNamespace(
                             status="failed" if raw.startswith("Error") else "success", summary=raw,
                             model_dump=lambda **_: {"status": "failed" if raw.startswith("Error") else "success",
                                                     "raw": raw})):
        update = graph_execution.execute_tool(SimpleNamespace(recorder=MagicMock()), {**state, "current_step": 0})
    return calls, update


@pytest.mark.parametrize("name", list(INJECTED))
def test_an_injected_unapproved_verdict_is_rejected_and_never_reaches_the_executor(name):
    state = _evaluate(_ready_plan(INJECTED[name]))
    assert state["plan_evaluation"]["status"] == "rejected"
    failed = {item["criterion"] for item in state["plan_evaluation"]["rubric"] if item["result"] == "fail"}
    assert failed == {"capability_verdict"}
    assert route_plan_evaluation(state) == "consolidate_memory"
    # Even past the evaluator (a forged approval), the executor gate refuses it.
    forged = {**state, "plan_evaluation": {**state["plan_evaluation"], "status": "approved"}}
    calls, update = _execute(forged)
    assert calls == [] and update["tool_result"]["status"] == "failed"
    assert "no analysis was started" in update["tool_result"]["raw"]


def test_an_approved_verdict_for_this_request_and_workflow_is_executed_once():
    state = _evaluate(_ready_plan(_verdict()))
    assert state["plan_evaluation"]["status"] == "approved" and route_plan_evaluation(state) == "execute_tool"
    calls, update = _execute(state)
    assert len(calls) == 1 and update["tool_result"]["status"] == "success"


def test_a_plan_whose_request_changed_after_approval_is_refused_at_the_executor():
    state = _evaluate(_ready_plan(_verdict()))
    changed = {**state, "messages": [HumanMessage(content="Run PANDA on my other files.")]}
    calls, _ = _execute(changed)
    assert calls == []


def test_a_continued_selection_is_approved_for_its_own_turn_only():
    plan = _ready_plan(_verdict("user_selected"))
    assert _evaluate(plan)["plan_evaluation"]["status"] == "approved"
    assert _evaluate(plan, task="Start planning PANDA")["plan_evaluation"]["status"] == "rejected"


def test_non_analysis_actions_keep_their_own_rules():
    from netzoo_agent_core.interpretation.run_check import run_approval_failures

    for action in ("inspect_inputs", "download_string", "web_search", "no_tool"):
        decision = TaskDecision(action=action, in_scope=True, should_execute=action != "no_tool", confidence=1.0,
                                reason="r")
        assert run_approval_failures(decision, "anything") == []
    assert approved(_panda(), PANDA_TASK).run_verdict.verdict == "agrees"
