"""Terminal-only input adapter for selecting the interactive runtime mode."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

MODE_MENU_OPTIONS = (
    ("/execute", "Execute — run validated commands for this session"),
)


class TerminalInputReader:
    """Read terminal input, exposing an inline selector at an empty slash prompt."""

    def __init__(
        self,
        input_func: Callable[[str], str],
        *,
        is_tty: Callable[[], bool],
        notice: Callable[[str], None],
        menu_line_reader: Callable[[str, str], str | None] | None = None,
    ) -> None:
        self._input_func = input_func
        self._is_tty = is_tty
        self._notice = notice
        self._menu_line_reader_is_injected = menu_line_reader is not None
        self._menu_line_reader = menu_line_reader or _read_menu_line
        self._tui_warning_shown = False

    def read(self, prompt: str, *, menu_enabled: bool) -> str | None:
        if (
            not menu_enabled
            or not self._is_tty()
            or (
                self._input_func is not input
                and not self._menu_line_reader_is_injected
            )
        ):
            return self._input_func(prompt)
        try:
            return self._menu_line_reader(prompt, self._default_command())
        except (EOFError, KeyboardInterrupt):
            raise
        except Exception:
            self._warn_once()
            return self._input_func(prompt)

    def _default_command(self) -> str:
        return "/execute"

    def _warn_once(self) -> None:
        if self._tui_warning_shown:
            return
        self._tui_warning_shown = True
        self._notice("Terminal mode selector unavailable; using plain input.")


def _read_menu_line(prompt: str, default_command: str) -> str:
    """Read a line with an inline mode selector available on an empty slash."""
    return _create_inline_mode_application(prompt, default_command).run()


def _split_inline_prompt(prompt: str) -> tuple[str, str]:
    """Separate display-only prompt text from the one-line input prefix."""
    question, separator, input_prefix = prompt.rpartition("\n")
    if not separator:
        return "", prompt
    return question + separator, input_prefix


def _selector_lines(selected_command: str) -> list[str]:
    """Return the compact visible rows for the mode selector."""
    return [
        f"{'▸' if command == selected_command else ' '} {command:<10} {description}"
        for command, description in MODE_MENU_OPTIONS
    ]


def _create_inline_mode_application(prompt: str, default_command: str):
    """Build one normal-screen application containing the prompt and selector."""
    from prompt_toolkit.application import Application
    from prompt_toolkit.filters import Condition
    from prompt_toolkit.formatted_text import FormattedText
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.containers import ConditionalContainer, HSplit, Window
    from prompt_toolkit.layout.controls import FormattedTextControl
    from prompt_toolkit.widgets import TextArea

    question, input_prefix = _split_inline_prompt(prompt)
    state: dict[str, Any] = {"visible": False, "selected": default_command}
    input_field = TextArea(multiline=False, prompt=input_prefix)
    bindings = KeyBindings()

    def _selector_text() -> FormattedText:
        fragments: list[tuple[str, str]] = []
        for line in _selector_lines(state["selected"]):
            style = "class:mode-menu.selected" if line.startswith("▸") else ""
            fragments.append((style, line + "\n"))
        return FormattedText(fragments)

    @bindings.add("/")
    def _open_selector(event) -> None:
        if input_field.text:
            input_field.buffer.insert_text("/")
            return
        state["visible"] = True
        event.app.invalidate()

    @bindings.add("c-v")
    def _insert_literal_slash(event) -> None:
        input_field.buffer.insert_text("/")

    @bindings.add("enter", eager=True)
    def _submit(event) -> None:
        if state["visible"]:
            event.app.exit(result=state["selected"])
            return
        event.app.exit(result=input_field.text)

    @bindings.add("escape", eager=True)
    @bindings.add("c-c", eager=True)
    def _cancel(event) -> None:
        if state["visible"]:
            state["visible"] = False
            event.app.invalidate()
            return
        event.app.exit(exception=KeyboardInterrupt())

    question_window = ConditionalContainer(
        Window(
            content=FormattedTextControl(lambda: question),
            dont_extend_height=True,
        ),
        filter=Condition(lambda: bool(question)),
    )
    selector = ConditionalContainer(
        Window(
            content=FormattedTextControl(_selector_text),
            dont_extend_height=True,
        ),
        filter=Condition(lambda: state["visible"]),
    )
    return Application(
        layout=Layout(
            HSplit([question_window, input_field, selector]),
            focused_element=input_field,
        ),
        key_bindings=bindings,
        full_screen=False,
    )
