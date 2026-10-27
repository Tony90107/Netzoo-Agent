"""jev-overlap-2026-10-27 (ROUND.md): Jev's second read of a result typed several_groups."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from netzoo_agent_core.interpretation import jev_overlap as jev_overlap_call  # noqa: E402

PLAIN = {"scale": "unstated", "omics_layers": 0, "data_unit": "not_stated", "regulator_kinds": [],
         "needs_sign": False, "input_network": "none", "group_membership": "not_about_groups",
         "time_model": "not_dynamic", "spatial": "not_spatial", "asked_as": "request"}
SUBTYPES = ("Please run SAMBAR on our 150 lung adenocarcinoma tumors to get pathway mutation scores and subtypes, "
            "trying 2 to 5 clusters.")
FUZZY = "We want a fuzzy community structure in which every gene has a degree of membership in each community."


def _proposal(quote, delivered, **attrs):
    from netzoo_agent_core.contracts.capability_check import proposal_model

    return proposal_model(1).model_validate({"s1": {
        "role": "asks", "has": [], "about_methods": [],
        "asks": [{**PLAIN, "quote": quote, "delivered_by": list(delivered), "not_by": [], **attrs}]}})


@pytest.fixture
def jev(monkeypatch):
    """Jev's read, set per test; every call is counted."""
    calls = []

    def read(task, quote):
        calls.append(quote)
        if "fuzzy" in task:
            return {"choice": "overlapping", "confidence": 1.0,
                    "probabilities": {"overlapping": 1.0, "one_each": 0.0, "not_stated": 0.0}}
        return {"choice": "not_stated", "confidence": 0.97,
                "probabilities": {"overlapping": 0.0, "one_each": 0.03, "not_stated": 0.97}}

    monkeypatch.setattr(jev_overlap_call, "_read", read)
    jev_overlap_call._READS.clear()
    return calls


def _check(task, quote, delivered):
    from netzoo_agent_core.interpretation.capability_check import build_capability_check

    check, _ = build_capability_check(task, _proposal(quote, delivered, group_membership="several_groups"))
    return check.results()[0]


def test_off_by_default_the_overlap_form_refuses_and_jev_is_never_called(jev, monkeypatch):
    monkeypatch.delenv("NETZOO_JEV_OVERLAP", raising=False)
    row = _check(SUBTYPES, SUBTYPES, ("sambar.subtypes",))
    assert row.status == "not_available" and jev == []


def test_shadow_records_the_read_and_changes_nothing(jev, monkeypatch):
    monkeypatch.setenv("NETZOO_JEV_OVERLAP", "shadow")
    row = _check(SUBTYPES, SUBTYPES, ("sambar.subtypes",))
    assert row.status == "not_available" and len(jev) == 1
    [read] = jev_overlap_call.take_reads(SUBTYPES)
    assert read["doubted"] and not read["applied"]


def test_on_a_subtyping_request_waits_on_the_group_membership_question(jev, monkeypatch):
    from netzoo_agent_core.interpretation.needed_facts import fact_line, fact_questions

    monkeypatch.setenv("NETZOO_JEV_OVERLAP", "on")
    row = _check(SUBTYPES, SUBTYPES, ("sambar.subtypes",))
    assert row.status == "needs_fact" and row.depends_on == "group_membership"
    assert row.outcomes == {"one_group": ["sambar.subtypes"], "several_groups": []}
    assert "overlapping memberships" not in " ".join(row.limits)
    line = fact_line(row)
    assert "you said you do not know" not in line and "one group each: SAMBAR" in line


def test_on_a_real_overlap_request_keeps_its_refusal(jev, monkeypatch):
    monkeypatch.setenv("NETZOO_JEV_OVERLAP", "on")
    quote = "a fuzzy community structure in which every gene has a degree of membership in each community"
    row = _check(FUZZY, quote, ("condor.communities",))
    assert row.status == "not_available" and len(jev) == 1


def test_jev_failing_leaves_the_refusal(monkeypatch):
    def down(task, quote):
        raise TimeoutError("jev down")

    monkeypatch.setattr(jev_overlap_call, "_read", down)
    monkeypatch.setenv("NETZOO_JEV_OVERLAP", "on")
    row = _check(SUBTYPES, SUBTYPES, ("sambar.subtypes",))
    assert row.status == "not_available"
    assert "error" in jev_overlap_call.take_reads(SUBTYPES)[0]["read"]


def test_a_reply_naming_an_option_binds_in_code_and_settles_the_row_next_turn(jev, monkeypatch):
    from netzoo_agent_core.contracts.task_state import TaskState
    from netzoo_agent_core.engine.task_updates import _pending, bind_answers
    from netzoo_agent_core.interpretation.core_decision import _facts
    from netzoo_agent_core.interpretation.task_answers import answered_check
    from netzoo_agent_core.interpretation.capability_check import build_capability_check

    monkeypatch.setenv("NETZOO_JEV_OVERLAP", "on")
    check, _ = build_capability_check(SUBTYPES, _proposal(SUBTYPES, ("sambar.subtypes",),
                                                          group_membership="several_groups"))
    [fact] = _facts(check, task=SUBTYPES)
    [pending] = _pending({"kind": "ASK", "facts": [fact.model_dump()]})
    assert pending.source == "dimension" and set(pending.options) == {"one_group", "several_groups"}
    state = TaskState.model_validate({"task_id": "t", "goal": SUBTYPES, "pending": [pending.model_dump()]})
    state, bound, _ = bind_answers(state, "One group each, please.")
    assert [item.value for item in bound] == ["one_group"]
    state = state.model_copy(update={"facts": bound})
    settled = answered_check(check, state).results()[0]
    assert settled.status == "available" and settled.delivered_by == ["sambar.subtypes"]
