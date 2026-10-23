"""Harness repair P3 (ROUND-P3.md, spec A11-A15): a task's questions, answers and rounds across turns and resumes.

Each test drives the real `ConversationMachine` through `save_session` and `cli.bootstrap.resumed_session`, as a
one-shot `--task` and a later `--resume S --task ...` do. The graph turn is a script of results (no model runs); what
the graph does with the task state is covered in test_clarification_budget.py.
"""

from __future__ import annotations

import importlib
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core import session as session_module  # noqa: E402
from netzoo_agent_core.cli.reply_resolution import ReplyResolutionResult  # noqa: E402
from netzoo_agent_core.contracts import (  # noqa: E402
    AIMessage, ContextualReplyResolution, LLMUsage, TaskDecision, WorkflowPlan,
)
from netzoo_agent_core.contracts.core_decision import CoreDecision, FactQuestion  # noqa: E402
from netzoo_agent_core.engine.machine import ConversationMachine, Turn  # noqa: E402
from netzoo_agent_core.interpretation.core_decision import with_core  # noqa: E402

GOAL = ("Run SAMBAR on brca_variant_matrix.csv for our 80 tumours. I can't tell whether those are somatic calls or "
        "germline variants.")
UNSURE = "I can't tell whether those are somatic calls or germline variants"
SID = "0a1b2c3d"  # an auto-generated id: a one-shot run deletes it unless it waits on its user


@pytest.fixture(autouse=True)
def sessions(tmp_path, monkeypatch):
    monkeypatch.setattr(session_module, "SESSION_ROOT", tmp_path / "sessions")
    return tmp_path / "sessions"


def _origin(**extra) -> FactQuestion:
    return FactQuestion(question="Are these acquired somatic mutations, or inherited germline variants?",
                        user_quote=UNSURE, depends_on="mutation_origin", workflows=["SAMBAR"],
                        outcomes={"somatic": ["SAMBAR"], "germline": []}, **extra)


def _agent(question: str, quote: str) -> FactQuestion:
    return FactQuestion(question=question, user_quote=quote, workflows=["SAMBAR"],
                        contract_quote="SAMBAR consumes a samples-by-genes somatic mutation CSV")


def _result(invocation: dict, kind: str, *facts: FactQuestion, reply: str = "reply") -> dict:
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                            matched_actions=["run_sambar"])
    basis = {"ASK": "needs_fact", "DO": "results_given", "DECLINE": "full_gap"}[kind]
    decision = with_core(decision, CoreDecision(kind=kind, basis=basis, facts=list(facts), workflows=["SAMBAR"]))
    plan = WorkflowPlan(workflow="NO-TOOL", objective="o", decision=decision.model_dump(), status="respond_only")
    return {"messages": [*invocation["messages"], AIMessage(content=reply)], "decision": decision.model_dump(),
            "plan": plan.model_dump(), "tool_results": [], "evaluation": None, "token_usage": None}


class Graph:
    """The graph turn as a script: each call returns the next result and keeps the invocation it got."""

    def __init__(self, *steps):
        self.steps, self.invocations = list(steps), []

    def __call__(self, _app, invocation):
        self.invocations.append(invocation)
        return self.steps.pop(0)(invocation)


def _resolver(kind="follow_up"):
    resolver = Mock()
    resolver.resolve.side_effect = lambda context, answer, *_rest: ReplyResolutionResult(
        ContextualReplyResolution(kind=kind, reason="r", resolved_task=(
            f"Previous NetZoo goal: {context.prior_user_goal}\nUser follow-up: {answer}"
            if kind in ("follow_up", "new_goal") else None)), LLMUsage(budget_tokens=1000))
    return resolver


def _runtime(graph, *, resume=False, resolver=None):
    bootstrap = importlib.import_module("netzoo_agent_core.cli.bootstrap")
    saved = bootstrap.resumed_session(SID) if resume else None
    recorder = Mock()
    recorder.start_run.return_value = "run"
    return bootstrap.CliRuntime(
        memory=SimpleNamespace(profile_id="p", profile_store=Mock(), episode_store=Mock()),
        project_policy=Mock(), session_id=SID, resume_id=SID if resume else None,
        conversation=saved.conversation if saved else [], pending_plan=saved.pending_plan if saved else None,
        active_usage=None, run_id=None, recorder=recorder, trace_store=Mock(),
        ensure_trace_sync=lambda _run_id: None, app=object(), input_func=Mock(), invoke_graph_turn_func=graph,
        reply_resolver=resolver or _resolver(), resumed_turn=saved.resumed_turn if saved else None,
        task_state=saved.task_state if saved else None)


def _turn(task: str, graph, *, resume=False, resolver=None):
    """One CLI invocation: `--task` (one-shot), or `--resume S --task` -- its first action, run to the end."""
    machine = ConversationMachine(SimpleNamespace(task=task, keep_session=False),
                                  _runtime(graph, resume=resume, resolver=resolver))
    action = machine.next_action()
    if isinstance(action, Turn):
        machine.run_turn()
    return machine, action


def _payload(sessions) -> dict:
    return json.loads((sessions / f"{SID}.json").read_text())


def test_an_asked_question_keeps_the_session_and_its_answer_reaches_the_next_turn(sessions):
    """A13 (resumable) and A11 (one answer bound): the ASK turn's session is kept, found by --resume latest."""
    graph = Graph(lambda inv: _result(inv, "ASK", _origin()), lambda inv: _result(inv, "DO"))
    _turn(GOAL, graph)
    task = _payload(sessions)["task_state"]
    assert (task["rounds"], task["status"], [q["what"] for q in task["pending"]]) == (1, "active", ["mutation_origin"])
    assert session_module.latest_pending_session_id("p") == SID

    machine, action = _turn("They are somatic calls from tumour versus matched normal.", graph, resume=True)
    assert isinstance(action, Turn) and action.task.startswith("Previous NetZoo goal: ")
    sent = graph.invocations[1]["task_state"]
    assert [(fact["what"], fact["value"], fact["status"]) for fact in sent["facts"]] == [
        ("mutation_origin", "somatic", "known")]
    assert sent["pending"] == [] and sent["rounds"] == 1
    assert _payload(sessions)["task_state"]["status"] == "closed"  # the DO closed the task


def test_an_answer_with_a_volunteered_condition_binds_the_answer_and_still_reads_the_condition():
    """A11: the code binds only the option; the new condition reaches the next reading in the user's words."""
    graph = Graph(lambda inv: _result(inv, "ASK", _origin()), lambda inv: _result(inv, "DO"))
    _turn(GOAL, graph)
    reply = "Somatic. Also keep only the 50 primary tumours."
    _machine, action = _turn(reply, graph, resume=True)
    assert action.task.endswith(f"User follow-up: {reply}")
    assert [(f["value"], f["answer_quote"]) for f in graph.invocations[1]["task_state"]["facts"]] == [("somatic", reply)]


def test_two_open_questions_and_a_bare_yes_bind_neither():
    """Spec 7.2 / A11: after two questions a bare "yes" fills no field; the next reading reads it."""
    graph = Graph(lambda inv: _result(inv, "ASK", _agent("Are the calls somatic?", "somatic calls"),
                                      _agent("Are all 80 tumours in the matrix?", "80 tumours")),
                  lambda inv: _result(inv, "ASK", _origin()))
    _turn(GOAL, graph)
    machine, _action = _turn("yes", graph, resume=True)
    assert graph.invocations[1]["task_state"]["facts"] == []
    assert len(graph.invocations[1]["task_state"]["pending"]) == 2


def test_one_open_yes_no_question_takes_a_short_yes_that_would_otherwise_be_too_vague():
    graph = Graph(lambda inv: _result(inv, "ASK", _agent("Are the calls somatic?", "somatic calls")),
                  lambda inv: _result(inv, "DO"))
    _turn(GOAL, graph)
    machine, action = _turn("yes", graph, resume=True, resolver=_resolver("needs_detail"))
    assert isinstance(action, Turn)  # not re-prompted for a "concrete follow-up"
    [fact] = graph.invocations[1]["task_state"]["facts"]
    assert (fact["source"], fact["value"]) == ("agent", "yes")


def test_a_corrected_answer_supersedes_the_earlier_one_and_voids_the_preview(sessions):
    """A12: a correction replaces the fact it corrects, keeps the earlier one as superseded, and voids the preview."""
    graph = Graph(lambda inv: _result(inv, "ASK", _origin()),
                  lambda inv: _result(inv, "ASK", _agent("Are all 80 tumours in the matrix?", "80 tumours")),
                  lambda inv: _result(inv, "ASK", _agent("Are all 80 tumours in the matrix?", "80 tumours")))
    _turn(GOAL, graph)
    _turn("somatic", graph, resume=True)
    machine = ConversationMachine(SimpleNamespace(task="Sorry, they are germline variants.", keep_session=False),
                                  _runtime(graph, resume=True))
    machine.state.preview = object()
    machine.next_action()
    facts = machine.state.task_state.facts
    assert [(fact.value, fact.status) for fact in facts] == [("somatic", "superseded"), ("germline", "known")]
    assert machine.state.preview is None and machine.state.pending_plan is None


def test_a_new_goal_closes_the_task_and_carries_nothing_over():
    """A12: a new request starts a new task; the old one's answers are not carried into it."""
    graph = Graph(lambda inv: _result(inv, "ASK", _origin()), lambda inv: _result(inv, "ASK", _origin()))
    _turn(GOAL, graph)
    first = ConversationMachine(SimpleNamespace(task=GOAL, keep_session=False), _runtime(Graph(), resume=True))
    old = first.state.task_state.task_id
    machine, _action = _turn("Different study: run PANDA on liver.tsv with somatic data.", graph, resume=True,
                             resolver=_resolver("new_goal"))
    assert graph.invocations[1]["task_state"] is None
    assert machine.state.task_state.task_id != old and machine.state.task_state.facts == []


def test_rounds_survive_resumes_and_reach_the_third_turn(sessions):
    """A13: two ASK turns, each in its own process; the third sees two rounds (it is not asked: see the budget tests)."""
    graph = Graph(*[lambda inv: _result(inv, "ASK", _origin())] * 3)
    _turn(GOAL, graph)
    _turn("I really am not sure.", graph, resume=True)
    _turn("Still not sure, the README says nothing.", graph, resume=True)
    assert [inv["task_state"] and inv["task_state"]["rounds"] for inv in graph.invocations] == [None, 1, 2]
    assert _payload(sessions)["task_state"]["rounds"] == 3


def test_compaction_never_drops_the_tasks_facts(sessions):
    """A14: past 12 messages the oldest are dropped, the task's answers are not."""
    graph = Graph(lambda inv: _result(inv, "ASK", _origin(), reply="x" * 3000),
                  *[lambda inv: _result(inv, "ASK", _agent("Are all 80 tumours in the matrix?", "80 tumours"),
                                        reply="y" * 3000)] * 7)
    _turn(GOAL, graph)
    _turn("somatic", graph, resume=True)
    for index in range(6):
        _turn(f"More detail number {index}.", graph, resume=True)
    payload = _payload(sessions)
    assert GOAL not in [message["content"] for message in payload["messages"]]  # compacted away
    assert [(f["what"], f["value"]) for f in payload["task_state"]["facts"]] == [("mutation_origin", "somatic")]


@pytest.mark.parametrize("task_state,message", [
    ({"version": 99, "task_id": "t"}, "newer NetZoo (version 99)"),
    ({"task_id": "t"}, "damaged (no version)"),
    ({"version": 1, "task_id": "t", "rounds": "many"}, "damaged"),
])
def test_a_newer_or_damaged_task_state_is_never_resumed_as_none(sessions, task_state, message):
    """A15: refused with the reason, the file left as saved."""
    graph = Graph(lambda inv: _result(inv, "ASK", _origin()))
    _turn(GOAL, graph)
    payload = _payload(sessions)
    payload["task_state"] = task_state
    (sessions / f"{SID}.json").write_text(json.dumps(payload))
    bootstrap = importlib.import_module("netzoo_agent_core.cli.bootstrap")
    with pytest.raises(SystemExit, match=re.escape(message)):
        bootstrap.resumed_session(SID)
    assert _payload(sessions)["task_state"] == task_state


def test_a_session_saved_before_p3_resumes_without_a_task_and_revives_no_approval(sessions):
    """A15: no task state is made up from the reply text; a finished plan never becomes a pending one."""
    graph = Graph(lambda inv: _result(inv, "DO"))
    _turn(GOAL, graph)  # a DO turn closes nothing and opens no task: the one-shot session is removed
    assert not (sessions / f"{SID}.json").exists()
    decision = TaskDecision(action="run_panda", in_scope=True, should_execute=True, confidence=0.9, reason="r")
    session_module.save_session(SID, [AIMessage(content="old")], {"plan": WorkflowPlan(
        workflow="PANDA", objective="o", decision=decision.model_dump(), status="respond_only").model_dump()},
        profile_id="p")
    payload = _payload(sessions)
    payload.pop("task_state")
    (sessions / f"{SID}.json").write_text(json.dumps(payload))
    saved = importlib.import_module("netzoo_agent_core.cli.bootstrap").resumed_session(SID)
    assert saved.task_state is None and saved.pending_plan is None
