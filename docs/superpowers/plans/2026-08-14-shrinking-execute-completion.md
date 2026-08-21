# Shrinking Execute Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render a muted `execute` suffix that shrinks as users type `/execute`.

**Architecture:** Use prompt_toolkit's buffer-aware input processor solely for display and calculate the unmatched suffix from the current text. The Enter binding resolves a matching prefix to `/execute`; nonmatching slash commands pass through unchanged.

**Tech Stack:** Python 3, pytest, prompt_toolkit.

## Global Constraints

- `/` displays muted `execute`; `/e` displays muted `xecute`.
- No selection highlight or duplicate suffix is rendered.
- Enter accepts a matching execute prefix; `/planning` remains typed input.

---

### Task 1: Render and accept the shrinking suffix

**Files:**
- Modify: `scripts/netzoo_agent_core/cli/terminal_input.py`
- Modify: `tests/test_terminal_input.py`

**Interfaces:**
- Consumes: current input text and `default_command='/execute'`.
- Produces: a display-only suffix and a resolved Enter result.

- [ ] **Step 1: Write failing tests**

```python
assert _execute_suffix("/", "/execute") == "execute"
assert _execute_suffix("/e", "/execute") == "xecute"
assert _execute_suffix("/planning", "/execute") == ""
```

- [ ] **Step 2: Run the terminal input test file**

Run: `pytest tests/test_terminal_input.py -v`

Expected: FAIL because the selected-buffer implementation has no shrinking suffix helper.

- [ ] **Step 3: Implement the display-only processor and Enter resolution**

Remove the selected-default helper and selection style. Add a processor that appends only the unmatched case-insensitive suffix for a prefix of `/execute`. Enter returns `/execute` for any matching prefix, otherwise returns the typed text.

- [ ] **Step 4: Run targeted regressions and commit**

Run: `pytest tests/test_terminal_input.py tests/test_cli_slash_commands.py tests/test_cli_lifecycle.py -v`

Expected: PASS.

Commit `scripts/netzoo_agent_core/cli/terminal_input.py` and `tests/test_terminal_input.py` with message `fix: show shrinking execute completion`.
