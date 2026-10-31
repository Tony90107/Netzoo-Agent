"""count-answers-2026-10-31: a bound "No" to an agent question naming a workflow's sample minimum rules out the
workflows whose own minimum the count fails; "Yes", another number, an unbound reply, a non-DO and the flag off change
nothing; shadow records only."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.graph import context as graph_context  # noqa: E402
from netzoo_agent_core.graph import count_answer_call as call  # noqa: E402
from netzoo_agent_core.interpretation.core_views import decline_reply  # noqa: E402

CONTRACT = "Require at least three samples and validate expression inside the execution wrapper."


def _state(value="no", question="Will you have at least three usable biopsies?", turn=1, turns=1):
    return {"task_state": {"turns": turns, "facts": [{
        "question_id": "agent:LIONESS-COEXPRESSION:x", "source": "agent", "what": "LIONESS-COEXPRESSION",
        "question": question, "user_quote": "five usable biopsies or only two", "value": value, "answer_quote": "No",
        "labels": {"contract": CONTRACT, "workflow": "LIONESS-COEXPRESSION"}, "turn": turn, "status": "known"}]}}


DO = CoreDecision(kind="DO", basis="results_given", workflows=["LIONESS-COEXPRESSION", "BONOBO"])


def test_scope():
    found = call.answered_count_question(_state()["task_state"])
    assert found["workflow"] == "LIONESS-COEXPRESSION" and found["minimum"] == 3
    assert call.answered_count_question(_state(question="Do you have at least 3 samples?")["task_state"])
    assert call.answered_count_question(_state(question="Do you have at least 12 tumours?")["task_state"]) is None
    assert call.answered_count_question(_state(turn=0)["task_state"]) is None  # not answered this turn
    assert call.answered_count_question(_state(value="unclear")["task_state"]) is None


def test_no_declines_with_the_contract_line():
    after, action = call.counted_core(DO, call.answered_count_question(_state()["task_state"]))
    assert action == "declined" and after.kind == "DECLINE" and after.basis == "count_answer"
    line = after.declined[0].line
    assert "Require at least three samples" in line and "Will you have at least three usable biopsies?" in line
    assert after.evidence["count_answer"]["ruled_out"] == ["LIONESS-COEXPRESSION", "BONOBO"]
    assert "No registered workflow" not in decline_reply(after)


def test_a_workflow_with_a_lower_minimum_stays():
    mixed = DO.model_copy(update={"workflows": ["LIONESS-COEXPRESSION", "COBRA"]})  # COBRA's minimum is 2
    after, action = call.counted_core(mixed, call.answered_count_question(_state()["task_state"]))
    assert action == "narrowed" and after.kind == "DO" and after.workflows == ["COBRA"]


def test_yes_and_non_do_change_nothing():
    question = call.answered_count_question(_state(value="yes")["task_state"])
    assert call.counted_core(DO, question) == (DO, "answer_yes")
    ask = CoreDecision(kind="ASK", basis="fact_agent")
    assert call.counted_core(ask, call.answered_count_question(_state()["task_state"])) == (ask, "not_do")


@pytest.fixture
def events(monkeypatch):
    found = []
    monkeypatch.setattr(graph_context, "record_event", lambda c, s, name, node, payload: found.append((name, payload)))
    return found


def test_modes(events, monkeypatch):
    monkeypatch.delenv("NETZOO_COUNT_ANSWERS", raising=False)
    assert call.apply_count_answer(None, _state(), DO, "task") is DO and events == []
    monkeypatch.setenv("NETZOO_COUNT_ANSWERS", "shadow")
    assert call.apply_count_answer(None, _state(), DO, "task") is DO
    assert events[-1][1]["would_have"]["kind"] == "DECLINE"
    monkeypatch.setenv("NETZOO_COUNT_ANSWERS", "on")
    assert call.apply_count_answer(None, _state(), DO, "task").kind == "DECLINE"
