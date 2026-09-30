"""Terminal driver for the conversation engine.

The state machine itself lives in ``netzoo_agent_core.engine``; this module is
the adapter that gives it a terminal: it reads lines, prints events, and owns
the two behaviours that only make sense at a tty — interrupt handling and the
non-interactive ``--resume`` hand-off.  A desktop UI attaches a second driver
to the same machine rather than reimplementing these transitions.
"""

from __future__ import annotations

import sys

# ruff: noqa: F401 -- NextTurnPrompt is imported for callers that patch this
# module's seams (TerminalInputReader, initial_next_turn_prompt) in tests.
from ..contracts.state import NextTurnPrompt
from ..engine.view import Event, Stop, Turn
from ..presentation import _clear_transient_trace, _ui_text
from .bootstrap import CliRuntime
from .follow_up import initial_next_turn_prompt
from .terminal_input import TerminalInputReader

__all__: list[str] = []


def _render(event: Event, brief: "_BriefReplies | None" = None) -> None:
    if event.kind == "blank":
        print()
        return
    if brief is not None and event.kind == "message":
        print(brief.message(event))
        return
    print(event.text)


class _BriefReplies:
    """Brief replies, Markdown and option menus for an interactive terminal.

    Built only for a real terminal: tests, pipes and ``--full-replies`` print the
    agent's full text exactly as before.
    """

    def __init__(self):
        from .terminal_cards import render_card, render_markdown

        self._card = render_card
        self._markdown = render_markdown
        self.last_full: str | None = None

    def message(self, event: Event) -> str:
        self.last_full = event.text
        if event.card and event.card.get("headline"):
            return "\n" + self._card(event.card)
        return self._markdown(event.text)

    def details(self) -> str:
        return self._markdown(self.last_full) if self.last_full else _ui_text("There is no earlier reply to expand.")


def run_conversation(args, runtime: CliRuntime) -> int:
    # Imported here, not at module scope: the engine reaches back into
    # ``cli.clarification`` and ``cli.follow_up`` for prompt rendering, and
    # ``cli/__init__`` imports this module, so a module-level import would
    # close the loop. ``engine.view`` has no such dependency and stays above.
    from ..engine.choices import selectable_options
    from ..engine.machine import ConversationMachine
    from .terminal_cards import DETAILS_COMMAND, option_prompt, render_options

    reader = TerminalInputReader(
        runtime.input_func,
        is_tty=sys.stdin.isatty,
        notice=lambda message: print(_ui_text(message)),
    )
    brief = (
        _BriefReplies()
        if runtime.input_func is input and sys.stdin.isatty() and sys.stdout.isatty()
        and not getattr(args, "full_replies", False)
        else None
    )
    machine = ConversationMachine(
        args,
        runtime,
        initial_prompt_factory=initial_next_turn_prompt,
    )
    if (opening := machine.opening_notice()) is not None:
        _render(opening)

    while True:
        action = machine.next_action()
        if isinstance(action, Stop):
            return action.exit_code
        if isinstance(action, Turn):
            for event in machine.run_turn():
                _render(event, brief)
            continue
        if (
            action.noninteractive_text is not None
            and not sys.stdin.isatty()
            and runtime.input_func is input
        ):
            _clear_transient_trace()
            print(action.noninteractive_text)
            print(
                _ui_text("Run the command again with --resume ")
                + f"{machine.state.session_id}"
                + _ui_text(" after preparing the answer.")
            )
            return 2
        options = selectable_options(action.card) if brief is not None else []
        try:
            if options:
                raw_answer = reader.read_option(
                    option_prompt(action.text), options,
                    lambda active, card=action.card: render_options(card, active=active),
                )
            else:
                raw_answer = reader.read(action.text, menu_enabled=action.menu_enabled)
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if raw_answer is None:
            continue
        if brief is not None and raw_answer.strip().casefold() == DETAILS_COMMAND:
            print(brief.details())
            continue
        for event in machine.submit(raw_answer):
            _render(event, brief)
