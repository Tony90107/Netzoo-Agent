"""Terminal-only input adapter for selecting the interactive runtime mode."""

from __future__ import annotations

from collections.abc import Callable

from .slash_commands import current_mode_label

MODE_MENU_TRIGGER = "\0NETZOO_MODE_MENU\0"
MODE_MENU_OPTIONS = (
    ("/test", "Test mode — preview commands only"),
    ("/execute", "Execute mode — run validated commands"),
)


class TerminalInputReader:
    """Read terminal input, exposing a mode selector at an empty slash prompt."""

    def __init__(
        self,
        input_func: Callable[[str], str],
        *,
        is_tty: Callable[[], bool],
        notice: Callable[[str], None],
        menu_line_reader: Callable[[str], str] | None = None,
        menu_dialog: Callable[[str], str | None] | None = None,
        current_mode: Callable[[], str] = current_mode_label,
    ) -> None:
        self._input_func = input_func
        self._is_tty = is_tty
        self._notice = notice
        self._menu_line_reader_is_injected = menu_line_reader is not None
        self._menu_line_reader = menu_line_reader or _read_menu_line
        self._menu_dialog = menu_dialog or _show_mode_menu
        self._current_mode = current_mode
        self._tui_warning_shown = False

    def read(self, prompt: str, *, menu_enabled: bool) -> str:
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
            answer = self._menu_line_reader(prompt)
        except (EOFError, KeyboardInterrupt):
            raise
        except Exception:
            self._warn_once()
            return self._input_func(prompt)
        if answer != MODE_MENU_TRIGGER:
            return answer
        return self._menu_dialog(self._default_command()) or ""

    def _default_command(self) -> str:
        return "/execute" if self._current_mode() == "EXECUTE" else "/test"

    def _warn_once(self) -> None:
        if self._tui_warning_shown:
            return
        self._tui_warning_shown = True
        self._notice("Terminal mode selector unavailable; using plain input.")


def _read_menu_line(prompt: str) -> str:
    """Read one line, opening the selector when slash starts an empty buffer."""
    from prompt_toolkit import prompt as toolkit_prompt
    from prompt_toolkit.key_binding import KeyBindings

    bindings = KeyBindings()

    @bindings.add("/")
    def _open_mode_menu(event) -> None:
        if not event.app.current_buffer.text:
            event.app.exit(result=MODE_MENU_TRIGGER)

    return toolkit_prompt(prompt, key_bindings=bindings)


def _show_mode_menu(default_command: str) -> str | None:
    """Present the available mode commands and return the selected command."""
    from prompt_toolkit.shortcuts import radiolist_dialog

    return radiolist_dialog(
        title="NetZoo mode",
        text="Choose how validated workflow commands should run.",
        values=MODE_MENU_OPTIONS,
        default=default_command,
    ).run()
