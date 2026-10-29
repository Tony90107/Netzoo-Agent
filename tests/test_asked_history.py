"""asked-history-2026-10-29 (j8 Z22): a question a later round replaced unanswered is remembered -- never asked again
for Jev's own questions, still open for a data confirm (jev-guard review)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.contracts.task_state import TaskState, load_task_state  # noqa: E402
from netzoo_agent_core.engine.task_updates import after_turn  # noqa: E402
from netzoo_agent_core.graph.jev_guard_call import (  # noqa: E402
    asked_doubts, asked_sentences, condition_asked, confirmed_core, pending_condition)

WHICH = "I'm not sure which of those two files my supervisor wants me to use."
DATA = "Our values are raw counts."
LINE = "BONOBO requires log-transformed expression."


def _ask(*facts):
    return {"decision": {"core": {"kind": "ASK", "facts": list(facts)}}}


def _jev(what, quote, **more):
    return {"depends_on": what, "by_code": False, "question": "Which of the files do you have?", "user_quote": quote,
            "workflows": ["LIONESS-DRAGON"], **more}


AGENT = {"depends_on": "", "by_code": False, "question": "Is it the 800-protein panel?", "user_quote": WHICH,
         "workflows": ["LIONESS-DRAGON"], "contract_quote": ""}


def test_a_replaced_jev_question_counts_as_asked():
    """Z22: t1 jev:which_file, t2 the user restates and a fact-agent question replaces it, t3 -> already asked."""
    state = after_turn(None, _ask(_jev("jev:which_file", WHICH)), "task")
    state = after_turn(state, _ask(AGENT), "task")
    assert [q.what for q in state.asked] == ["jev:which_file"] and [q.source for q in state.pending] == ["agent"]
    dumped = state.model_dump()
    assert WHICH in asked_sentences(dumped) and WHICH in asked_doubts(dumped)
    state = after_turn(state, _ask(_jev("jev:which_file", WHICH)), "task")  # asked again only if something re-asks
    assert [q.what for q in state.asked] == ["LIONESS-DRAGON"]  # back in pending, it leaves `asked`; the agent joins


def test_an_answered_question_is_not_kept_as_asked_and_a_closed_task_starts_clean():
    state = after_turn(None, _ask(_jev("jev:which_file", WHICH)), "task")
    state = state.model_copy(update={"pending": []})  # bound this turn: the binder moved it to facts
    state = after_turn(state, _ask(AGENT), "task")
    assert state.asked == []
    closed = after_turn(state, {"decision": {"core": {"kind": "DO"}}}, "task")
    assert closed.status == "closed" and after_turn(closed, _ask(AGENT), "new").asked == []


def test_a_replaced_data_confirm_stays_open_and_is_asked_again():
    """jev-guard review (S35): t1 confirm asked, t2 restate replaced by a fact-agent ASK, t3 DO -> the confirm again."""
    confirm = _jev("jev:condition", DATA, contract_quote=LINE, question="Is your data raw counts? Yes or no.")
    state = after_turn(None, _ask(confirm), "task")
    state = after_turn(state, _ask(AGENT), "task")
    dumped = state.model_dump()
    waiting = pending_condition(dumped)
    assert waiting is not None and waiting["what"] == "jev:condition"
    assert not condition_asked(dumped) and DATA not in asked_sentences(dumped)
    after, action = confirmed_core(CoreDecision(kind="DO", basis="results_given", workflows=["BONOBO"], evidence={}),
                                   waiting, "Please just run it.", {"answer": "unread", "confidence": 0.0})
    assert action == "reask" and after.kind == "ASK" and after.facts[0].depends_on == "jev:condition"


def test_a_version_1_state_still_loads():
    old = TaskState(task_id="t").model_dump()
    old.pop("asked")
    old["version"] = 1
    assert load_task_state({"task_state": old}).asked == []


def test_a_re_asked_and_answered_confirm_is_not_found_again():
    """jev-guard review: replaced -> re-asked -> answered "no" -> a later round: `pending_condition` finds nothing."""
    from netzoo_agent_core.engine.task_updates import bind_answers

    confirm = _jev("jev:condition", DATA, contract_quote=LINE, question="Is your data raw counts? Yes or no.")
    state = after_turn(None, _ask(confirm), "task")
    state = after_turn(state, _ask(AGENT), "task")  # replaced
    state = after_turn(state, _ask(confirm), "task")  # the guard re-asks it
    assert state.asked[0].source == "agent" and pending_condition(state.model_dump())["what"] == "jev:condition"
    state, bound, _ = bind_answers(state, "No, they are not.")
    assert [fact.value for fact in bound] == ["no"]
    state = after_turn(state, _ask(AGENT), "task")  # the task stays open on another question
    assert pending_condition(state.model_dump()) is None
