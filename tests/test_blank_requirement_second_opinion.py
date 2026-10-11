"""Log 404 part 2: a blank verdict beside results the check found gets Log 397's second opinion.

heldout11 n11 VC4s-2 (candidate arm, replayed from the stored decision; nothing calls a model):
"find each community's core genes" came back blank beside communities credited to CONDOR, and no
second opinion was asked because the request as a whole was no gap. Part 1 (routing's workflows
listed as unconfirmed when the check read no result) was withdrawn on heldout12 (Log 404).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import blank_requirement_pairs  # noqa: E402

RECORDED = json.loads((ROOT / "tests" / "log404_decisions.json").read_text())["decisions"]


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
