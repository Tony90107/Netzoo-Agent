from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as legacy_agent  # noqa: E402
import netzoo_agent_core.cli as cli  # noqa: E402
import netzoo_agent_core.interaction as interaction  # noqa: E402


CLI_EXPORTS = ["parse_args", "main", "export_local_trace", "local_trace_status"]
INTERACTION_EXPORTS = [
    "_candidate_selection",
    "parse_clarification_assignments",
    "clarification_continuation",
    "resolve_clarification",
    "clarification_prompt",
    "preference_confirmation_prompt",
    "preference_continuation",
    "initial_next_turn_prompt",
    "build_next_turn_prompt",
    "follow_up_declined",
    "render_next_turn_prompt",
    "follow_up_returns_to_main",
    "resolve_next_turn_input",
]

SIGNATURES = {
    "parse_args": "() -> 'argparse.Namespace'",
    "main": "() -> 'int'",
    "parse_clarification_assignments": (
        "(plan: 'WorkflowPlan', answer: 'str', *, selected: "
        "'dict[str, str] | None' = None, target_field: 'str') -> "
        "'dict[str, str]'"
    ),
    "clarification_prompt": (
        "(plan: 'WorkflowPlan', selected: 'dict[str, str] | None' = None) -> 'str'"
    ),
    "build_next_turn_prompt": "(state: 'dict') -> 'NextTurnPrompt'",
    "resolve_next_turn_input": (
        "(prompt: 'NextTurnPrompt', answer: 'str') -> 'str'"
    ),
}


def test_cli_is_a_package_with_responsibility_modules():
    assert hasattr(cli, "__path__")
    for name in (
        "arguments",
        "trace_commands",
        "clarification",
        "follow_up",
        "loop",
        "main",
        "slash_commands",
        "terminal_input",
    ):
        importlib.import_module(f"netzoo_agent_core.cli.{name}")


def test_cli_surface_and_legacy_identity_are_preserved():
    assert cli.__all__ == CLI_EXPORTS
    for name in CLI_EXPORTS:
        assert getattr(legacy_agent, name) is getattr(cli, name)
    assert not hasattr(legacy_agent, "handle_slash_command")
    for name in ("parse_args", "main"):
        assert str(inspect.signature(getattr(cli, name))) == SIGNATURES[name]


def test_interaction_facade_preserves_historical_identity():
    assert interaction.__all__ == INTERACTION_EXPORTS
    clarification = importlib.import_module("netzoo_agent_core.cli.clarification")
    follow_up = importlib.import_module("netzoo_agent_core.cli.follow_up")
    for name in INTERACTION_EXPORTS:
        owner = clarification if hasattr(clarification, name) else follow_up
        assert getattr(interaction, name) is getattr(owner, name)
        assert getattr(legacy_agent, name) is getattr(owner, name)


def test_representative_interaction_signatures_are_preserved():
    for name in (
        "parse_clarification_assignments",
        "clarification_prompt",
        "build_next_turn_prompt",
        "resolve_next_turn_input",
    ):
        assert str(inspect.signature(getattr(interaction, name))) == SIGNATURES[name]


def test_cli_main_is_orchestration_sized():
    main_module = importlib.import_module("netzoo_agent_core.cli.main")
    assert len(inspect.getsource(main_module.main).splitlines()) <= 140


def test_timeline_is_mutually_exclusive_with_quiet(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["netzoo_agent.py", "--timeline", "--quiet"])

    with pytest.raises(SystemExit) as error:
        cli.parse_args()

    assert error.value.code == 2


def test_execute_startup_flag_is_removed(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["netzoo_agent.py", "--execute"])

    with pytest.raises(SystemExit) as error:
        cli.parse_args()

    assert error.value.code == 2
