# Inline Slash Mode Selector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the full-screen slash mode dialog with an inline terminal selector displayed below the active NetZoo prompt.

**Architecture:** `TerminalInputReader` remains the only terminal-specific adapter and returns either a synthetic `/test` or `/execute` command or ordinary typed text. Its prompt-toolkit reader becomes one non-full-screen application containing the input buffer and a conditionally visible two-row selector; cancellation hides only that selector and keeps the same application alive. `conversation.py` continues to be the sole caller of the existing slash-command authority.

**Tech Stack:** Python 3.12, prompt_toolkit 3.x, pytest, prompt_toolkit `PipeInput` and `DummyOutput`.

## Global Constraints

- Keep `prompt_toolkit>=3.0,<4` in `environment.yml`; do not add a second terminal UI dependency.
- Do not create `Dialog` instances or full-screen prompt-toolkit applications for mode selection.
- At an empty eligible TTY prompt, `/` expands the inline selector immediately; at a nonempty prompt, `/` is literal.
- The selector has exactly `/test` and `/execute`, defaults to the current mode, supports Up/Down/Tab, Enter, Esc, and Ctrl-C.
- Cancellation must collapse the selector in place, preserve the active buffer, mode, and pending state, and never create a graph turn or trace.
- Path-role prompts and non-TTY/injected input retain their existing plain-input behavior.
- `handle_slash_command()` remains the only execution-mode state-transition authority.

---

### Task 1: Replace the modal input adapter with an inline selector

**Files:**
- Modify: `scripts/netzoo_agent_core/cli/terminal_input.py`
- Modify: `tests/test_terminal_input.py`

**Interfaces:**
- Consumes: `TerminalInputReader.read(prompt: str, *, menu_enabled: bool) -> str | None` and `current_mode_label() -> str`.
- Produces: the same `read()` result contract, with an injected `menu_line_reader(prompt: str, default_command: str) -> str` test seam.
- Removes: `MODE_MENU_TRIGGER`, `_show_mode_menu()`, and `_create_mode_menu()`; no caller outside this module may depend on them.

- [ ] **Step 1: Write failing real-dispatch tests for the inline selector**

  In `tests/test_terminal_input.py`, replace dialog-oriented helpers with one that sends pipe input to the inline reader. Add selection assertions and an application-construction assertion that proves the selector is not full-screen:

  ```python
  def _dispatch_inline_keys(default_command: str, keys: str) -> str | None:
      with create_pipe_input() as pipe_input:
          pipe_input.send_text(keys)
          with create_app_session(input=pipe_input, output=DummyOutput()):
              return _read_menu_line("prompt> ", default_command)

  def test_inline_selector_down_then_enter_selects_execute():
      assert _dispatch_inline_keys("/test", "/\x1b[B\r") == "/execute"

  def test_inline_selector_application_is_not_full_screen():
      application = _create_inline_mode_application("prompt> ", "/test")
      assert application.full_screen is False
  ```

  Add tests for current-mode default selection, Up from `/execute`, Tab navigation, Esc and Ctrl-C collapsing before an ordinary `exit` submission, a nonempty literal slash, and Ctrl-V text-command pass-through. Update the injected-adapter tests to pass a two-argument reader and assert it receives the expected default command.

- [ ] **Step 2: Run the focused tests to verify failure**

  Run: `python -m pytest tests/test_terminal_input.py -q`

  Expected: FAIL because `_read_menu_line` does not accept a default command and the current implementation still creates a `Dialog` application.

- [ ] **Step 3: Implement the non-full-screen input application**

  In `scripts/netzoo_agent_core/cli/terminal_input.py`:

  ```python
  def _read_menu_line(prompt: str, default_command: str) -> str:
      return _create_inline_mode_application(prompt, default_command).run()

  def _create_inline_mode_application(
      prompt: str, default_command: str
  ) -> Application:
      state = {"visible": False, "selected": default_command}
      buffer = Buffer(multiline=False)
      return Application(
          layout=Layout(
              HSplit([BufferControl(buffer=buffer), _selector_rows(state)]),
              focused_element=buffer,
          ),
          key_bindings=_inline_key_bindings(buffer, state),
          full_screen=False,
      )
  ```

  Use a boolean selector-visible state and a selected-command state initialized to `default_command`. Bind `/` to expand only when `buffer.text` is empty; otherwise call `buffer.insert_text("/")`. Bind Up, Down, and Tab to change selection only when visible; bind Enter to `app.exit(result=selected_command)` only when visible, otherwise accept normal input. Bind Esc/Ctrl-C to hide the selector and restore focus to the input buffer; return `None` only when cancellation terminates the read rather than producing an empty submitted answer. Render the two option rows through a `ConditionalContainer` below the input control, with a visible `▸` marker for the selected row.

  Change `TerminalInputReader` to invoke `_menu_line_reader(prompt, self._default_command())` in one try block. Preserve the existing once-only fallback notice if prompt-toolkit initialization fails. The Esc/Ctrl-C selector binding must hide the selector and leave the application running rather than returning `None`.

- [ ] **Step 4: Run focused tests to verify success**

  Run: `python -m pytest tests/test_terminal_input.py -q`

  Expected: PASS, including real key-dispatch coverage for inline navigation and cancellation.

- [ ] **Step 5: Commit the adapter change**

  ```bash
  git add scripts/netzoo_agent_core/cli/terminal_input.py tests/test_terminal_input.py
  git commit -m "feat: render slash mode selector inline"
  ```

### Task 2: Preserve lifecycle behavior and correct user-facing documentation

**Files:**
- Modify: `tests/test_cli_lifecycle.py`
- Modify: `README.md`
- Modify: `AGENT_USAGE.md`

**Interfaces:**
- Consumes: `TerminalInputReader.read()` synthetic command and cancellation contracts from Task 1.
- Produces: unchanged conversation-level guarantees for preference confirmation, clarification, task prompts, and path-role inputs; accurate terminal guidance.

- [ ] **Step 1: Write failing lifecycle and documentation assertions**

  Extend `tests/test_cli_lifecycle.py` so an inline selector cancellation followed by `exit` at a preference prompt cannot be interpreted as a no answer, and so a selected `/execute` still reaches `handle_slash_command()` without invoking the graph or starting a trace. Add documentation assertions only if the repository has a documentation test convention; otherwise inspect the exact rendered snippets in review.

  Update the existing `test_menu_cancellation_preserves_preference_confirmation_and_mode` fixture to use a reader result of `exit` after the selector has been locally collapsed; assert `profile_store.confirm` is never called. Keep `test_mode_menu_selection_reuses_slash_handler_without_graph_or_trace` as the `/execute` authority-boundary regression test.

- [ ] **Step 2: Run lifecycle coverage to verify the test is meaningful**

  Run: `python -m pytest tests/test_cli_lifecycle.py -q`

  Expected: PASS if Task 1 preserved the established `None` contract; otherwise fix only the conversation boundary required to distinguish cancellation from text input.

- [ ] **Step 3: Update user guidance from dialog language to inline language**

  In both `README.md` and `AGENT_USAGE.md`, replace any implication of a popup or separate selector with this behavior: `/` at an empty eligible prompt expands two choices beneath the prompt; arrows or Tab choose; Enter applies; Esc/Ctrl-C collapse; Ctrl-V permits textual slash commands. Keep the existing path-prompt exception and `/test`/`/execute` alternatives.

- [ ] **Step 4: Run targeted regression tests and inspect docs**

  Run: `python -m pytest tests/test_terminal_input.py tests/test_cli_lifecycle.py tests/test_cli_slash_commands.py -q`

  Expected: PASS. Then run `git diff --check` and confirm both guides describe an inline selector and never call it a dialog, popup, or full-screen screen.

- [ ] **Step 5: Commit lifecycle coverage and documentation**

  ```bash
  git add tests/test_cli_lifecycle.py README.md AGENT_USAGE.md
  git commit -m "docs: describe inline slash mode selector"
  ```

### Task 3: Run the complete regression suite

**Files:**
- Verify only: repository test suite and working-tree status

**Interfaces:**
- Consumes: completed Tasks 1–2.
- Produces: evidence that inline selector behavior did not regress NetZoo’s CLI or non-terminal flows.

- [ ] **Step 1: Run the full suite**

  Run: `python -m pytest -q`

  Expected: all tests pass; record only pre-existing warnings separately from failures.

- [ ] **Step 2: Inspect the final diff and user-owned working-tree changes**

  Run: `git diff --check && git status --short && git log --oneline -3`

  Expected: no whitespace errors; only Task 1–2 files are committed; existing user modifications remain unstaged and untouched.

- [ ] **Step 3: Commit any necessary test-only follow-up**

  If Step 1 required a narrowly scoped regression-test adjustment, commit it with the exact affected test file. Otherwise do not create an empty commit.
