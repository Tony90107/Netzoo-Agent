"""Log 404: what the capability check did not verify is never presented as verified.

heldout11 (Log 403 n11 round, candidate arm), replayed from the stored decisions; nothing calls a model:
- VN5q: "Is there a method that models how each TF-gene edge at one time point depends on the
  edges at the previous time point?" was read as a question about methods, so no result was
  checked, and four TF-network workflows were said to "all fit" (3 of 3 false commitments).
- VT2: "each gene should be allowed to sit in several communities at once" was read as a
  constraint; CONDOR "fits that result" while its description says one community per node.
- VC4s-2: "find each community's core genes" came back blank beside communities credited to
  CONDOR, and no second opinion was asked because the request as a whole was no gap.
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
from netzoo_agent_core.interpretation.capability_check import blank_requirement_pairs  # noqa: E402
from netzoo_agent_core.interpretation.unconfirmed_routes import checked_no_result, confirms_nothing  # noqa: E402
from netzoo_agent_core.reply_cards import build_reply_card  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
RECORDED = json.loads((ROOT / "tests" / "log404_decisions.json").read_text())["decisions"]
FIT_WORDS = ("These all fit", "fits that result", "Selected path", "fits your goal", "Recommended", "Best match")


def _replay(task: str, decision: TaskDecision):
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task, decision=decision.model_dump(), status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None}
    out = respond(SimpleNamespace(project_policy=POLICY), state)
    result = {**state, "messages": [HumanMessage(content=task), out["messages"][-1]], "reply_kind": out["reply_kind"]}
    prompt = build_next_turn_prompt(result)
    return str(out["messages"][-1].content), out["reply_kind"], build_reply_card(result, prompt, POLICY, task=task), prompt


@pytest.mark.parametrize("item", ["VN5q", "VT2"])
def test_routings_workflows_are_unconfirmed_when_the_check_read_no_result(item):
    recorded = RECORDED[item]
    decision = TaskDecision.model_validate(recorded["decision"])
    assert checked_no_result(decision.capability_check) and confirms_nothing(decision.capability_check)

    reply, kind, card, prompt = _replay(recorded["task"], decision)

    assert kind == "capability_unconfirmed"
    assert "found no result in your request to check them against" in reply
    text = reply + json.dumps(card.model_dump())
    assert not any(words in text for words in FIT_WORDS)
    resolutions = {step.resolution for step in card.next_steps} | {
        option.resolution for option in (card.choices.options if card.choices else [])}
    assert not resolutions & {"confirm_workflow", "plan_workflow"}
    assert not prompt.allow_workflow_continuation


def _methods_only(quote: str) -> CapabilityCheck:
    return CapabilityCheck(requirements=[CheckedRequirement(quote=quote, kind="about_methods", status="not_checked")])


def test_a_question_about_how_a_named_workflow_works_is_not_an_unchecked_result():
    assert not checked_no_result(_methods_only("How does PANDA use the PPI network?"))
    assert not checked_no_result(_methods_only("What does lioness assume about the cohort?"))
    assert checked_no_result(_methods_only("Is there a method that models time lags between TFs and targets?"))


def test_a_check_that_found_a_result_or_did_not_run_is_not_counted():
    found = CapabilityCheck(requirements=[CheckedRequirement(
        quote="one TF-gene network", kind="result", status="available", delivered_by=["panda.network"])])
    assert not checked_no_result(found)
    assert not checked_no_result(CapabilityCheck(unavailable=True))
    assert confirms_nothing(CapabilityCheck(unavailable=True))
    assert not confirms_nothing(None)


def test_a_blank_verdict_beside_a_found_result_is_asked_about_its_implied_workflows():
    check = TaskDecision.model_validate(RECORDED["VC4s"]["decision"]).capability_check
    assert not check.full_gap
    pairs = blank_requirement_pairs(check)
    assert [(check.requirements[index].quote, action) for index, action, _keys in pairs] == [
        ("find each community's core genes", "run_condor")]
    assert "condor.core_scores" in pairs[0][2]


def test_a_blank_verdict_whose_attributes_point_nowhere_and_a_cited_near_miss_are_not_asked():
    """heldout11 VP1, VP2, VP3, VP4: a dashboard, a narrative report, causal direction and a DE table."""
    def result(quote, status, **extra):
        return CheckedRequirement(quote=quote, kind="result", status=status, attrs={
            "scale": "whole_cohort", "omics_layers": 0, "data_unit": "not_stated", "regulator_kinds": [],
            "needs_sign": False, "input_network": "none"}, **extra)

    check = CapabilityCheck(requirements=[
        result("finds the communities in our bipartite TF-gene network", "available", delivered_by=["condor.communities"]),
        result("writes a narrative report on their biology automatically", "not_available", blank=True),
        result("a differential expression table of smokers versus non-smokers", "not_available",
               not_by=["cobra.no_differential_expression"]),
    ])
    assert blank_requirement_pairs(check) == []


def test_a_blank_verdict_is_credited_when_the_second_opinion_says_its_workflow_gives_it(monkeypatch):
    from netzoo_agent_core.contracts.capability_check import proposal_model
    from netzoo_agent_core.graph import router_invocation

    task = RECORDED["VC4s"]["task"]
    plain = {"scale": "whole_cohort", "omics_layers": 0, "data_unit": "bulk_samples", "regulator_kinds": ["tf"],
             "needs_sign": False, "input_network": "regulator_gene", "group_membership": "not_about_groups",
             "time_model": "not_dynamic", "spatial": "not_spatial", "asked_as": "request"}
    proposal = proposal_model(2).model_validate({
        "s1": {"role": "background", "has": ["We have a bipartite TF-gene network from an earlier PANDA run."],
               "about_methods": [], "asks": []},
        "s2": {"role": "asks", "has": [], "about_methods": [], "asks": [
            {**plain, "quote": "split it into communities, with each gene in exactly one community",
             "delivered_by": ["condor.communities"], "not_by": [], "group_membership": "one_group"},
            {**plain, "quote": "find each community's core genes", "delivered_by": [], "not_by": []}]}})
    asked = []
    monkeypatch.setattr(router_invocation, "record_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(router_invocation, "request_second_opinion",
                        lambda context, state, pairs, usage, warnings, situation=():
                        (asked.extend(pairs) or ["all"] * len(pairs), usage, warnings))
    exact = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                         capability_match_status="exact", matched_actions=["run_condor"])
    invocation = router_invocation._RouterInvocation(decision=exact, routing_state={}, usage=None,
                                                     budget_warnings=[], reason_code=None)

    check = router_invocation._with_capability_check(None, {}, task, invocation, proposal).decision.capability_check

    assert [quote for quote, _workflow, _text in asked] == ["find each community's core genes"]
    core = check.results()[1]
    assert core.status == "available" and core.second_opinion and "condor.core_scores" in core.delivered_by
    # A backup reading is reported, never acted on, so no second opinion is spent on it.
    asked.clear()
    router_invocation._with_capability_check(None, {}, task, invocation, proposal, provisional=True)
    assert asked == []
