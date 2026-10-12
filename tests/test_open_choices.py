"""G2 (feasibility eval 2026-10-12 F37, F43): a choice of result the user leaves open.

Each option is an ask checked against the sheet; two or more options found in the request keep every
workflow unselected, and the reply lists what each option gives and asks one question.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.graph import router_invocation  # noqa: E402
from netzoo_agent_core.graph.response import respond  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import (  # noqa: E402
    build_capability_check, open_choice_groups,
)

F43 = ("Some regulators seem different between patients. I cannot tell if I mean their activity or their "
       "network wiring. Help me choose before planning anything.")
METHODS = "We want a network per sample. Should we use LIONESS-PANDA or BONOBO?"


def _ask(quote, delivered=(), scale="per_sample"):
    return {"quote": quote, "delivered_by": list(delivered), "not_by": [], "scale": scale, "omics_layers": 0,
            "data_unit": "not_stated", "regulator_kinds": [], "needs_sign": False, "input_network": "none",
            "group_membership": "not_about_groups", "time_model": "not_dynamic", "spatial": "not_spatial",
            "asked_as": "request"}


def _sentence(role="background", has=(), asks=(), choices=()):
    return {"role": role, "has": list(has), "about_methods": [], "asks": list(asks),
            "open_choices": [{"options": list(options)} for options in choices]}


def _f43_proposal(wiring=("lioness_panda.per_sample_networks",)):
    return proposal_model(3).model_validate({
        "s1": _sentence(has=["Some regulators seem different between patients."]),
        "s2": _sentence(role="asks", choices=[[_ask("their activity", ["giraffe.tf_activity"]),
                                               _ask("their network wiring", wiring)]]),
        "s3": _sentence(has=["Help me choose before planning anything."]),
    })


def _decision(check, **update):
    return TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                        capability_match_status="exact", matched_actions=["run_puma"],
                        capability_check=check, **update)


def test_two_options_found_in_the_request_are_one_open_choice():
    check, rejected = build_capability_check(F43, _f43_proposal())
    assert rejected == [] and not check.full_gap
    assert [[item.quote for item in group] for group in check.open_choices()] == [
        ["their activity", "their network wiring"]]
    assert open_choice_groups(check)


def test_one_option_found_is_an_ask_and_no_choice():
    proposal = proposal_model(3).model_validate({
        "s1": _sentence(has=["Some regulators seem different between patients."]),
        "s2": _sentence(role="asks", choices=[[_ask("their activity", ["giraffe.tf_activity"]),
                                               _ask("their dynamics over time", ["panda.tf_gene_network"])]]),
        "s3": _sentence(has=["Help me choose before planning anything."]),
    })
    check, rejected = build_capability_check(F43, proposal)
    assert [item["quote"] for item in rejected] == ["their dynamics over time"]
    assert check.open_choices() == [] and [item.quote for item in check.results()] == ["their activity"]


def test_options_naming_workflows_are_a_methods_question_not_a_choice():
    proposal = proposal_model(2).model_validate({
        "s1": _sentence(role="asks", asks=[_ask("We want a network per sample", ["bonobo.per_sample_networks"])]),
        "s2": _sentence(role="asks", choices=[[_ask("LIONESS-PANDA", ["lioness_panda.per_sample_networks"]),
                                               _ask("BONOBO", ["bonobo.per_sample_networks"])]]),
    })
    check, _ = build_capability_check(METHODS, proposal)
    assert check.open_choices() == [] and [item.quote for item in check.results()] == ["We want a network per sample"]


def test_options_one_workflow_gives_alike_keep_routing():
    check, _ = build_capability_check(F43, _f43_proposal(wiring=("giraffe.tf_activity",)))
    assert check.open_choices() and open_choice_groups(check) == []


def test_router_clears_the_selection_and_offers_each_option(monkeypatch):
    check, _ = build_capability_check(F43, _f43_proposal())
    monkeypatch.setattr(router_invocation, "record_event", lambda *args, **kwargs: None)
    invocation = router_invocation._RouterInvocation(
        decision=_decision(check), routing_state={}, usage=None, budget_warnings=[], reason_code=None)
    updated = router_invocation._with_open_choice(None, {}, invocation).decision
    assert updated.matched_actions == [] and updated.recommended_actions == []
    assert updated.hypothesis_actions == ["run_giraffe", "run_lioness_panda"]
    assert updated.capability_match_status == "ambiguous"


def test_reply_lists_each_option_and_asks_one_question():
    check, _ = build_capability_check(F43, _f43_proposal())
    result = respond(None, {"decision": _decision(check).model_dump(), "messages": []})
    text = result["messages"][-1].content
    assert result["reply_kind"] == "open_choice"
    assert '- "their activity": GIRAFFE gives each TF\'s activity in each sample' in text
    assert '- "their network wiring": LIONESS-PANDA gives one TF-gene network per sample' in text
    assert "No workflow has been selected. Which option do you want?" in text
    assert "not matched" not in text and "No registered workflow produces" not in text


def test_an_unconfirmed_check_never_holds_a_choice():
    check, _ = build_capability_check(F43, _f43_proposal())
    assert open_choice_groups(check.model_copy(update={"provisional": True})) == []
