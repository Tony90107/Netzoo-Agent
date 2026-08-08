"""Terminal-only input adapter for selecting the interactive runtime mode."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .slash_commands import current_mode_label

MODE_MENU_OPTIONS = (
    ("/test", "Test mode — preview commands only"),
    ("/execute", "Execute mode — run validated commands"),
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
        current_mode: Callable[[], str] = current_mode_label,
    ) -> None:
        self._input_func = input_func
        self._is_tty = is_tty
        self._notice = notice
        self._menu_line_reader_is_injected = menu_line_reader is not None
        self._menu_line_reader = menu_line_reader or _read_menu_line
        self._current_mode = current_mode
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
        return "/execute" if self._current_mode() == "EXECUTE" else "/test"

    def _warn_once(self) -> None:
        if self._tui_warning_shown:
            return
        self._tui_warning_shown = True
        self._notice("Terminal mode selector unavailable; using plain input.")


def _read_menu_line(prompt: str, default_command: str) -> str:
    """Read a line with an inline mode selector available on an empty slash."""
    return _create_inline_mode_application(prompt, default_command).run()


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

    state: dict[str, Any] = {"visible": False, "selected": default_command}
    input_field = TextArea(multiline=False, prompt=prompt)
    bindings = KeyBindings()

    def _toggle_selected() -> None:
        state["selected"] = (
            "/execute" if state["selected"] == "/test" else "/test"
        )

    def _selector_text() -> FormattedText:
        fragments: list[tuple[str, str]] = []
        for command, description in MODE_MENU_OPTIONS:
            selected = state["selected"] == command
            marker = "▸" if selected else " "
            style = "class:mode-menu.selected" if selected else ""
            fragments.append((style, f"{marker} {command:<10} {description}\n"))
        fragments.append(("class:mode-menu.hint", "  ↑/↓/Tab move · Enter select · Esc/Ctrl-C cancel"))
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

    @bindings.add("up", eager=True)
    @bindings.add("down", eager=True)
    @bindings.add("tab", eager=True)
    def _move_selector(event) -> None:
        if not state["visible"]:
            return
        _toggle_selected()
        event.app.invalidate()

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

    selector = ConditionalContainer(
        Window(content=FormattedTextControl(_selector_text)),
        filter=Condition(lambda: state["visible"]),
    )
    return Application(
        layout=Layout(HSplit([input_field, selector]), focused_element=input_field),
        key_bindings=bindings,
        full_screen=False,
    )
