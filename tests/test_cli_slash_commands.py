from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core import settings  # noqa: E402
from netzoo_agent_core.cli.slash_commands import (  # noqa: E402
    current_mode_label,
    handle_slash_command,
    render_mode_prompt,
)
from netzoo_agent_core.runtime import configure_runtime  # noqa: E402


@pytest.fixture(autouse=True)
def restore_execution_mode():
    previous = settings.EXECUTE_TOOLS
    configure_runtime(EXECUTE_TOOLS=False)
    yield
    configure_runtime(EXECUTE_TOOLS=previous)


def test_natural_language_and_absolute_paths_are_not_slash_commands():
    for user_input in (
        "run PANDA",
        "/work/data/expression.tsv",
        "/expression.tsv",
        "expression_file=/data/expression.tsv",
    ):
        result = handle_slash_command(user_input)
        assert result.handled is False
        assert result.message == ""


def test_execute_and_test_switch_the_process_mode_persistently():
    execute = handle_slash_command("/execute")
    assert execute.handled is True
    assert "Execution mode enabled" in execute.message
    assert settings.EXECUTE_TOOLS is True
    assert current_mode_label() == "EXECUTE"
    assert render_mode_prompt("Question") == "[EXECUTE] Question"

    test = handle_slash_command("/TEST")
    assert test.handled is True
    assert "Test mode enabled" in test.message
    assert settings.EXECUTE_TOOLS is False
    assert current_mode_label() == "TEST"


def test_status_and_help_report_without_changing_mode():
    status = handle_slash_command("/status")
    assert status == type(status)(handled=True, message="Current mode: TEST")

    help_result = handle_slash_command("/help")
    assert help_result.handled is True
    for command in ("/test", "/execute", "/status", "/help"):
        assert command in help_result.message
    assert settings.EXECUTE_TOOLS is False


def test_unknown_command_and_trailing_arguments_are_consumed_locally():
    unknown = handle_slash_command("/exec")
    assert unknown.handled is True
    assert "Unknown slash command: /exec" in unknown.message
    assert "/help" in unknown.message

    arguments = handle_slash_command("/execute run PANDA")
    assert arguments.handled is True
    assert "Enter /execute by itself" in arguments.message
    assert settings.EXECUTE_TOOLS is False
