"""jev-answers-2026-10-27 (ROUND.md): natural answers to form questions read by Jev and bound in code; one question
per doubted form."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from netzoo_agent_core.contracts.task_state import TaskState  # noqa: E402
from netzoo_agent_core.interpretation.jev_forms import answer_value, bind_form_answers  # noqa: E402

PLAIN = {"scale": "unstated", "omics_layers": 0, "data_unit": "not_stated", "regulator_kinds": [],
         "needs_sign": False, "input_network": "none", "group_membership": "not_about_groups",
         "time_model": "not_dynamic", "spatial": "not_spatial", "asked_as": "request"}
TASK = ("Please run SAMBAR on our tumors to get subtypes, trying 2 to 4 clusters. "
        "I also want SAMBAR subtypes for the validation tumors.")
FIRST = "Please run SAMBAR on our tumors to get subtypes, trying 2 to 4 clusters."
SECOND = "I also want SAMBAR subtypes for the validation tumors."


def _proposal(*quotes):
    from netzoo_agent_core.contracts.capability_check import proposal_model

    return proposal_model(1).model_validate({"s1": {"role": "asks", "has": [], "about_methods": [], "asks": [
        {**PLAIN, "quote": quote, "delivered_by": ["sambar.subtypes"], "not_by": [], "group_membership": "several_groups"}
        for quote in quotes]}})


def _check():
    from netzoo_agent_core.interpretation.capability_check import build_capability_check

    check, _ = build_capability_check(TASK, _proposal(FIRST, SECOND), overlap_reader=lambda task, quote: True)
    return check


def _pending(check):
    from netzoo_agent_core.engine.task_updates import _pending
    from netzoo_agent_core.interpretation.core_decision import _facts

    facts = _facts(check, task=TASK)
    return facts, _pending({"kind": "ASK", "facts": [fact.model_dump() for fact in facts]})


def test_answer_value_needs_bind_probability_on_one_value():
    assert answer_value("group_membership", {"probabilities": {"one_each": 0.99}}) == "one_group"
    assert answer_value("input_network", {"probabilities": {"other": 0.83, "gene_gene": 0.16}}) is None
    assert answer_value("time_model", {"probabilities": {"not_stated": 1.0}}) is None
    assert answer_value("spatial", {"error": "down"}) is None


def test_two_rows_waiting_on_the_same_doubted_form_are_one_question():
    """j4 S32: the group question was listed twice, once per quote."""
    check = _check()
    assert [row.depends_on for row in check.needed_facts()] == ["group_membership", "group_membership"]
    facts, pending = _pending(check)
    assert len(facts) == 1 and len(pending) == 1


def test_a_natural_answer_binds_through_the_reader_and_settles_every_waiting_row():
    from netzoo_agent_core.engine.task_updates import bind_answers
    from netzoo_agent_core.interpretation.task_answers import answered_check

    check = _check()
    _facts, pending = _pending(check)
    state = TaskState.model_validate({"task_id": "t", "goal": TASK, "pending": [q.model_dump() for q in pending]})
    reply = "Each tumour should land in a single subtype, never two."
    state, bound, _ = bind_answers(state, reply)
    assert bound == []  # natural words name no option: code binds nothing
    calls = []
    state, read = bind_form_answers(state, reply, lambda dim, question, answer: calls.append(dim) or "one_group")
    assert calls == ["group_membership"] and [fact.value for fact in read] == ["one_group"]
    assert state.pending == [] and read[0].answer_quote == reply
    settled = answered_check(check, state)
    assert [row.status for row in settled.results()] == ["available", "available"]


def test_a_reader_value_outside_the_options_or_none_binds_nothing():
    check = _check()
    _facts, pending = _pending(check)
    state = TaskState.model_validate({"task_id": "t", "goal": TASK, "pending": [q.model_dump() for q in pending]})
    for value in (None, "not_stated", "regulator_gene"):
        after, read = bind_form_answers(state, "Hmm.", lambda dim, question, answer, v=value: v)
        assert read == [] and after is state


def test_code_binding_goes_first_and_the_reader_never_sees_a_bound_question():
    from netzoo_agent_core.engine.task_updates import bind_answers

    check = _check()
    _facts, pending = _pending(check)
    state = TaskState.model_validate({"task_id": "t", "goal": TASK, "pending": [q.model_dump() for q in pending]})
    state, bound, _ = bind_answers(state, "One group each.")
    assert [fact.value for fact in bound] == ["one_group"]
    after, read = bind_form_answers(state, "One group each.", lambda *args: (_ for _ in ()).throw(AssertionError))
    assert read == []
