# Clean Inline Selector Rendering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render NetZoo's inline slash mode selector without visible `^J` newline controls or a keyboard-shortcut hint row.

**Architecture:** Split a supplied conversation prompt at its final newline before creating the prompt-toolkit input control. Render the question portion as ordinary formatted terminal text above a `TextArea` whose prompt is only the final `>` segment; retain the two selector rows as the sole conditional menu content.

**Tech Stack:** Python 3.12, prompt_toolkit 3.x, pytest.

## Global Constraints

- Keep the selector non-full-screen and inline below the same active prompt.
- The `TextArea` prompt passed to prompt_toolkit must contain no newline character.
- Do not show the `↑/↓/Tab move · Enter select · Esc/Ctrl-C cancel` hint row.
- Preserve `/`, Ctrl-V, arrow, Tab, Enter, Esc, Ctrl-C, path-prompt, and non-TTY behavior.
- Only `handle_slash_command()` changes the execution mode.

---

### Task 1: Separate prompt text from the inline input control

**Files:**
- Modify: `scripts/netzoo_agent_core/cli/terminal_input.py`
- Modify: `tests/test_terminal_input.py`
- Modify: `README.md`
- Modify: `AGENT_USAGE.md`

**Interfaces:**
- Consumes: `_create_inline_mode_application(prompt: str, default_command: str)` and the existing `TextArea` selector input.
- Produces: `_split_inline_prompt(prompt: str) -> tuple[str, str]`, returning display-only prompt text and the one-line input prefix.

- [x] **Step 1: Write failing prompt-splitting and selector-copy tests**

  Add tests in `tests/test_terminal_input.py`:

  ```python
  def test_split_inline_prompt_keeps_newlines_out_of_input_prefix():
      question, input_prefix = _split_inline_prompt(
          "\n[TEST] What would you like to accomplish with NetZoo?\n> "
      )
      assert question == "\n[TEST] What would you like to accomplish with NetZoo?\n"
      assert input_prefix == "> "
      assert "\n" not in input_prefix

  def test_selector_copy_contains_only_mode_rows():
      assert _selector_lines("/test") == [
          "▸ /test      Test mode — preview commands only",
          "  /execute   Execute mode — run validated commands",
      ]
  ```

- [x] **Step 2: Run focused tests to verify failure**

  Run: `python -m pytest tests/test_terminal_input.py -q`

  Expected: FAIL because `_split_inline_prompt` and `_selector_lines` do not exist.

- [x] **Step 3: Implement normal prompt rendering and compact selector copy**

  In `scripts/netzoo_agent_core/cli/terminal_input.py`, implement:

  ```python
  def _split_inline_prompt(prompt: str) -> tuple[str, str]:
      question, separator, input_prefix = prompt.rpartition("\n")
      if not separator:
          return "", prompt
      return question + separator, input_prefix
  ```

  Build the application `HSplit` as a question `Window(FormattedTextControl(question))`, the one-line `TextArea(prompt=input_prefix)`, and the conditional selector. Generate its fragments only from `_selector_lines(state["selected"])`; remove the hint fragment. Set the static question and selector windows to `dont_extend_height=True` so they occupy only their content lines. Update both user guides to show the two rows only.

- [x] **Step 4: Run focused tests to verify success**

  Run: `python -m pytest tests/test_terminal_input.py -q`

  Expected: PASS while retaining existing real key-dispatch coverage.

- [x] **Step 5: Run targeted CLI regressions and commit**

  Run: `python -m pytest tests/test_terminal_input.py tests/test_cli_lifecycle.py tests/test_cli_slash_commands.py -q && git diff --check`

  Expected: PASS with no whitespace errors.

  ```bash
  git add scripts/netzoo_agent_core/cli/terminal_input.py tests/test_terminal_input.py README.md AGENT_USAGE.md
  git commit -m "fix: clean inline selector rendering"
  ```

### Task 2: Full regression verification

**Files:**
- Verify only: repository test suite and working-tree status

**Interfaces:**
- Consumes: Task 1’s clean inline rendering.
- Produces: proof that the selector change did not affect CLI workflows.

- [x] **Step 1: Run the full test suite**

  Run: `python -m pytest -q`

  Expected: all tests pass; document any warnings separately from failures.

- [x] **Step 2: Verify preserved user changes and commit any plan record**

  Run: `git diff --check && git status --short && git log --oneline -3`

  Expected: no whitespace errors; only plan or feature files are committed, and pre-existing user modifications remain unstaged.
