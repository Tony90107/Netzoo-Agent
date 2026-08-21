# Inline Slash Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the slash selector with an inline `/execute` completion hint that also accepts typed `/planning` commands.

**Architecture:** Keep slash-command authority in `slash_commands.py`. Change only the prompt_toolkit adapter: an empty `/` opens an inline command entry whose buffer is `/` and whose muted suffix is `execute`; Enter resolves an untouched buffer to `/execute`, while subsequent typing produces the literal slash command for the existing handler.

**Tech Stack:** Python 3, pytest, prompt_toolkit.

## Global Constraints

- The visible default completion is exactly `/execute`, with `execute` rendered as muted hint text rather than inserted into the input buffer.
- Enter on an untouched `/` submits `/execute`.
- Typing after `/` removes the completion and permits `/planning`, `/status`, `/help`, and `/execute` without Ctrl-V.
- `/planning` changes authority only for future workflow tasks; Ctrl+C remains the running-process interrupt.
- No menu row or execution-description copy is displayed.

---

### Task 1: Replace the slash selector with an inline completion input

**Files:**
- Modify: `scripts/netzoo_agent_core/cli/terminal_input.py`
- Modify: `scripts/netzoo_agent_core/cli/slash_commands.py`
- Test: `tests/test_terminal_input.py`
- Test: `tests/test_cli_slash_commands.py`
- Modify: `README.md`
- Modify: `AGENT_USAGE.md`

**Interfaces:**
- Consumes: `TerminalInputReader.read(prompt: str, *, menu_enabled: bool) -> str | None` and `handle_slash_command('/planning')`.
- Produces: `_read_menu_line(prompt: str, default_command: str) -> str` that returns `/execute` when only `/` is entered and returns a typed slash command unchanged.

- [ ] **Step 1: Write the failing tests**

```python
def test_empty_slash_shows_execute_as_a_hint_and_submits_execute():
    assert _dispatch_line_keys("/execute", "/\r") == "/execute"


def test_typed_planning_command_is_not_replaced_by_execute():
    assert _dispatch_line_keys("/execute", "/planning\r") == "/planning"
```

Replace every `/test` expectation with `/planning` in the slash-command tests, including help and mode revocation.

- [ ] **Step 2: Run focused tests to verify they fail**

Run: `pytest tests/test_terminal_input.py tests/test_cli_slash_commands.py -v`

Expected: FAIL because the handler still recognizes `/test` and the current input adapter has no completion hint.

- [ ] **Step 3: Implement the minimal change**

In `slash_commands.py`, replace `/test` with `/planning` in the known-command set, revocation branch, and help copy.

In `terminal_input.py`, keep the input buffer at `/` when the user presses `/`; render a muted `execute` suffix only while the buffer equals `/`; Enter returns `/execute` for that untouched buffer and otherwise returns the typed buffer. Remove the selector container and menu rows. Update README and AGENT_USAGE to document `/planning` and inline completion, without `/test`, Ctrl-V, or execute-description copy.

- [ ] **Step 4: Run focused regression tests**

Run: `pytest tests/test_cli_slash_commands.py tests/test_terminal_input.py tests/test_cli_lifecycle.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/netzoo_agent_core/cli/terminal_input.py scripts/netzoo_agent_core/cli/slash_commands.py tests/test_terminal_input.py tests/test_cli_slash_commands.py README.md AGENT_USAGE.md
git commit -m "feat: add inline slash command completion"
```

### Task 2: Verify the complete CLI contract

**Files:**
- Test: `tests/test_cli_slash_commands.py`
- Test: `tests/test_terminal_input.py`
- Test: `tests/test_cli_lifecycle.py`

**Interfaces:**
- Consumes: completed Task 1.
- Produces: evidence that Planning stays hidden and command authority remains session-scoped.

- [ ] **Step 1: Run the targeted regression suite**

Run: `pytest tests/test_cli_slash_commands.py tests/test_terminal_input.py tests/test_cli_lifecycle.py -v`

Expected: PASS.

- [ ] **Step 2: Run the source-level safety check**

Run: `rg -n -U 'configure_runtime\(\s*EXECUTE_TOOLS=(True|False)|_KNOWN_COMMANDS' scripts/netzoo_agent_core/cli && rg -n '/test|Ctrl-V|Execute — run validated' README.md AGENT_USAGE.md scripts/netzoo_agent_core/cli`

Expected: `/execute` is the only `True` grant; CLI startup and `/planning` set `False`; the second command emits no matches.
