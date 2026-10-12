"""Log 410: a resumed session's first message answers the session's last turn.

`--resume S --task ...` and a session reopened in the desktop app started from the main prompt with no
follow-up context, so the message was routed and checked alone (heldout15 KN1: "Those samples are 50
spatial spots from one tissue section, and neighbouring spots should share information." was matched
to SAMBAR). The interactive loop resolves the same message against the turn it follows.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.cli.reply_resolution import ReplyResolutionResult  # noqa: E402
from netzoo_agent_core.contracts import (  # noqa: E402
    AIMessage, ContextualReplyResolution, HumanMessage, LLMUsage, TaskDecision, WorkflowPlan,
)
from netzoo_agent_core.engine.machine import ConversationMachine, Turn  # noqa: E402

GOAL = "We want per-sample TF-gene networks from expression, motifs and PPI of 50 samples."
REPLY = "Those samples are 50 spatial spots from one tissue section, and neighbouring spots should share information."


def _saved_turn() -> dict:
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                            capability_match_status="exact", matched_actions=["run_lioness_panda"],
                            recommended_actions=["run_lioness_panda"])
    plan = WorkflowPlan(workflow="NO-TOOL", objective=GOAL, decision=decision.model_dump(), status="respond_only")
    return {"plan": plan.model_dump(), "tool_results": [], "evaluation": None}


def _runtime(*, resumed_turn, resolver):
    bootstrap = importlib.import_module("netzoo_agent_core.cli.bootstrap")
    recorder = Mock()
    recorder.start_run.return_value = "run-2"
    return bootstrap.CliRuntime(
        memory=SimpleNamespace(profile_id="p", profile_store=Mock(), episode_store=Mock()),
        project_policy=Mock(), session_id="s", resume_id="s",
        conversation=[HumanMessage(content=GOAL), AIMessage(content="Use LIONESS-PANDA.")],
        pending_plan=None, active_usage=None, run_id="run-2", recorder=recorder, trace_store=Mock(),
        ensure_trace_sync=lambda _run_id: None, app=object(), input_func=Mock(), invoke_graph_turn_func=Mock(),
        reply_resolver=resolver, resumed_turn=resumed_turn,
    )


def _resolver(kind="follow_up"):
    resolver = Mock()
    resolver.resolve.return_value = ReplyResolutionResult(
        ContextualReplyResolution(kind=kind, reason="r", resolved_task=(
            f"Previous NetZoo goal: {GOAL}\nUser follow-up: {REPLY}" if kind == "follow_up" else None)),
        LLMUsage(budget_tokens=1000))
    return resolver


def test_the_resumed_task_is_resolved_against_the_saved_turn():
    resolver = _resolver()
    machine = ConversationMachine(SimpleNamespace(task=REPLY), _runtime(resumed_turn=_saved_turn(), resolver=resolver))

    assert machine.state.follow_up_context.prior_user_goal == GOAL
    assert machine.state.follow_up_context.candidate_actions == ["run_lioness_panda"]
    action = machine.next_action()

    assert isinstance(action, Turn)
    assert action.task == f"Previous NetZoo goal: {GOAL}\nUser follow-up: {REPLY}"
    assert resolver.resolve.call_args.args[1] == REPLY


def test_a_resumed_reply_that_needs_detail_asks_for_it_instead_of_running_alone():
    machine = ConversationMachine(SimpleNamespace(task="ok"), _runtime(resumed_turn=_saved_turn(),
                                                                      resolver=_resolver("needs_detail")))
    action = machine.next_action()
    assert not isinstance(action, Turn) and "concrete follow-up" in action.text


def test_without_a_saved_turn_the_task_runs_as_a_new_request():
    resolver = _resolver()
    machine = ConversationMachine(SimpleNamespace(task=REPLY), _runtime(resumed_turn=None, resolver=resolver))
    action = machine.next_action()
    assert isinstance(action, Turn) and action.task == REPLY
    resolver.resolve.assert_not_called()


def test_an_unreadable_saved_turn_starts_from_the_main_prompt():
    machine = ConversationMachine(SimpleNamespace(task=None), _runtime(resumed_turn={"plan": {"bad": 1}},
                                                                      resolver=_resolver()))
    assert machine.state.follow_up_context is None and machine.state.next_prompt.kind == "initial"
