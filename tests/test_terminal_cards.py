"""An interactive terminal shows a reply's key points and options first."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock

from prompt_toolkit.application.current import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.cli.terminal_cards import render_card, render_markdown, render_options  # noqa: E402
from netzoo_agent_core.cli.terminal_input import TerminalInputReader, _read_option_line  # noqa: E402

CARD = {
    "kind": "method_choice",
    "headline": "2 registered methods can build a per-sample co-expression network.",
    "points": ["Recommended: BONOBO, from what you said.", "Nothing has run yet."],
    "choices": {
        "header": "Method", "question": "Which method fits your study?", "ordering": "Recommended first.",
        "allow_other": True,
        "options": [
            {"key": "run_bonobo", "label": "BONOBO", "badge": "Recommended", "answer": "Use BONOBO",
             "description": "Fits what you said: you have only a handful of samples", "available": True,
             "resolution": "confirm_workflow"},
            {"key": "run_lioness_coexpression", "label": "LIONESS-COEXPRESSION", "badge": "",
             "answer": "Use LIONESS-COEXPRESSION", "description": "", "available": True,
             "resolution": "confirm_workflow"},
        ],
    },
    "unavailable": [{"key": "x", "label": "TIGER", "reason": "netZooR only", "available": False, "resolution": "none"}],
    "next_steps": [{"key": "new-task", "label": "Start a new task", "answer": "new", "available": True,
                    "resolution": "command"}],
    "ran_nothing": True,
}


def test_markdown_becomes_terminal_text_without_markup():
    text = render_markdown("## Result\n\n**PANDA** uses `motif_file`.\n- first\n  - nested\n---", color=False)
    assert text.splitlines() == ["Result", "", "PANDA uses motif_file.", "• first", "  ◦ nested", "─" * 60]


def test_markdown_tables_and_code_blocks_keep_their_layout():
    text = render_markdown("| a | b |\n| - | - |\n```\nrun-panda -e x\n```", color=False)
    assert "| a | b |" in text and "run-panda -e x" in text and "```" not in text


def test_a_card_shows_the_brief_form_and_where_the_full_reply_is():
    text = render_card(CARD, color=False)
    assert text.splitlines()[0] == CARD["headline"]
    assert "  • Recommended: BONOBO, from what you said." in text
    assert "✕ TIGER — netZooR only" in text
    assert text.endswith("Full explanation: /details")


def test_options_are_numbered_as_the_machine_numbers_them():
    lines = render_options(CARD, color=False)
    assert "  1) BONOBO  (Recommended)" in lines
    assert "  2) LIONESS-COEXPRESSION" in lines
    assert lines[-1] == "  Next: 3) Start a new task"
    assert any("TIGER — not available here" in line for line in lines)


def _pick(keys: str) -> str:
    with create_pipe_input() as pipe_input:
        pipe_input.send_text(keys)
        with create_app_session(input=pipe_input, output=DummyOutput()):
            options = CARD["choices"]["options"] + CARD["next_steps"]
            return _read_option_line("Next step\n> ", options, lambda active: render_options(CARD, active=active))


def test_enter_on_an_empty_line_picks_the_highlighted_option_by_number():
    assert _pick("\r") == "1"
    assert _pick("\x1b[B\r") == "2"   # down arrow
    assert _pick("\x1b[A\r") == "3"   # up arrow wraps to the next step


def test_typed_text_is_returned_as_written():
    assert _pick("How do they differ?\r") == "How do they differ?"


def test_without_a_terminal_the_options_are_printed_and_a_line_is_read():
    notices = []
    plain = Mock(return_value="2")
    reader = TerminalInputReader(plain, is_tty=lambda: False, notice=notices.append)
    options = CARD["choices"]["options"]
    assert reader.read_option("> ", options, lambda active: render_options(CARD, active=active, color=False)) == "2"
    assert any("1) BONOBO" in line for line in notices)
    plain.assert_called_once_with("> ")
