"""Options-first decision, step 7: the hybrid hard gates on the live path's DO (no model calls).

The gate read and the requirement check are faked; `workflow_gate` and `gated_core` are code. A workflow some contract
condition rules out is never offered as runnable; with none left the live call is DECLINE in the contract's words; a
requirement no offered contract addresses is asked as a must under the 9/10 rule; a gate that cannot run changes
nothing.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import LLMUsage  # noqa: E402
from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.contracts.menu_reading import MenuReading, Requirement, SettingAsked, Wanted  # noqa: E402
from netzoo_agent_core.graph import hybrid_gate_call  # noqa: E402
from netzoo_agent_core.interpretation.ask_facts import ask_reply  # noqa: E402
from netzoo_agent_core.interpretation.core_views import decline_reply  # noqa: E402
from netzoo_agent_core.interpretation.hybrid_gates import gated_core  # noqa: E402
from netzoo_agent_core.interpretation.menu_decision import workflow_gate  # noqa: E402
from netzoo_agent_core.interpretation.menu_focus import focus_limits, gate_model  # noqa: E402

DO = CoreDecision(kind="DO", basis="results_given", workflows=["GIRAFFE"])


def test_an_unsupported_setting_rules_its_workflow_out_in_the_contracts_words():
    reading = MenuReading(wanted=[Wanted(quote="")], data=["expression", "motif_prior", "ppi"], settings=[
        SettingAsked(quote="a custom learning rate of 0.001", workflow="GIRAFFE", control="unregistered")])
    verdict = workflow_gate(reading, "GIRAFFE")
    assert verdict.reasons and "package defaults" in verdict.reasons[0]
    core = gated_core(DO, {"GIRAFFE": verdict})
    assert core.kind == "DECLINE" and core.basis == "hybrid_gate"
    assert "NetZoo cannot run GIRAFFE for this because NetZoo runs GIRAFFE with its package defaults" in \
        decline_reply(core)


def test_data_the_user_lacks_and_a_contradicted_requirement_are_reasons():
    condor = MenuReading(wanted=[Wanted(quote="")], data_absent=["regulator_gene_network"])
    assert "regulator_gene_network" in workflow_gate(condor, "CONDOR").reasons[0]
    dragon = MenuReading(wanted=[Wanted(quote="", requirements=[Requirement(
        quote="a lambda_inter of 0.2 controlling only the cross-layer edges", verdicts={"DRAGON": "contradicted"})])],
        data=["expression", "methylation"])
    assert any("contract contradicts" in r for r in workflow_gate(dragon, "DRAGON").reasons)


def test_a_tie_keeps_the_workflows_that_pass():
    core = CoreDecision(kind="DO", basis="results_given", workflows=["PANDA", "OTTER"])
    reading = MenuReading(wanted=[Wanted(quote="")], data=["expression", "motif_prior", "ppi"], settings=[
        SettingAsked(quote="an L1 sparsity penalty", workflow="OTTER", control="unregistered")])
    gated = gated_core(core, {name: workflow_gate(reading, name) for name in ("PANDA", "OTTER")})
    assert gated.kind == "DO" and gated.workflows == ["PANDA"] and gated.declined


def test_a_requirement_no_contract_addresses_is_asked_as_a_must_under_the_nine_in_ten_rule():
    reading = MenuReading(wanted=[Wanted(quote="", requirements=[Requirement(
        quote="found with the Louvain algorithm", verdicts={"CONDOR": "not_addressed"})])],
        data=["regulator_gene_network"])
    verdict = workflow_gate(reading, "CONDOR")
    assert not verdict.reasons and verdict.must_ask == ["found with the Louvain algorithm"]
    gated = gated_core(CoreDecision(kind="DO", basis="results_given", workflows=["CONDOR"]), {"CONDOR": verdict})
    assert gated.kind == "ASK" and gated.basis == "hybrid_requirement"
    text = ask_reply(gated)
    assert 'Is this a must for your analysis: "found with the Louvain algorithm"?' in text and 'contract: ""' not in text


def test_a_passing_do_is_unchanged_but_records_the_check():
    reading = MenuReading(wanted=[Wanted(quote="")], data=["expression", "motif_prior", "ppi"])
    gated = gated_core(CoreDecision(kind="DO", basis="run", workflows=["PANDA"], run_allowed=True),
                       {"PANDA": workflow_gate(reading, "PANDA")})
    assert gated.kind == "DO" and gated.run_allowed and gated.evidence["hybrid_gate"]["judged"] == ["PANDA"]
    other = CoreDecision(kind="ASK", basis="fact_agent")
    assert gated_core(other, {"PANDA": workflow_gate(reading, "PANDA")}) is other


def _context(llm):
    return SimpleNamespace(study_purpose_llm=llm, semantic_model_name="openai/gpt-4o-mini", router_max_tokens=1200,
                           task_token_budget=200_000, price_catalog=None)


def test_the_gate_call_declines_a_live_do_and_a_failed_call_changes_nothing(monkeypatch):
    events = []
    monkeypatch.setenv("NETZOO_HYBRID_GATES", "1")  # off by default since the user's decision 2026-10-19 (c)
    monkeypatch.setattr(hybrid_gate_call, "record_event", lambda *a: events.append(a[2]))
    monkeypatch.setattr(hybrid_gate_call, "preflight_budget",
                        lambda context, state, **kw: (SimpleNamespace(status="ok"), state["budget_warnings"]))
    monkeypatch.setattr(hybrid_gate_call, "append_llm_usage", lambda usage, **kw: usage)
    task = "I'd like GIRAFFE run on 75 AML samples with a custom learning rate of 0.001."
    limits = focus_limits(("GIRAFFE",))
    payload = {"settings": {}, "counts": {n: {"status": "not_mentioned", "value": None, "values": [], "quote": ""}
                                           for n in limits["counts"]},
               "data": {k: {"status": "not_mentioned", "quote": ""} for k in limits["data"]},
               "conditions": {n: {"status": "not_mentioned", "value": None, "values": [], "quote": ""}
                              for n in limits["conditions"]},
               "unsupported_settings": [{"quote": "a custom learning rate of 0.001", "workflow": "GIRAFFE",
                                         "value": "0.001", "asks_to_set": True}],
               "requirements": []}
    gate_model(("GIRAFFE",)).model_validate(payload)

    class Model:
        def with_structured_output(self, schema, **kwargs):
            return SimpleNamespace(invoke=lambda messages: {"parsed": schema.model_validate(payload), "raw": None})

    core, _usage, _warnings = hybrid_gate_call.apply_hybrid_gates(
        _context(Model()), {"budget_warnings": []}, None, DO, task, LLMUsage(budget_tokens=200_000), [])
    assert core.kind == "DECLINE" and "core.hybrid_gate" in events

    class Broken:
        def with_structured_output(self, *args, **kwargs):
            raise RuntimeError("provider down")

    core, _usage, _warnings = hybrid_gate_call.apply_hybrid_gates(
        _context(Broken()), {"budget_warnings": []}, None, DO, task, LLMUsage(budget_tokens=200_000), [])
    assert core is DO
    core, *_ = hybrid_gate_call.apply_hybrid_gates(_context(None), {}, None, DO, task, LLMUsage(budget_tokens=1), [])
    assert core is DO  # no model configured (tests, the harness): no gate
