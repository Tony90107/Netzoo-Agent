# Hidden Planning Execute Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Start each interactive NetZoo Agent session in an unlabelled Planning state, enable visibly labelled execution after `/execute`, and return to Planning with typed `/test`.

**Architecture:** Keep `settings.EXECUTE_TOOLS` as the session-scoped authority flag. The CLI slash-command module translates that flag into hidden Planning or displayed Execute UX and changes it only for subsequent tasks. Simplify the terminal selector so typing `/` immediately chooses `/execute`, while a literal typed `/test` returns the session to Planning. Conversation keeps passing rendered prompts through the same command and input seams.

**Tech Stack:** Python 3, pytest, prompt_toolkit, existing NetZoo Agent CLI modules.

## Global Constraints

- A new interactive session starts with execution disabled and no Planning or TEST prefix.
- Only exact `/execute` grants execution authority, and it persists until `/test` or the Agent session ends.
- Exact `/test` returns the current session to preview-only Planning; it is documented in help but is not shown in the empty-`/` selector.
- `/test` applies only to future workflow tasks. It does not cancel analysis already in progress; Ctrl+C remains the interrupt mechanism.
- `[Execute]` uses this exact capitalization and is displayed only after execution is enabled.
- Preserve all existing path-input, graph-routing, Plan Evaluator, and Executor safeguards.
- All user-visible Agent output remains English.

---

### Task 1: Replace the visible TEST/EXECUTE toggle API with Planning/Execute presentation

**Files:**
- Modify: `scripts/netzoo_agent_core/cli/slash_commands.py:13-88`
- Test: `tests/test_cli_slash_commands.py:20-91`

**Interfaces:**
- Consumes: `settings.EXECUTE_TOOLS: bool` and `configure_runtime(EXECUTE_TOOLS: bool)`.
- Produces: `current_mode_label() -> str`, `render_mode_prompt(prompt: str) -> str`, and `handle_slash_command(...) -> SlashCommandResult` with Planning/Execute copy.

- [ ] **Step 1: Write the failing slash-command tests**

  Replace the toggle presentation test with assertions for the hidden Planning prompt and typed two-way authority commands:

  ```python
  def test_execute_and_test_change_the_session_mode_and_only_execute_is_in_the_menu():
      assert current_mode_label() == "Planning"
      assert render_mode_prompt("Question") == "Question"

      execute = handle_slash_command("/execute")
      assert execute.handled is True
      assert settings.EXECUTE_TOOLS is True
      assert current_mode_label() == "Execute"
      assert render_mode_prompt("Question") == "[Execute] Question"

      test = handle_slash_command("/test")
      assert test.handled is True
      assert "Planning mode enabled" in test.message
      assert settings.EXECUTE_TOOLS is False
      assert current_mode_label() == "Planning"
      assert render_mode_prompt("Question") == "Question"
  ```

  Update status and help assertions to require `Current mode: Planning`, `Current mode: Execute`, `/execute`, `/test`, `/status`, and `/help`. Assert the help copy says `/test` returns future workflow tasks to preview-only Planning and does not claim it can cancel work already underway.

- [ ] **Step 2: Run the focused test file to verify it fails**

  Run: `pytest tests/test_cli_slash_commands.py -v`

  Expected: FAIL because the current code reports TEST/EXECUTE, prefixes Planning prompts, and still accepts `/test`.

- [ ] **Step 3: Implement the minimal slash-command changes**

  In `slash_commands.py`:

  ```python
  _KNOWN_COMMANDS = frozenset({"/test", "/execute", "/status", "/help"})

  def current_mode_label() -> str:
      return "Execute" if settings.EXECUTE_TOOLS else "Planning"

  def render_mode_prompt(prompt: str) -> str:
      return f"[Execute] {prompt}" if settings.EXECUTE_TOOLS else prompt
  ```

  Keep `/execute` setting `EXECUTE_TOOLS=True`; make `/test` set `EXECUTE_TOOLS=False` and report Planning mode. Change status to use the new labels, and replace help copy with all four commands. Help must make clear that `/test` affects future tasks only; it must not claim the command can interrupt a running tool.

- [ ] **Step 4: Run the focused test file to verify it passes**

  Run: `pytest tests/test_cli_slash_commands.py -v`

  Expected: PASS.

- [ ] **Step 5: Commit the command-surface change**

  ```bash
  git add scripts/netzoo_agent_core/cli/slash_commands.py tests/test_cli_slash_commands.py
  git commit -m "feat: hide planning mode labels"
  ```

### Task 2: Simplify the inline slash UI to a one-command execute prompt

**Files:**
- Modify: `scripts/netzoo_agent_core/cli/terminal_input.py:10-128`
- Test: `tests/test_terminal_input.py`

**Interfaces:**
- Consumes: `MODE_MENU_OPTIONS: tuple[tuple[str, str], ...]` and `TerminalInputReader.read(prompt: str, *, menu_enabled: bool) -> str | None`.
- Produces: An empty `/` selector that submits `/execute`; no selector navigation exists. Typed literal `/test` remains available through Ctrl-V.

- [ ] **Step 1: Write failing terminal-input tests**

  Add or update tests to lock the new single-command menu contract:

  ```python
  def test_slash_selector_offers_only_execute():
      assert terminal_input.MODE_MENU_OPTIONS == (
          ("/execute", "Execute — run validated commands for this session"),
      )
      assert terminal_input._selector_lines("/execute") == [
          "▸ /execute   Execute — run validated commands for this session"
      ]
  ```

  Add a test that invokes the selector application's Enter binding after opening it with `/` and asserts the result is `/execute`; assert no up/down/tab key bindings are registered for a mode toggle. Retain the Ctrl-V dispatch test for `test`, proving a user can type `/test` even though it is not a menu row.

- [ ] **Step 2: Run the terminal-input tests to verify they fail**

  Run: `pytest tests/test_terminal_input.py -v`

  Expected: FAIL because the menu still contains `/test`, defaults based on the current mode, and binds navigation to toggle selections.

- [ ] **Step 3: Implement the one-command selector**

  In `terminal_input.py`, replace the menu and default command implementation:

  ```python
  MODE_MENU_OPTIONS = (
      ("/execute", "Execute — run validated commands for this session"),
  )

  def _default_command(self) -> str:
      return "/execute"
  ```

  Remove the `current_mode_label` import and injected `current_mode` constructor parameter. In `_create_inline_mode_application`, retain `selected="/execute"`, but delete `_toggle_selected` and the up/down/tab bindings. Pressing Enter after the menu opens must return `/execute`; Esc still closes it; Ctrl-V still inserts a literal slash.

- [ ] **Step 4: Run the terminal-input tests to verify they pass**

  Run: `pytest tests/test_terminal_input.py -v`

  Expected: PASS.

- [ ] **Step 5: Commit the terminal selector change**

  ```bash
  git add scripts/netzoo_agent_core/cli/terminal_input.py tests/test_terminal_input.py
  git commit -m "feat: make slash menu execute-only"
  ```

### Task 3: Update interactive lifecycle behavior and user documentation

**Files:**
- Modify: `scripts/netzoo_agent_core/cli/conversation.py:73-78`
- Modify: `tests/test_cli_lifecycle.py:113-171`
- Modify: `README.md:135-160`
- Modify: `AGENT_USAGE.md:634-671`

**Interfaces:**
- Consumes: `render_mode_prompt()` and `handle_slash_command()` from Task 1, plus the execute-only selector from Task 2.
- Produces: Startup, lifecycle tests, and user-facing instructions consistent with hidden Planning and session-persistent Execute.

- [ ] **Step 1: Write failing lifecycle assertions**

  In `test_main_prompt_commands_switch_mode_without_graph_or_trace`, use `interactive_answers=["/execute", "/status", "/test", "exit"]` and assert:

  ```python
  assert prompts[0].startswith("\nWhat would you like to accomplish with NetZoo?")
  assert not prompts[0].startswith("\n[")
  assert prompts[1].startswith("\n[Execute] What would you like to accomplish with NetZoo?")
  assert "Current mode: Execute" in output
  assert "Planning mode enabled" in output
  assert prompts[3].startswith("\nWhat would you like to accomplish with NetZoo?")
  assert settings.EXECUTE_TOOLS is False
  ```

  Add a new `run_cli` test that starts after an Execute-enabled lifecycle, mocks the no-op preflight and bootstrap dependencies, and asserts `configure_runtime` resets `settings.EXECUTE_TOOLS` to `False` before conversation startup.

- [ ] **Step 2: Run lifecycle tests to verify they fail**

  Run: `pytest tests/test_cli_lifecycle.py -v`

  Expected: FAIL because startup announces TEST and prompts use TEST/EXECUTE uppercase labels rather than the required hidden Planning and `[Execute]` presentation.

- [ ] **Step 3: Implement startup and documentation copy**

  Replace the interactive startup notice in `conversation.py` with:

  ```python
  "NetZoo agent started in Planning mode. Enter /help for controls, "
  "or exit or quit to stop."
  ```

  Do not add a Planning prompt prefix. In README and AGENT_USAGE, replace the two-option examples with:

  ```text
  What would you like to accomplish with NetZoo?
  > /
  ▸ /execute   Execute — run validated commands for this session
  ```

  State that the default Planning state is preview-only and unlabelled; `/execute` lasts until `/test` or the interactive session ends. Show only `/execute` in the empty-`/` selector example. Explain that Ctrl-V can be used to type `/test` to return future tasks to Planning, and that Ctrl+C is required to interrupt a currently running CLI process.

- [ ] **Step 4: Run focused lifecycle and documentation checks**

  Run: `pytest tests/test_cli_lifecycle.py -v && rg -n -i '(/test|\[test\]|test mode|choose test|switch.*test)' README.md AGENT_USAGE.md scripts/netzoo_agent_core/cli`

  Expected: lifecycle tests PASS; `rg` shows `/test` only in its new typed-command documentation and in the command handler, never as an empty-`/` menu choice or a visible `[TEST]` prompt prefix.

- [ ] **Step 5: Commit lifecycle and documentation updates**

  ```bash
  git add scripts/netzoo_agent_core/cli/conversation.py tests/test_cli_lifecycle.py README.md AGENT_USAGE.md
  git commit -m "docs: describe hidden planning execute flow"
  ```

### Task 4: Run regression checks across the affected CLI boundaries

**Files:**
- Test: `tests/test_cli_slash_commands.py`
- Test: `tests/test_terminal_input.py`
- Test: `tests/test_cli_lifecycle.py`

**Interfaces:**
- Consumes: Completed Tasks 1-3.
- Produces: Evidence that command parsing, terminal interaction, and session lifecycle satisfy the approved UX without weakening execution gates.

- [ ] **Step 1: Run the complete targeted regression suite**

  Run: `pytest tests/test_cli_slash_commands.py tests/test_terminal_input.py tests/test_cli_lifecycle.py -v`

  Expected: PASS with no skipped replacement tests.

- [ ] **Step 2: Perform a source-level safety check**

  Run: `rg -n 'configure_runtime\(EXECUTE_TOOLS=False|configure_runtime\(EXECUTE_TOOLS=True|_KNOWN_COMMANDS|MODE_MENU_OPTIONS' scripts/netzoo_agent_core/cli`

  Expected: CLI startup and typed `/test` reset execution to `False`; `/execute` is the only interactive command grant; `MODE_MENU_OPTIONS` contains only `/execute`.

- [ ] **Step 3: Commit any regression-only corrections, if needed**

  ```bash
  git add scripts/netzoo_agent_core/cli tests/test_cli_slash_commands.py tests/test_terminal_input.py tests/test_cli_lifecycle.py
  git commit -m "test: verify hidden planning execute flow"
  ```
