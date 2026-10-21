"""Check failures and unread settings must not turn into successful approvals."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import TaskDecision
from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement
from netzoo_agent_core.contracts.fact_check import FactCheck
from netzoo_agent_core.contracts.request_facts import RequestFact
from netzoo_agent_core.interpretation.core_decision import decide_core, with_core
from netzoo_agent_core.interpretation.method_conditions import unresolved_settings


DOUBT = "I don't know whether my values were centered"
TASK = "Run BONOBO. " + DOUBT + "."


def decision(check, status="blocked"):
    return TaskDecision(action="run_bonobo", in_scope=True, should_execute=True, execution_requested=True,
                        confidence=0.9, reason="read", matched_actions=["run_bonobo"], capability_check=check,
                        fact_check=FactCheck(status=status, candidates=["BONOBO"]))


def available(**extra):
    return CapabilityCheck(requirements=[CheckedRequirement(
        quote="Run BONOBO", kind="result", status="available", delivered_by=["bonobo.per_sample_networks"])], **extra)


@pytest.mark.parametrize("status", ["failed", "blocked"])
def test_failed_necessary_fact_check_holds_execution_without_guessing_an_answer(status):
    run = decision(available(uncertain_quotes=[DOUBT]), status)
    core = decide_core(run, TASK)
    assert (core.kind, core.basis) == ("UNCHECKED", "fact_check_incomplete")
    assert core.evidence["unchecked_fact_quotes"] == [DOUBT]
    held = with_core(run, core)
    assert held.action == "no_tool" and not held.should_execute and not held.execution_requested
    assert not held.matched_actions


def test_failed_optional_check_with_no_witnessed_doubt_does_not_create_a_question():
    core = decide_core(decision(available()), "Run BONOBO.")
    assert core.kind == "DO" and not core.facts


def test_an_invented_doubt_is_not_a_reason_to_hold_a_run():
    core = decide_core(decision(available(uncertain_quotes=["I don't know the number of genes"])), TASK)
    assert core.kind == "DO"


def test_successful_fact_check_can_find_no_deciding_question():
    core = decide_core(decision(available(uncertain_quotes=[DOUBT]), "checked"), TASK)
    assert core.kind == "DO" and not core.facts


def test_failed_fact_call_preserves_an_existing_grounded_question():
    row = CheckedRequirement(quote="my network", kind="result", status="needs_fact", depends_on="input_network",
                             unknown_quote="I don't know the node types",
                             outcomes={"regulator_gene": ["condor.communities"], "gene_gene": []})
    core = decide_core(decision(CapabilityCheck(requirements=[row])), "I don't know the node types")
    assert core.kind == "ASK" and core.facts[0].user_quote == "I don't know the node types"


def test_a_count_already_decided_in_code_does_not_require_another_fact_call():
    quote = "nine or seventeen samples"
    check = available(uncertain_quotes=[quote], count_alternatives=[{"of": "sample_count", "quote": quote,
                                                                  "values": [9, 17]}])
    core = decide_core(decision(check), "Run BONOBO on " + quote)
    assert core.kind == "DO" and not core.facts


def test_methods_only_question_retains_unparsed_request_level_setting():
    quote = "normalization sparse-ish"
    check = CapabilityCheck(goal="method_named", goal_quote="SAMBAR", facts=[RequestFact(
        id="setting", property="setting", name="SAMBAR.norm_patient", value="sparse-ish", quote=quote)])
    run = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="read",
                       matched_actions=["run_sambar"], capability_check=check)
    core = decide_core(run, "Can SAMBAR use " + quote + "?")
    assert core.kind == "ASK" and core.facts[0].depends_on == "SAMBAR.norm_patient"


def test_a_base_workflow_setting_is_checked_for_its_registered_lioness_variant():
    # A number given as two values is unsettled (a number given without digits is no value: `stated_no_value`).
    method = {"settings": [{"name": "DRAGON.lambda1", "quote": "lambda1 0.2 or 0.5", "value": "0.2 or 0.5"}]}
    unresolved = unresolved_settings(method, ["lioness_dragon.per_sample_networks"])
    assert unresolved and unresolved[0]["workflow"] == "LIONESS-DRAGON"


def test_a_run_held_for_an_unparsed_setting_asks_for_that_setting(monkeypatch):
    from netzoo_agent_core.graph import router_invocation

    task = "Run SAMBAR with normalization sparse-ish."
    row = CheckedRequirement(quote=task, kind="result", status="available", delivered_by=["sambar.subtypes"],
                             method={"named": "SAMBAR", "named_quote": "SAMBAR", "settings": [
                                 {"name": "SAMBAR.norm_patient", "quote": "normalization sparse-ish",
                                  "value": "sparse-ish"}]})
    check = CapabilityCheck(requirements=[row])
    run = TaskDecision(action="run_sambar", in_scope=True, should_execute=True, confidence=0.9,
                       reason="read", capability_check=check)
    result = router_invocation._RouterInvocation(decision=run, routing_state={}, usage=None,
                                                 budget_warnings=[], reason_code="test")
    monkeypatch.setattr(router_invocation, "record_event", lambda *args: None)
    held = router_invocation._on_run_verdict(None, {}, task, result, check, "ok").decision
    assert held.run_verdict.held and held.action == "no_tool"
    core = decide_core(held, task)
    assert (core.kind, core.basis) == ("ASK", "setting_unresolved")


