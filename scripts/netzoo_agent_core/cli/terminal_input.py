"""Terminal-only input adapter for selecting the interactive runtime mode."""

from __future__ import annotations

from collections.abc import Callable


def _execute_suffix(text: str, command: str) -> str:
    """Return the unmatched execute suffix for a matching slash prefix."""
    if text.startswith("/") and command.casefold().startswith(text.casefold()):
        return command[len(text) :]
    return ""


class TerminalInputReader:
    """Read terminal input, exposing an inline selector at an empty slash prompt."""

    def __init__(
        self,
        input_func: Callable[[str], str],
        *,
        is_tty: Callable[[], bool],
        notice: Callable[[str], None],
        menu_line_reader: Callable[[str, str], str | None] | None = None,
        option_line_reader: Callable[[str, list[dict], Callable[[int | None], list[str]]], str | None] | None = None,
    ) -> None:
        self._input_func = input_func
        self._is_tty = is_tty
        self._notice = notice
        self._menu_line_reader_is_injected = menu_line_reader is not None
        self._menu_line_reader = menu_line_reader or _read_menu_line
        self._option_line_reader = option_line_reader or _read_option_line
        self._option_reader_is_injected = option_line_reader is not None
        self._tui_warning_shown = False

    def read_option(
        self,
        prompt: str,
        options: list[dict],
        render: Callable[[int | None], list[str]],
    ) -> str | None:
        """Read an answer with the reply's options listed and selectable by arrow keys.

        Enter on an empty line picks the highlighted option and returns its
        number, which the machine maps to that option; any typed text is
        returned as written. Without a usable terminal the options are printed
        and the line is read as usual.
        """
        interactive = self._is_tty() and (self._input_func is input or self._option_reader_is_injected)
        if interactive:
            try:
                return self._option_line_reader(prompt, options, render)
            except (EOFError, KeyboardInterrupt):
                raise
            except Exception:
                self._warn_once()
        for line in render(None):
            self._notice(line)
        return self._input_func(prompt)

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
    """Build one normal-screen application with a shrinking slash completion."""
    from prompt_toolkit.application import Application
    from prompt_toolkit.filters import Condition
    from prompt_toolkit.layout.processors import Processor, Transformation
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.containers import ConditionalContainer, HSplit, Window
    from prompt_toolkit.layout.controls import FormattedTextControl
    from prompt_toolkit.styles import Style
    from prompt_toolkit.widgets import TextArea

    class _ExecuteCompletionProcessor(Processor):
        def apply_transformation(self, transformation_input):
            suffix = _execute_suffix(
                transformation_input.document.text,
                default_command,
            )
            return Transformation(
                transformation_input.fragments
                + ([('class:execute-completion', suffix)] if suffix else [])
            )

    question, input_prefix = _split_inline_prompt(prompt)
    input_field = TextArea(
        # Keep the buffer multiline so long natural-language tasks can wrap in
        # the terminal instead of being horizontally scrolled inside a fixed
        # one-line widget.  The Enter binding below still submits the whole
        # buffer, so this does not turn the prompt into a multi-step editor.
        multiline=True,
        prompt=input_prefix,
        input_processors=[_ExecuteCompletionProcessor()],
    )
    bindings = KeyBindings()

    @bindings.add("/")
    def _open_selector(event) -> None:
        input_field.buffer.insert_text("/")

    @bindings.add("enter", eager=True)
    def _submit(event) -> None:
        text = input_field.text
        event.app.exit(
            result=default_command
            if text and default_command.casefold().startswith(text.casefold())
            else text
        )

    @bindings.add("escape", eager=True)
    @bindings.add("c-c", eager=True)
    def _cancel(event) -> None:
        if input_field.text == "/":
            input_field.buffer.reset()
            event.app.invalidate()
            return
        event.app.exit(exception=KeyboardInterrupt())

    question_window = ConditionalContainer(
        Window(
            content=FormattedTextControl(lambda: question),
            dont_extend_height=True,
            # Display-only guidance needs wrapping too, independently of the
            # editable TextArea. Otherwise Next step silently clips at the
            # current terminal width, including after a resize.
            wrap_lines=True,
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
        style=Style.from_dict({"execute-completion": "fg:#666666"}),
    )


def _read_option_line(prompt: str, options: list[dict], render) -> str:
    return _create_option_application(prompt, options, render).run()


def _create_option_application(prompt: str, options: list[dict], render):
    """A normal-screen picker: the options above, a free-text line below."""
    from prompt_toolkit.application import Application
    from prompt_toolkit.formatted_text import ANSI
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.containers import HSplit, Window
    from prompt_toolkit.layout.controls import FormattedTextControl
    from prompt_toolkit.widgets import TextArea

    question, input_prefix = _split_inline_prompt(prompt)
    state = {"active": 0}
    input_field = TextArea(multiline=True, prompt=input_prefix)
    bindings = KeyBindings()

    def _empty() -> bool:
        return not input_field.text

    @bindings.add("up", filter=_as_filter(_empty))
    def _up(event) -> None:
        state["active"] = (state["active"] - 1) % len(options)
        event.app.invalidate()

    @bindings.add("down", filter=_as_filter(_empty))
    def _down(event) -> None:
        state["active"] = (state["active"] + 1) % len(options)
        event.app.invalidate()

    @bindings.add("enter", eager=True)
    def _submit(event) -> None:
        text = input_field.text
        event.app.exit(result=text if text.strip() else str(state["active"] + 1))

    @bindings.add("escape", eager=True)
    def _clear(event) -> None:
        input_field.buffer.reset()
        event.app.invalidate()

    @bindings.add("c-c", eager=True)
    def _cancel(event) -> None:
        event.app.exit(exception=KeyboardInterrupt())

    hint = "↑/↓ choose · Enter selects · or type your own answer"
    menu = Window(
        content=FormattedTextControl(lambda: ANSI("\n".join([*render(state["active"]), hint]))),
        dont_extend_height=True,
        wrap_lines=True,
    )
    children = [menu, input_field]
    if question.strip():
        children.insert(0, Window(content=FormattedTextControl(lambda: question),
                                  dont_extend_height=True, wrap_lines=True))
    return Application(
        layout=Layout(HSplit(children), focused_element=input_field),
        key_bindings=bindings,
        full_screen=False,
    )


def _as_filter(predicate):
    from prompt_toolkit.filters import Condition

    return Condition(predicate)
