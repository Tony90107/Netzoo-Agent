"""Verdict layer step 2: a result waits on a fact the user said they do not know, only when the fact decides it.

Blind set heldout416b UNKNOWN_INPUT: 0/10 such requests were asked about; feasibility eval F46 was refused.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import proposal_model, unstated_conditions  # noqa: E402
from netzoo_agent_core.graph import router_invocation  # noqa: E402
from netzoo_agent_core.graph.response import respond  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402

CONDOR = ("Run CONDOR on the network my student made. I can't recall whether it connects TFs to genes or genes to "
          "genes.")
COEXPRESSION = ("I want a per-sample co-expression network from my count matrix. I am not sure whether the prior I "
                "downloaded includes miRNAs.")


def _ask(quote, delivered, **attrs):
    return {"quote": quote, "delivered_by": list(delivered), "not_by": [], "scale": "unstated", "omics_layers": 0,
            "data_unit": "not_stated", "regulator_kinds": [], "needs_sign": False, "input_network": "none",
            "group_membership": "not_about_groups", "time_model": "not_dynamic", "spatial": "not_spatial",
            "asked_as": "request", **attrs}


def _check(task, ask, unknown_quote, about):
    conditions = {**unstated_conditions(), "unknown_facts": [{"quote": unknown_quote, "about": about}]}
    proposal = proposal_model(2).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": [ask]},
        "s2": {"role": "background", "has": [unknown_quote], "about_methods": [], "asks": []},
        "conditions": conditions})
    return build_capability_check(task, proposal)[0]


def _condor_check(input_network="gene_gene"):
    return _check(CONDOR, _ask("Run CONDOR on the network my student made", ["condor.communities"],
                               input_network=input_network),
                  "I can't recall whether it connects TFs to genes or genes to genes", "input_network")


def test_a_deciding_unknown_fact_makes_the_result_wait_instead_of_a_gap():
    """F46 / heldout416b B20: the model guessed gene-gene, which rules CONDOR out -- the user said they do not know."""
    check = _condor_check()
    (item,) = check.needed_facts()
    assert item.depends_on == "input_network" and not check.full_gap
    assert item.outcomes == {"regulator_gene": ["condor.communities"], "gene_gene": []}


def test_an_unknown_fact_that_changes_nothing_is_never_asked_about():
    check = _check(COEXPRESSION, _ask("a per-sample co-expression network", ["bonobo.per_sample_networks"],
                                      scale="per_sample"),
                   "I am not sure whether the prior I downloaded includes miRNAs", "regulator_kinds")
    assert check.needed_facts() == [] and check.results()[0].status == "available"


def test_unknown_words_not_in_the_request_are_ignored():
    check = _check(CONDOR, _ask("Run CONDOR on the network my student made", ["condor.communities"],
                                input_network="gene_gene"),
                   "I do not know the node roles", "input_network")
    assert check.needed_facts() == []


def _invocation(check, action):
    decision = TaskDecision(action=action, in_scope=True, should_execute=action != "no_tool", confidence=0.9,
                            reason="r", capability_match_status="exact", matched_actions=["run_condor"],
                            capability_check=check)
    return router_invocation._RouterInvocation(decision=decision, routing_state={}, usage=None, budget_warnings=[],
                                               reason_code=None)


def test_a_waiting_turn_selects_and_runs_nothing_and_asks_one_question(monkeypatch):
    monkeypatch.setattr(router_invocation, "record_event", lambda *args: None)
    check = _condor_check()
    from netzoo_agent_core.interpretation.needed_facts import waiting_decision

    waiting = waiting_decision(_invocation(check, "run_condor").decision, check)
    assert waiting.action == "no_tool" and not waiting.should_execute and waiting.matched_actions == []
    assert waiting.hypothesis_actions == ["run_condor"]
    reply = respond(None, {"decision": waiting.model_dump(), "messages": []})
    text = reply["messages"][-1].content
    assert reply["reply_kind"] == "needs_fact"
    assert ("depends on whether your network links regulators to genes or genes to genes, which you said you do not "
            "know") in text
    assert "if regulators to genes: CONDOR; if genes to genes: no registered workflow gives this." in text
    assert "Before I choose a workflow, please tell me: Does your network link regulators" in text
    assert "No registered workflow produces" not in text


def test_the_run_path_waits_too(monkeypatch):
    """heldout416b B20 ("Run community detection on the network my student made ..."): a run is not planned."""
    monkeypatch.setattr(router_invocation, "record_event", lambda *args: None)
    proposal = proposal_model(2).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": [
            _ask("Run CONDOR on the network my student made", ["condor.communities"], input_network="gene_gene")]},
        "s2": {"role": "background", "has": [], "about_methods": [], "asks": []},
        "conditions": {**unstated_conditions(), "unknown_facts": [
            {"quote": "I can't recall whether it connects TFs to genes or genes to genes", "about": "input_network"}]}})
    updated = router_invocation._with_run_check(None, {}, CONDOR, _invocation(None, "run_condor"), proposal, "ok")
    assert updated.decision.action == "no_tool" and updated.decision.capability_check.needed_facts()


def _puma_decision(delivered=("puma.regulator_gene_network",), plan=None):
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement

    requirement = CheckedRequirement(quote="a TF and miRNA regulatory network", kind="result", status="available",
                                     delivered_by=list(delivered))
    check = CapabilityCheck(requirements=[requirement], unknowns=[[
        "regulator_kinds", "The target prior I downloaded may include miRNA-target pairs or may only hold TF-gene "
                           "motif hits"]])
    return TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                        capability_check=check, data_plan=plan)


def test_an_unknown_mirna_input_a_credited_workflow_takes_is_asked_in_the_users_words():
    """Pre-measure B23: PUMA gives the network either way; what waits is PUMA's miRNA input."""
    from netzoo_agent_core.interpretation.data_plan import plan_with_unknowns, render_plan_block

    plan = plan_with_unknowns(None, _puma_decision())
    (need,) = plan.needs
    assert (need.kind, need.action) == ("mirna", "ask")
    assert render_plan_block(plan, "") == (
        '**Data your question needs.** Your question needs a miRNA list, and you said you do not know whether your '
        'data has it ("The target prior I downloaded may include miRNA-target pairs or may only hold TF-gene motif '
        'hits"). Does it?')


def test_no_mirna_ask_when_no_credited_workflow_takes_it_or_the_request_rules_it_out():
    from netzoo_agent_core.contracts.data_plan import DataNeed, DataPlan
    from netzoo_agent_core.interpretation.data_plan import plan_with_unknowns

    assert plan_with_unknowns(None, _puma_decision(("panda.tf_gene_network",))) is None
    ruled_out = DataPlan(answerable=True, basis="question", needs=[DataNeed(
        kind="mirna", state="ruled_out", source="model", quote="the miRNA list is missing", action="say_ruled_out")])
    assert plan_with_unknowns(ruled_out, _puma_decision(plan=ruled_out)) is ruled_out


def _blank(quote, **attrs):
    from netzoo_agent_core.contracts.capability_check import CheckedRequirement

    base = {"scale": "unstated", "omics_layers": 2, "data_unit": "not_stated", "regulator_kinds": [],
            "needs_sign": False, "input_network": "none", "group_membership": "not_about_groups",
            "time_model": "not_dynamic", "spatial": "not_spatial"}
    return CheckedRequirement(quote=quote, kind="result", status="not_available", blank=True, attrs={**base, **attrs})


DRAGON_PAIRS = [(0, "run_dragon", ["dragon.two_layer_network", "dragon.edge_pvalues"]),
                (0, "run_lioness_dragon", ["lioness_dragon.per_sample_networks"])]


def test_an_unknown_fact_decides_among_the_workflows_the_second_opinion_weighed():
    """Live B30: nothing credited, second opinion 'part' for DRAGON/LIONESS-DRAGON, layer count unknown -> wait."""
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck
    from netzoo_agent_core.interpretation.capability_check import wait_on_asked

    check = CapabilityCheck(requirements=[_blank("partial-correlation networks linking my omics layers")],
                            full_gap=True, unknowns=[["omics_layers", "whether there are two layers or more"]])
    updated = wait_on_asked(check, DRAGON_PAIRS)
    (item,) = updated.needed_facts()
    assert not updated.full_gap and item.depends_on == "omics_layers"
    assert item.outcomes["3"] == [] and "dragon.two_layer_network" in item.outcomes["2"]


def test_without_an_unknown_fact_or_a_deciding_one_the_gap_stands():
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck
    from netzoo_agent_core.interpretation.capability_check import wait_on_asked

    plain = CapabilityCheck(requirements=[_blank("a network")], full_gap=True)
    assert wait_on_asked(plain, DRAGON_PAIRS) is plain
    undecided = CapabilityCheck(requirements=[_blank("a network")], full_gap=True,
                                unknowns=[["data_unit", "not sure"]])
    assert wait_on_asked(undecided, [(0, "run_dragon", [])]) is undecided
