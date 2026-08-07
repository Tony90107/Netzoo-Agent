from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


def _fake_cli_runtime(*, invoke_error, interactive_answers=()):
    bootstrap = importlib.import_module("netzoo_agent_core.cli.bootstrap")
    answers = iter(interactive_answers)

    def input_func(_prompt: str) -> str:
        return next(answers)

    def invoke_graph_turn_func(_app, _invocation: dict) -> dict:
        raise invoke_error

    recorder = Mock()
    recorder.start_run.return_value = "test-run"
    return bootstrap.CliRuntime(
        memory=SimpleNamespace(
            profile_id="test-profile",
            profile_store=Mock(),
            episode_store=Mock(),
        ),
        project_policy=Mock(),
        session_id="test-session",
        resume_id=None,
        conversation=[],
        pending_plan=None,
        active_usage=None,
        run_id=None,
        recorder=recorder,
        trace_store=Mock(),
        ensure_trace_sync=lambda _run_id: None,
        app=object(),
        input_func=input_func,
        invoke_graph_turn_func=invoke_graph_turn_func,
    )


def test_cli_lifecycle_modules_define_the_intended_seams():
    commands = importlib.import_module("netzoo_agent_core.cli.commands")
    bootstrap = importlib.import_module("netzoo_agent_core.cli.bootstrap")
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")

    assert str(inspect.signature(commands.handle_preflight_command)) == (
        "(args) -> 'int | None'"
    )
    assert str(inspect.signature(bootstrap.bootstrap_memory)) == (
        "(args) -> 'MemoryRuntime'"
    )
    assert str(inspect.signature(conversation.run_conversation)) == (
        "(args, runtime: 'CliRuntime') -> 'int'"
    )


def test_one_shot_ordinary_failure_returns_one():
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    runtime = _fake_cli_runtime(invoke_error=RuntimeError("provider unavailable"))

    result = conversation.run_conversation(
        SimpleNamespace(task="run PANDA", keep_session=False),
        runtime,
    )

    assert result == 1


def test_interactive_ordinary_failure_can_continue():
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    runtime = _fake_cli_runtime(
        invoke_error=RuntimeError("provider unavailable"),
        interactive_answers=["first request", "exit"],
    )

    result = conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False),
        runtime,
    )

    assert result == 0


def test_interrupt_remains_130():
    state_contracts = importlib.import_module("netzoo_agent_core.contracts.state")
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    runtime = _fake_cli_runtime(
        invoke_error=state_contracts.AgentTurnInterrupted(),
    )

    result = conversation.run_conversation(
        SimpleNamespace(task="run PANDA", keep_session=False),
        runtime,
    )

    assert result == 130
