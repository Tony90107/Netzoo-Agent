from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from prompt_toolkit.application.current import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.keys import Keys
from prompt_toolkit.output import DummyOutput

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.cli.terminal_input import (  # noqa: E402
    TerminalInputReader,
    _create_inline_mode_application,
    _read_menu_line,
    _select_default_command,
    _split_inline_prompt,
)
from prompt_toolkit.buffer import Buffer  # noqa: E402


def _dispatch_line_keys(default_command: str, keys: str) -> str | None:
    with create_pipe_input() as pipe_input:
        pipe_input.send_text(keys)
        with create_app_session(input=pipe_input, output=DummyOutput()):
            return _read_menu_line("prompt> ", default_command)


def test_split_inline_prompt_keeps_newlines_out_of_input_prefix():
    question, input_prefix = _split_inline_prompt(
        "\nWhat would you like to accomplish with NetZoo?\n> "
    )

    assert question == "\nWhat would you like to accomplish with NetZoo?\n"
    assert input_prefix == "> "
    assert "\n" not in input_prefix


def test_empty_slash_opens_execute_completion_and_returns_selection():
    line_reader = Mock(return_value="/execute")
    reader = TerminalInputReader(
        Mock(),
        is_tty=lambda: True,
        notice=Mock(),
        menu_line_reader=line_reader,
    )

    assert reader.read("prompt\n> ", menu_enabled=True) == "/execute"
    line_reader.assert_called_once_with("prompt\n> ", "/execute")


def test_execute_default_is_buffer_text_with_only_its_suffix_selected():
    buffer = Buffer()

    _select_default_command(buffer, "/execute")

    assert buffer.text == "/execute"
    assert buffer.selection_state is not None
    assert buffer.selection_state.original_cursor_position == 1
    assert buffer.cursor_position == len("/execute")


def test_cancelled_menu_returns_distinct_result_without_fallback_notice():
    notice = Mock()
    reader = TerminalInputReader(
        Mock(),
        is_tty=lambda: True,
        notice=notice,
        menu_line_reader=Mock(return_value=None),
    )

    assert reader.read("prompt", menu_enabled=True) is None
    notice.assert_not_called()


def test_path_and_non_tty_prompts_use_plain_input_without_initializing_tui():
    plain_input = Mock(return_value="/output")
    menu_line_reader = Mock()
    reader = TerminalInputReader(
        plain_input,
        is_tty=lambda: False,
        notice=Mock(),
        menu_line_reader=menu_line_reader,
    )

    assert reader.read("path prompt", menu_enabled=True) == "/output"
    assert reader.read("path prompt", menu_enabled=False) == "/output"
    assert menu_line_reader.call_count == 0


def test_tui_failure_notices_once_then_uses_plain_input():
    plain_input = Mock(side_effect=["/status", "/help"])
    notice = Mock()
    reader = TerminalInputReader(
        plain_input,
        is_tty=lambda: True,
        notice=notice,
        menu_line_reader=Mock(side_effect=RuntimeError("terminal unavailable")),
    )

    assert reader.read("prompt", menu_enabled=True) == "/status"
    assert reader.read("prompt", menu_enabled=True) == "/help"
    notice.assert_called_once()


def test_empty_slash_then_enter_submits_execute_without_full_screen():
    application = _create_inline_mode_application("prompt> ", "/execute")

    assert application.full_screen is False
    assert _dispatch_line_keys("/execute", "/\r") == "/execute"


def test_nonempty_slash_is_preserved_by_real_key_dispatch():
    assert _dispatch_line_keys("/execute", "goal/help\r") == "goal/help"


def test_typed_planning_command_is_not_replaced_by_execute():
    assert _dispatch_line_keys("/execute", "/planning\r") == "/planning"


@pytest.mark.parametrize("key", ["\x1b", "\x03"], ids=["escape", "ctrl-c"])
def test_escape_and_ctrl_c_collapse_selector_and_keep_input_active(key: str):
    assert _dispatch_line_keys("/execute", f"/{key}exit\r") == "exit"
