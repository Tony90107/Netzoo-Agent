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
    MODE_MENU_OPTIONS,
    TerminalInputReader,
    _create_inline_mode_application,
    _read_menu_line,
)


def _dispatch_line_keys(default_command: str, keys: str) -> str | None:
    with create_pipe_input() as pipe_input:
        pipe_input.send_text(keys)
        with create_app_session(input=pipe_input, output=DummyOutput()):
            return _read_menu_line("prompt> ", default_command)


def test_mode_menu_options_are_ordered_and_use_existing_commands():
    assert MODE_MENU_OPTIONS == (
        ("/test", "Test mode — preview commands only"),
        ("/execute", "Execute mode — run validated commands"),
    )


def test_empty_slash_opens_current_mode_menu_and_returns_selection():
    line_reader = Mock(return_value="/execute")
    reader = TerminalInputReader(
        Mock(),
        is_tty=lambda: True,
        notice=Mock(),
        menu_line_reader=line_reader,
        current_mode=lambda: "TEST",
    )

    assert reader.read("[TEST] prompt\n> ", menu_enabled=True) == "/execute"
    line_reader.assert_called_once_with("[TEST] prompt\n> ", "/test")


def test_cancelled_menu_returns_distinct_result_without_fallback_notice():
    notice = Mock()
    reader = TerminalInputReader(
        Mock(),
        is_tty=lambda: True,
        notice=notice,
        menu_line_reader=Mock(return_value=None),
        current_mode=lambda: "EXECUTE",
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
        current_mode=lambda: "TEST",
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
        current_mode=lambda: "TEST",
    )

    assert reader.read("prompt", menu_enabled=True) == "/status"
    assert reader.read("prompt", menu_enabled=True) == "/help"
    notice.assert_called_once()


def test_empty_slash_then_enter_selects_current_test_mode_without_full_screen():
    application = _create_inline_mode_application("prompt> ", "/test")

    assert application.full_screen is False
    assert _dispatch_line_keys("/test", "/\r") == "/test"


def test_nonempty_slash_is_preserved_by_real_key_dispatch():
    assert _dispatch_line_keys("/test", "goal/help\r") == "goal/help"


@pytest.mark.parametrize("command", ["test", "execute", "status", "help"])
def test_ctrl_v_pass_through_supports_every_text_command(command: str):
    assert _dispatch_line_keys("/test", f"\x16{command}\r") == f"/{command}"


def test_down_then_enter_selects_execute_from_test():
    assert _dispatch_line_keys("/test", "/\x1b[B\r") == "/execute"


def test_up_then_enter_selects_test_from_execute():
    assert _dispatch_line_keys("/execute", "/\x1b[A\r") == "/test"


def test_tab_then_enter_selects_execute_from_test():
    assert _dispatch_line_keys("/test", "/\t\r") == "/execute"


@pytest.mark.parametrize("key", ["\x1b", "\x03"], ids=["escape", "ctrl-c"])
def test_escape_and_ctrl_c_collapse_selector_and_keep_input_active(key: str):
    assert _dispatch_line_keys("/execute", f"/{key}exit\r") == "exit"
