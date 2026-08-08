from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core import settings  # noqa: E402
from netzoo_agent_core.contracts import (  # noqa: E402
    InputEvidence,
    PreferenceProposal,
    TaskDecision,
    WorkflowPlan,
)
from netzoo_agent_core.runtime import configure_runtime  # noqa: E402


def _fake_cli_runtime(*, invoke_error, interactive_answers=()):
    bootstrap = importlib.import_module("netzoo_agent_core.cli.bootstrap")
    input_func = Mock(side_effect=interactive_answers)
    invoke_graph_turn_func = Mock(side_effect=invoke_error)

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


def _decision() -> TaskDecision:
    return TaskDecision(
        action="run_panda",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="test",
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


def test_main_prompt_commands_switch_mode_without_graph_or_trace(capsys):
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    previous = settings.EXECUTE_TOOLS
    try:
        configure_runtime(EXECUTE_TOOLS=False)
        runtime = _fake_cli_runtime(
            invoke_error=AssertionError("graph must not run"),
            interactive_answers=["/execute", "/status", "/test", "exit"],
        )

        result = conversation.run_conversation(
            SimpleNamespace(task=None, keep_session=False), runtime
        )

        assert result == 0
        runtime.invoke_graph_turn_func.assert_not_called()
        runtime.recorder.start_run.assert_not_called()
        prompts = [call.args[0] for call in runtime.input_func.call_args_list]
        assert prompts[0].startswith("\n[TEST]")
        assert prompts[1].startswith("\n[EXECUTE]")
        assert "Execution mode enabled" in capsys.readouterr().out
        assert settings.EXECUTE_TOOLS is False
    finally:
        configure_runtime(EXECUTE_TOOLS=previous)


def test_slash_command_does_not_consume_missing_input_state():
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    plan = WorkflowPlan(
        workflow="PANDA",
        objective="run PANDA",
        decision=_decision().model_dump(),
        evidence=[
            InputEvidence(
                field="expression_file",
                status="missing",
                reason="required",
                candidates=["data/expression.tsv"],
            )
        ],
        missing_inputs=["expression_file"],
        status="needs_input",
    )
    runtime = _fake_cli_runtime(
        invoke_error=AssertionError("graph must not run"),
        interactive_answers=["/status", "exit"],
    )
    runtime.pending_plan = plan

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0
    runtime.invoke_graph_turn_func.assert_not_called()
    prompts = [call.args[0] for call in runtime.input_func.call_args_list]
    assert sum("expression_file" in prompt for prompt in prompts) == 2


def test_slash_command_does_not_confirm_preference():
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    plan = WorkflowPlan(
        workflow="NO-TOOL",
        objective="remember preference",
        decision=TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            confidence=1.0,
            reason="test",
        ).model_dump(),
        status="needs_confirmation",
        preference_proposals=[
            PreferenceProposal(
                key="reuse_last_inputs",
                value="true",
                reason="explicit request",
            )
        ],
    )
    runtime = _fake_cli_runtime(
        invoke_error=AssertionError("graph must not run"),
        interactive_answers=["/help", "exit"],
    )
    runtime.pending_plan = plan

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0
    runtime.memory.profile_store.confirm.assert_not_called()
    runtime.invoke_graph_turn_func.assert_not_called()
