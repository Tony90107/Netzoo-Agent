"""Source-recorded regressions for method goals and the approval/check boundary."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import TaskDecision
from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement, proposal_model
from netzoo_agent_core.graph import router_invocation
from netzoo_agent_core.interpretation.capability_check import build_capability_check
from netzoo_agent_core.interpretation.core_decision import decide_core, with_core

CASES = json.loads((Path(__file__).parent / "fixtures/judgment_repairs/goal_input_cases.json").read_text())


def recorded(name):
    row = CASES[name]
    count = sum(key[1:].isdigit() for key in row["proposal"])
    proposal = proposal_model(count).model_validate(row["proposal"])
    check, _ = build_capability_check(row["task"], proposal)
    decision = TaskDecision.model_validate(row["decision"]).model_copy(update={"capability_check": check})
    return row["task"], decision


@pytest.mark.parametrize("name", ["H46", "J06", "J29"])
def test_unresolved_method_results_are_clarified_even_for_a_run(name):
    task, decision = recorded(name)
    core = decide_core(decision, task)
    held = with_core(decision, core)
    assert core.kind == "CLARIFY"
    assert core.clarify and len(core.clarify.candidates) == 2
    assert held.action == "no_tool" and not held.should_execute and not held.execution_requested


def test_approved_run_carries_the_check_that_still_has_an_open_goal(monkeypatch):
    check = CapabilityCheck(goal="purpose_only", goal_quote="I need results by Friday")
    decision = TaskDecision(action="run_dragon", in_scope=True, should_execute=True, reason="run", confidence=0.9,
                            matched_actions=["run_dragon"])
    result = router_invocation._RouterInvocation(decision=decision, routing_state={}, usage=None,
                                                 budget_warnings=[], reason_code="test")
    monkeypatch.setattr(router_invocation, "record_event", lambda *args: None)
    out = router_invocation._on_run_verdict(None, {}, "I need results by Friday", result, check, "ok")
    assert out.decision.capability_check == check
    assert decide_core(out.decision).kind == "CLARIFY"


def test_a_method_only_in_an_input_description_does_not_define_the_goal():
    check = CapabilityCheck(goal="purpose_only", goal_quote="our PANDA network is the input",
                            requirements=[CheckedRequirement(quote="our PANDA network is the input",
                                                             kind="context", status="not_checked")])
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, reason="read", confidence=0.9,
                            capability_check=check)
    assert decide_core(decision).kind == "CLARIFY"


@pytest.mark.parametrize("quote", ["Build a TF-gene network from mutation data only",
                                     "Produce differential modularity", "Train a prediction model"])
def test_concrete_unsupported_results_remain_declined(quote):
    row = CheckedRequirement(quote=quote, kind="result", status="not_available", blank=True)
    check = CapabilityCheck(goal="result_named", goal_quote=quote, requirements=[row], full_gap=True)
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, reason="read", confidence=0.9,
                            capability_check=check)
    assert decide_core(decision, quote).kind == "DECLINE"


def test_two_methods_for_an_explicitly_read_result_do_not_create_a_goal_question():
    quote = "a TF-gene network"
    check = CapabilityCheck(goal="method_named", goal_quote="PANDA or PUMA", requirements=[
        CheckedRequirement(quote=quote, kind="result", status="available", delivered_by=["panda.tf_gene_network"])])
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, reason="read", confidence=0.9,
                            capability_check=check)
    assert decide_core(decision).kind == "DO"


def test_known_input_rejection_cannot_be_overridden_by_a_capability_credit():
    from netzoo_agent_core.interpretation.checked_match import checked_match
    from netzoo_agent_core.policy import ProjectPolicyLoader
    from netzoo_agent_core.routing.method_rejections import rejected_methods_for

    task, decision = recorded("H37")
    decision = decision.model_copy(update={
        "rejected_methods": rejected_methods_for(task, ["expression_matrix"], actions=["run_condor"])})
    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()
    assert checked_match(decision, policy.workflows).matched_actions == decision.matched_actions


