"""Terminal-only input adapter for selecting the interactive runtime mode."""

from __future__ import annotations

from collections.abc import Callable


def _select_default_command(buffer, command: str) -> None:
    """Load a command and select its suffix so typed text replaces it."""
    buffer.text = command
    buffer.cursor_position = 1
    buffer.start_selection()
    buffer.cursor_position = len(command)


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


def _create_inline_mode_application(prompt: str, default_command: str):
    """Build one normal-screen application with a selected slash default."""
    from prompt_toolkit.application import Application
    from prompt_toolkit.filters import Condition
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.keys import Keys
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.containers import ConditionalContainer, HSplit, Window
    from prompt_toolkit.layout.controls import FormattedTextControl
    from prompt_toolkit.styles import Style
    from prompt_toolkit.widgets import TextArea

    question, input_prefix = _split_inline_prompt(prompt)
    input_field = TextArea(multiline=False, prompt=input_prefix)
    bindings = KeyBindings()

    @bindings.add("/")
    def _open_selector(event) -> None:
        if input_field.text:
            input_field.buffer.insert_text("/")
            return
        _select_default_command(input_field.buffer, default_command)

    @bindings.add(
        Keys.Any,
        filter=Condition(lambda: input_field.buffer.selection_state is not None),
        eager=True,
    )
    def _replace_selected_default(event) -> None:
        input_field.buffer.cut_selection()
        input_field.buffer.insert_text(event.data)

    @bindings.add("enter", eager=True)
    def _submit(event) -> None:
        event.app.exit(result=input_field.text)

    @bindings.add("escape", eager=True)
    @bindings.add("c-c", eager=True)
    def _cancel(event) -> None:
        if input_field.text == default_command:
            input_field.buffer.reset()
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
    return Application(
        layout=Layout(
            HSplit([question_window, input_field]),
            focused_element=input_field,
        ),
        key_bindings=bindings,
        full_screen=False,
        style=Style.from_dict({"selection": "fg:#777777 bg:#1e1e1e"}),
    )
