from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.cli.terminal_input import (  # noqa: E402
    MODE_MENU_OPTIONS,
    TerminalInputReader,
)


def test_mode_menu_options_are_ordered_and_use_existing_commands():
    assert MODE_MENU_OPTIONS == (
        ("/test", "Test mode — preview commands only"),
        ("/execute", "Execute mode — run validated commands"),
    )


def test_empty_slash_trigger_opens_current_mode_menu_and_returns_selection():
    line_reader = Mock(return_value="\0NETZOO_MODE_MENU\0")
    dialog = Mock(return_value="/execute")
    reader = TerminalInputReader(
        Mock(),
        is_tty=lambda: True,
        notice=Mock(),
        menu_line_reader=line_reader,
        menu_dialog=dialog,
        current_mode=lambda: "TEST",
    )

    assert reader.read("[TEST] prompt\n> ", menu_enabled=True) == "/execute"
    dialog.assert_called_once_with("/test")


def test_cancelled_menu_returns_empty_input_without_fallback_notice():
    notice = Mock()
    reader = TerminalInputReader(
        Mock(),
        is_tty=lambda: True,
        notice=notice,
        menu_line_reader=Mock(return_value="\0NETZOO_MODE_MENU\0"),
        menu_dialog=Mock(return_value=None),
        current_mode=lambda: "EXECUTE",
    )

    assert reader.read("prompt", menu_enabled=True) == ""
    notice.assert_not_called()


def test_path_and_non_tty_prompts_use_plain_input_without_initializing_tui():
    plain_input = Mock(return_value="/output")
    menu_line_reader = Mock()
    reader = TerminalInputReader(
        plain_input,
        is_tty=lambda: False,
        notice=Mock(),
        menu_line_reader=menu_line_reader,
        menu_dialog=Mock(),
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
        menu_dialog=Mock(),
        current_mode=lambda: "TEST",
    )

    assert reader.read("prompt", menu_enabled=True) == "/status"
    assert reader.read("prompt", menu_enabled=True) == "/help"
    notice.assert_called_once()
