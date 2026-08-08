# Immediate Slash Mode Menu Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Open an arrow-key Test/Execute selector immediately when `/` is pressed in an eligible empty NetZoo terminal prompt.

**Architecture:** A new `terminal_input` adapter wraps real TTY reads and uses `prompt_toolkit` only when the menu is eligible. It returns synthetic `/test` or `/execute` text to the existing conversation control path, leaving `handle_slash_command()` as the sole runtime-authority implementation and retaining ordinary injected `input_func` behavior for tests and non-TTY runs.

**Tech Stack:** Python 3.10, `prompt_toolkit>=3.0,<4`, argparse CLI, pytest, Docker Compose.

## Global Constraints

- At an eligible empty real-TTY prompt, pressing `/` opens the selector without Enter.
- The selector has exactly two choices: `Test mode — preview commands only` and `Execute mode — run validated commands`.
- Arrow keys move, Enter selects, and Esc/Ctrl-C cancels with no mode, task, trace, graph, or pending-plan change.
- The current mode is the initial selection.
- `/test`, `/execute`, `/status`, and `/help` text commands remain supported.
- The menu is disabled for path-role clarification and path-role recommended follow-up prompts, non-TTY input, and `--task` mode.
- `/tmp`, `/output`, and `/work/data/expression.tsv` must remain valid path answers.
- `handle_slash_command()` remains the only function that changes `EXECUTE_TOOLS`.
- If TUI import or initialization fails, print one concise English notice and fall back to line input.
- Preserve all user-owned dirty changes and do not modify `docs/archive/`.

## File Map

- Create `scripts/netzoo_agent_core/cli/terminal_input.py`: isolated TTY/menu adapter and deterministic selection seams.
- Modify `scripts/netzoo_agent_core/cli/conversation.py`: use one adapter instance to read all prompts and enable the menu only outside path-role prompts.
- Modify `scripts/netzoo_agent_core/cli/__init__.py`: register the new CLI responsibility module without adding a legacy-facade export.
- Modify `environment.yml`: add pinned-major `prompt_toolkit` dependency to the container environment.
- Create `tests/test_terminal_input.py`: unit-test menu choices, key-trigger result, cancellation, fallback, and no-TTY behavior without a real terminal.
- Modify `tests/test_cli_lifecycle.py`: prove synthetic selection uses the existing slash handler and path prompts do not request the menu.
- Modify `tests/test_cli_package.py`: verify module ownership without expanding public CLI exports.
- Modify `README.md` and `AGENT_USAGE.md`: make `/` the primary mode-selection instruction and retain text commands as alternatives.

---

### Task 1: Terminal menu adapter and deterministic unit tests

**Files:**
- Create: `scripts/netzoo_agent_core/cli/terminal_input.py`
- Create: `tests/test_terminal_input.py`
- Modify: `environment.yml`
- Modify: `scripts/netzoo_agent_core/cli/__init__.py`
- Modify: `tests/test_cli_package.py`

**Interfaces:**
- Produces `TerminalInputReader(input_func: Callable[[str], str], *, is_tty: Callable[[], bool], notice: Callable[[str], None])`.
- Produces `TerminalInputReader.read(prompt: str, *, menu_enabled: bool) -> str`.
- Produces `MODE_MENU_OPTIONS: tuple[tuple[str, str], ...]` whose command values are `/test` and `/execute`.
- Consumes `current_mode_label()` and returns a synthetic text command; it must not call `configure_runtime` or `handle_slash_command`.

- [ ] **Step 1: Write failing adapter tests**

Create `tests/test_terminal_input.py` with injectable prompt and dialog seams:

```python
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.cli.terminal_input import (  # noqa: E402
    MODE_MENU_OPTIONS,
    TerminalInputReader,
)


def test_mode_menu_options_are_ordered_and_use_existing_commands():
    assert MODE_MENU_OPTIONS == (
        ("/test", "Test mode — preview commands only"),
        ("/execute", "Execute mode — run validated commands"),
    )


def test_empty_slash_trigger_opens_current_mode_menu_and_returns_selection():
    line_reader = Mock(return_value="\0NETZOO_MODE_MENU\0")
    dialog = Mock(return_value="/execute")
    reader = TerminalInputReader(
        Mock(),
        is_tty=lambda: True,
        notice=Mock(),
        menu_line_reader=line_reader,
        menu_dialog=dialog,
        current_mode=lambda: "TEST",
    )

    assert reader.read("[TEST] prompt\n> ", menu_enabled=True) == "/execute"
    dialog.assert_called_once_with("/test")


def test_cancelled_menu_returns_empty_input_without_fallback_notice():
    notice = Mock()
    reader = TerminalInputReader(
        Mock(),
        is_tty=lambda: True,
        notice=notice,
        menu_line_reader=Mock(return_value="\0NETZOO_MODE_MENU\0"),
        menu_dialog=Mock(return_value=None),
        current_mode=lambda: "EXECUTE",
    )

    assert reader.read("prompt", menu_enabled=True) == ""
    notice.assert_not_called()


def test_path_and_non_tty_prompts_use_plain_input_without_initializing_tui():
    plain_input = Mock(return_value="/output")
    menu_line_reader = Mock()
    reader = TerminalInputReader(
        plain_input,
        is_tty=lambda: False,
        notice=Mock(),
        menu_line_reader=menu_line_reader,
        menu_dialog=Mock(),
        current_mode=lambda: "TEST",
    )

    assert reader.read("path prompt", menu_enabled=True) == "/output"
    assert reader.read("path prompt", menu_enabled=False) == "/output"
    assert menu_line_reader.call_count == 0


def test_tui_failure_notices_once_then_uses_plain_input():
    plain_input = Mock(side_effect=["/status", "/help"])
    notice = Mock()
    reader = TerminalInputReader(
        plain_input,
        is_tty=lambda: True,
        notice=notice,
        menu_line_reader=Mock(side_effect=RuntimeError("terminal unavailable")),
        menu_dialog=Mock(),
        current_mode=lambda: "TEST",
    )

    assert reader.read("prompt", menu_enabled=True) == "/status"
    assert reader.read("prompt", menu_enabled=True) == "/help"
    notice.assert_called_once()
```

Add a `test_cli_package.py` assertion that `terminal_input` imports as a CLI
responsibility module while `CLI_EXPORTS` is unchanged.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
python -m pytest tests/test_terminal_input.py tests/test_cli_package.py -q
```

Expected: collection fails because `netzoo_agent_core.cli.terminal_input` does
not exist.

- [ ] **Step 3: Implement the adapter without changing execution authority**

Create `terminal_input.py` with these stable seams:

```python
MODE_MENU_TRIGGER = "\0NETZOO_MODE_MENU\0"
MODE_MENU_OPTIONS = (
    ("/test", "Test mode — preview commands only"),
    ("/execute", "Execute mode — run validated commands"),
)


class TerminalInputReader:
    def __init__(self, input_func, *, is_tty, notice, menu_line_reader=None,
                 menu_dialog=None, current_mode=current_mode_label):
        ...

    def read(self, prompt: str, *, menu_enabled: bool) -> str:
        if not menu_enabled or self._input_func is not input or not self._is_tty():
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
        selected = self._menu_dialog(self._default_command())
        return selected or ""
```

`_menu_line_reader` lazily imports `prompt_toolkit`, configures a `/` key
binding that exits with `MODE_MENU_TRIGGER` only when the current buffer is
empty, and otherwise returns normal text. `_menu_dialog(default_command)` uses
`prompt_toolkit.shortcuts.radiolist_dialog` with `MODE_MENU_OPTIONS`; it returns
the command string or `None` on Esc/Ctrl-C. The default is `/execute` only when
`current_mode_label()` returns `EXECUTE`; otherwise it is `/test`.

Do not import `prompt_toolkit` at module import time. Do not call
`configure_runtime` here. Register `terminal_input` in the package import block,
but not `_CLI_IMPLEMENTATION_MODULES` or `cli.__all__`.

In `environment.yml`, add this exact pip dependency beside other runtime Python
packages:

```yaml
      - prompt_toolkit>=3.0,<4
```

- [ ] **Step 4: Run unit tests and static package checks**

Run:

```bash
python -m pytest tests/test_terminal_input.py tests/test_cli_package.py -q
```

Expected: all pass.

- [ ] **Step 5: Commit the isolated adapter**

```bash
git add environment.yml scripts/netzoo_agent_core/cli/terminal_input.py scripts/netzoo_agent_core/cli/__init__.py tests/test_terminal_input.py tests/test_cli_package.py
git commit -m "feat: add terminal mode selector adapter"
```

---

### Task 2: Conversation integration, path gating, and lifecycle tests

**Files:**
- Modify: `scripts/netzoo_agent_core/cli/conversation.py`
- Modify: `tests/test_cli_lifecycle.py`

**Interfaces:**
- Consumes `TerminalInputReader.read(prompt, menu_enabled=...)` and the existing `_PATH_ANSWER_FIELDS`.
- Produces all current prompt input through one reader; only eligible initial/general follow-ups request the menu.
- Preserves `handle_slash_command()` as the sole mode-change function.

- [ ] **Step 1: Add failing lifecycle tests for synthetic menu commands and path gating**

Let `_fake_cli_runtime` optionally receive an `input_reader` factory or monkeypatch
`conversation.TerminalInputReader`. Add tests shaped as follows:

```python
def test_mode_menu_selection_reuses_slash_handler_without_graph_or_trace(monkeypatch, capsys):
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    reader = Mock()
    reader.read.side_effect = ["/execute", "exit"]
    monkeypatch.setattr(conversation, "TerminalInputReader", Mock(return_value=reader))
    runtime = _fake_cli_runtime(
        invoke_error=AssertionError("graph must not run"),
        interactive_answers=(),
    )

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0
    runtime.invoke_graph_turn_func.assert_not_called()
    runtime.recorder.start_run.assert_not_called()
    assert "Execution mode enabled" in capsys.readouterr().out


def test_path_clarification_disables_immediate_menu(monkeypatch):
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    reader = Mock()
    reader.read.side_effect = ["/output", "exit"]
    reader_factory = Mock(return_value=reader)
    monkeypatch.setattr(conversation, "TerminalInputReader", reader_factory)
    runtime = _fake_cli_runtime(
        invoke_error=RuntimeError("captured continuation"),
        interactive_answers=(),
    )
    runtime.pending_plan = _condor_missing_output_plan()

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0
    assert reader.read.call_args_list[0].kwargs["menu_enabled"] is False
    assert "output_dir is /output" in runtime.invoke_graph_turn_func.call_args.args[1]["messages"][-1].content
```

Extract the existing inline CONDOR plan fixture into
`_condor_missing_output_plan()` so both its existing path regression and this
test construct identical valid input. Add a complementary ordinary
recommended-follow-up test with `expected_field=None` and assert its first
`reader.read` call has `menu_enabled=True`.

- [ ] **Step 2: Run lifecycle tests and verify RED**

Run:

```bash
python -m pytest tests/test_cli_lifecycle.py -q
```

Expected: the module has no `TerminalInputReader` import and the new tests fail.

- [ ] **Step 3: Route all interactive reads through one reader**

Import `TerminalInputReader` in `conversation.py`, instantiate it once after
capturing `input_func`, and replace each `input_func(...).strip()` call with:

```python
answer = reader.read(
    render_mode_prompt(prompt_text),
    menu_enabled=menu_enabled,
).strip()
```

Use these exact eligibility rules:

```python
# preference confirmation
menu_enabled = True

# missing-input clarification
menu_enabled = target_field not in _PATH_ANSWER_FIELDS

# initial or outcome-aware main prompt
menu_enabled = next_prompt.expected_field not in _PATH_ANSWER_FIELDS
```

Keep non-interactive pending-plan handling before the reader. Do not alter
`_handle_interactive_control`; synthetic `/test` and `/execute` must flow into
it exactly like text commands. Preserve EOF and keyboard-interrupt handling.

- [ ] **Step 4: Run focused lifecycle suite**

Run:

```bash
python -m pytest tests/test_terminal_input.py tests/test_cli_lifecycle.py tests/test_cli_slash_commands.py tests/test_cli_package.py -q
```

Expected: all pass, with graph and trace still untouched by menu-selected modes.

- [ ] **Step 5: Commit conversation integration**

```bash
git add scripts/netzoo_agent_core/cli/conversation.py tests/test_cli_lifecycle.py
git commit -m "feat: open mode selector with slash key"
```

---

### Task 3: Help text, current guides, Docker smoke check, and regression suite

**Files:**
- Modify: `scripts/netzoo_agent_core/cli/slash_commands.py`
- Modify: `tests/test_cli_slash_commands.py`
- Modify: `README.md`
- Modify: `AGENT_USAGE.md`
- Verify: `Dockerfile`, `docker-compose.yml`, full pytest suite

**Interfaces:**
- Consumes the two-mode immediate menu from Tasks 1 and 2.
- Produces `/help` text that names `/` as the primary selector and documents text commands as alternatives.

- [ ] **Step 1: Update failing help/documentation assertions**

Extend `test_status_and_help_report_without_changing_mode`:

```python
assert "Press / at an empty prompt to choose Test or Execute mode." in help_result.message
assert "Text alternatives:" in help_result.message
```

Add a README/guide text assertion only if the project has an existing markdown
test location; otherwise use the explicit `rg` audit in Step 4.

- [ ] **Step 2: Run focused slash tests and verify RED**

Run:

```bash
python -m pytest tests/test_cli_slash_commands.py -q
```

Expected: the new `/help` assertion fails.

- [ ] **Step 3: Update help and current operating examples**

In `slash_commands.py`, prepend this exact help content before the text-command
list:

```python
"Press / at an empty prompt to choose Test or Execute mode.\n"
"Text alternatives:\n"
```

In `README.md` and `AGENT_USAGE.md`, replace the primary execution transcript
with:

```text
[TEST] What would you like to accomplish with NetZoo?
> /
Select NetZoo mode
❯ Test mode — preview commands only
  Execute mode — run validated commands

↑/↓ move · Enter select · Esc cancel
```

Then explain that `/execute` and `/test` remain typed alternatives, and that
path prompts intentionally do not open the menu so absolute paths can be typed.
Do not alter archived documents.

- [ ] **Step 4: Run focused tests and documentation audits**

Run:

```bash
python -m pytest tests/test_terminal_input.py tests/test_cli_lifecycle.py tests/test_cli_slash_commands.py tests/test_cli_package.py tests/test_netzoo_chat_launcher.py -q
```

Expected: all pass.

Run:

```bash
rg -n "Press / at an empty prompt|Text alternatives|↑/↓ move|absolute paths" README.md AGENT_USAGE.md scripts/netzoo_agent_core/cli/slash_commands.py
```

Expected: current help and both guides contain the immediate-menu and path-safety
instructions.

- [ ] **Step 5: Verify the Docker dependency and end-to-end regression**

Run:

```bash
docker compose build
docker compose run --rm netzoo python -c 'import prompt_toolkit; print(prompt_toolkit.__version__)'
python -m pytest -q
```

Expected: Docker build succeeds, the container imports `prompt_toolkit`, and the
full Python suite passes. If an official-toy fixture is absent in an isolated
worktree, use the existing test-only symlink procedure and remove it before
checking status.

- [ ] **Step 6: Commit help and documentation**

```bash
git add README.md AGENT_USAGE.md scripts/netzoo_agent_core/cli/slash_commands.py tests/test_cli_slash_commands.py
git commit -m "docs: explain slash mode selector"
```
