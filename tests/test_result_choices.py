"""Verdict layer step 2b: a choice among results the user names but has not made waits for them.

Feasibility eval F43 ("I cannot tell if I mean their activity or their network wiring. Help me choose before planning
anything.") was refused (10-12) or answered with every regulatory workflow (10-13). Log 416's G0: a methods question
("should we use LIONESS or BONOBO?") must not become a result choice -- here the model types it, no string is matched.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import proposal_model, unstated_conditions  # noqa: E402
from netzoo_agent_core.graph.response import respond  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402
from netzoo_agent_core.interpretation.needed_facts import waiting_decision  # noqa: E402

F43 = ("Some regulators seem different between patients. I cannot tell if I mean their activity or their network "
       "wiring. Help me choose before planning anything.")
METHODS = "For per-sample co-expression networks of 50 samples, should we use LIONESS or BONOBO?"


def _ask(quote, delivered, **attrs):
    return {"quote": quote, "delivered_by": list(delivered), "not_by": [], "scale": "per_sample", "omics_layers": 0,
            "data_unit": "not_stated", "regulator_kinds": ["tf"], "needs_sign": False, "input_network": "none",
            "group_membership": "not_about_groups", "time_model": "not_dynamic", "spatial": "not_spatial",
            "asked_as": "request", **attrs}


def _check(task, quote, options, differs_in="result", asks=()):
    conditions = {**unstated_conditions(),
                  "open_choices": [{"quote": quote, "differs_in": differs_in, "options": list(options)}]}
    proposal = proposal_model(1).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": list(asks)}, "conditions": conditions})
    return build_capability_check(task, proposal)[0]


ACTIVITY = _ask("their activity", ["giraffe.tf_activity"])
WIRING = _ask("their network wiring", ["lioness_panda.per_sample_networks"])


def test_a_result_choice_whose_options_lead_to_different_workflows_waits():
    check = _check(F43, "I cannot tell if I mean their activity or their network wiring", [ACTIVITY, WIRING])
    (item,) = check.needed_facts()
    assert item.depends_on == "choice" and not check.full_gap
    assert item.outcomes == {"their activity": ["giraffe.tf_activity"],
                             "their network wiring": ["lioness_panda.per_sample_networks"]}
    reply = respond(None, {"decision": waiting_decision(TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r"), check).model_dump(),
        "messages": []})
    text = reply["messages"][-1].content
    assert ('"I cannot tell if I mean their activity or their network wiring" -- you have not chosen which result you '
            'want: if "their activity": GIRAFFE; if "their network wiring": LIONESS-PANDA.') in text
    assert 'Before I choose a workflow, please tell me: Which result do you want: "their activity" or "their network ' \
           'wiring"?' in text


def test_a_methods_choice_is_left_to_routing():
    """Log 416 G0: "LIONESS or BONOBO?" -- the same result by two methods is a tie, not a result choice."""
    check = _check(METHODS, "should we use LIONESS or BONOBO?", [
        _ask("LIONESS", ["lioness_coexpression.per_sample_networks"], regulator_kinds=[]),
        _ask("BONOBO", ["bonobo.per_sample_networks"], regulator_kinds=[])], differs_in="method")
    assert check.needed_facts() == []


def test_options_leading_to_the_same_workflows_decide_nothing():
    same = _ask("their network wiring", ["giraffe.tf_activity"])
    assert _check(F43, "I cannot tell if I mean their activity or their network wiring", [ACTIVITY, same]) \
        .needed_facts() == []


def test_an_option_also_read_as_an_ask_is_listed_once_as_part_of_the_choice():
    check = _check(F43, "I cannot tell if I mean their activity or their network wiring", [ACTIVITY, WIRING],
                   asks=[ACTIVITY])
    assert [item.quote for item in check.results()] == [
        "I cannot tell if I mean their activity or their network wiring"]


def test_words_that_state_a_result_choice_are_not_also_an_unknown_fact():
    """Pre-measure F37: the choice's own sentence was also read as an unknown omics-layer count."""
    task = ("I want a network for each sample, but I have not decided whether edges should mean TF regulation or "
            "gene-gene coexpression.")
    said = "I have not decided whether edges should mean TF regulation or gene-gene coexpression"
    conditions = {**unstated_conditions(),
                  "unknown_facts": [{"quote": said, "about": "omics_layers"}],
                  "open_choices": [{"quote": said, "differs_in": "result", "options": [
                      _ask("TF regulation", ["lioness_panda.per_sample_networks"]),
                      _ask("gene-gene coexpression", ["bonobo.per_sample_networks"], regulator_kinds=[])]}]}
    proposal = proposal_model(1).model_validate({"s1": {"role": "asks", "has": [], "about_methods": [], "asks": [
        _ask("I want a network for each sample", ["lioness_panda.per_sample_networks",
                                                  "lioness_dragon.per_sample_networks"])]},
        "conditions": conditions})
    check = build_capability_check(task, proposal)[0]
    assert [item.depends_on for item in check.needed_facts()] == ["choice"]
