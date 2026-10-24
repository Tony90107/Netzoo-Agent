"""Harness repair P5 round 1 fixes (ROUND-P5.md, user decision 2026-10-24): three defects h7 found live.

(1) M11: a new request while a no-run plan waited crashed `_recheck` (WorkflowContinuation takes run actions only).
(2) M01: a correction to a waiting run was checked under the paused turn's usage, the check was budget-blocked, and the
    run was held unconfirmed instead of decided again.
(3) S04: "GIRAFFE does not give it: ..." -- a near miss the model's reading chose, said as if code had verified it.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core import session as session_module  # noqa: E402
from netzoo_agent_core.contracts import AIMessage, TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement  # noqa: E402
from netzoo_agent_core.engine.machine import ConversationMachine, Turn  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import understanding_paragraph  # noqa: E402
from netzoo_agent_core.interpretation.stated_reasons import stated  # noqa: E402

PAUSED_USAGE = {"input_tokens": 40000, "output_tokens": 2638, "total_tokens": 42638, "budget_tokens": 60000,
                "budget_exhausted": False, "calls": []}


@pytest.fixture(autouse=True)
def sessions(tmp_path, monkeypatch):
    monkeypatch.setattr(session_module, "SESSION_ROOT", tmp_path / "sessions")


def _waiting(action: str) -> WorkflowPlan:
    decision = TaskDecision(action=action, in_scope=True, should_execute=action != "no_tool", confidence=0.9,
                            reason="r")
    return WorkflowPlan(workflow="LIONESS-DRAGON" if action != "no_tool" else "NO-TOOL", objective="o",
                        decision=decision.model_dump(), status="needs_input", missing_inputs=["omics_layer_1"])


def _machine(plan: WorkflowPlan, message: str, graph=None):
    import importlib

    bootstrap = importlib.import_module("netzoo_agent_core.cli.bootstrap")
    recorder = Mock()
    recorder.start_run.return_value = "run"
    runtime = bootstrap.CliRuntime(
        memory=SimpleNamespace(profile_id="p", profile_store=Mock(), episode_store=Mock()), project_policy=Mock(),
        session_id="0a1b2c3d", resume_id="0a1b2c3d", conversation=[AIMessage(content="Which export did she send?")],
        pending_plan=plan, active_usage=dict(PAUSED_USAGE), run_id="run", recorder=recorder, trace_store=Mock(),
        ensure_trace_sync=lambda _run_id: None, app=object(), input_func=Mock(), invoke_graph_turn_func=graph or Mock(),
        reply_resolver=Mock())
    return ConversationMachine(SimpleNamespace(task=message, keep_session=True), runtime)


def test_a_new_request_while_a_no_run_plan_waits_is_a_new_turn_not_a_crash():
    """M11 on A, D and E: pydantic rejected `no_tool` as a continuation action."""
    message = "Forget that. Build one DRAGON network from our transcript and protein tables of 30 mice."
    machine = _machine(_waiting("no_tool"), message)
    action = machine.next_action()
    assert isinstance(action, Turn) and action.task == message
    assert machine.state.pending_continuation is None and machine.state.active_usage is None


def test_a_correction_to_a_waiting_run_is_checked_again_with_its_own_budget():
    """M01 on D and E: the re-check inherited the paused turn's 42,638 tokens and its capability check was blocked."""
    invocations = []

    def graph(_app, invocation):
        invocations.append(invocation)
        raise RuntimeError("stop after the invocation is built")

    machine = _machine(_waiting("run_lioness_dragon"), "Sorry, I checked again: she sent the full export.", graph)
    action = machine.next_action()
    assert isinstance(action, Turn)
    assert machine.state.pending_continuation.recheck and machine.state.pending_continuation.action == "run_lioness_dragon"
    assert machine.state.active_usage is None
    machine.run_turn()  # the graph's error is the machine's to report; only the invocation it got matters here
    assert invocations and "token_usage" not in invocations[0]


def test_an_input_wizard_answer_still_continues_the_paused_budget():
    machine = _machine(_waiting("run_lioness_dragon"), "omics_layer_1=data/rna.tsv")
    machine.next_action()
    assert machine.state.active_usage == PAUSED_USAGE and machine.state.pending_continuation.recheck is False


def _near_miss_row():
    return CheckedRequirement(quote="together with signed activating or repressing effects on its targets",
                              kind="result", status="not_available", not_by=["giraffe.no_protein_level"])


def test_a_near_miss_the_reading_chose_is_never_said_as_a_reason():
    """S04 on E: GIRAFFE does give signed effects; the reading cited its 'measured protein level' near miss."""
    row = _near_miss_row()
    assert stated(row).not_by == []
    paragraph = understanding_paragraph(CapabilityCheck(requirements=[row]))
    assert "does not give it" not in paragraph
    assert "I couldn't match this to anything a registered NetZoo workflow produces or lets you set." in paragraph
