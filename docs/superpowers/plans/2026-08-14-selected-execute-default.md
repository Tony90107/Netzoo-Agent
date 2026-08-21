# Selected Execute Default Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show a reliable, muted selected `/execute` default after `/`, with typed commands replacing the selected suffix.

**Architecture:** Replace the renderer-dependent `AppendAutoSuggestion` suffix with real buffer text and a character selection. The terminal owns the selected default only; the existing slash-command handler remains the sole owner of `/execute` and `/planning` semantics.

**Tech Stack:** Python 3, pytest, prompt_toolkit.

## Global Constraints

- Pressing `/` at an empty prompt displays `/execute` once.
- `execute` is selected and muted; Enter submits `/execute`.
- Typing replaces the selected suffix, so `planning` produces `/planning` without duplication.
- No appended auto-suggestion processor remains.

---

### Task 1: Use a selected buffer default instead of an appended suggestion

**Files:**
- Modify: `scripts/netzoo_agent_core/cli/terminal_input.py`
- Modify: `tests/test_terminal_input.py`

**Interfaces:**
- Consumes: `_create_inline_mode_application(prompt: str, default_command: str)`.
- Produces: an application whose `/` key binding loads and selects the command suffix, and whose Enter binding returns the selected command or user replacement.

- [ ] **Step 1: Write the failing test**

```python
def test_slash_preloads_execute_and_selects_only_its_suffix():
    assert _dispatch_line_keys("/execute", "/planning\r") == "/planning"
    assert _dispatch_line_keys("/execute", "/execute\r") == "/execute"
```

- [ ] **Step 2: Run the focused test**

Run: `pytest tests/test_terminal_input.py -v`

Expected: FAIL because the current implementation uses an appended auto-suggestion rather than a selected buffer suffix.

- [ ] **Step 3: Implement the selected default**

Remove `AutoSuggest`, `Suggestion`, `Document`, and `AppendAutoSuggestion`. In the empty-slash key binding, set the buffer text to `default_command`, place the cursor after the slash, begin a character selection, then move the cursor to the end. Apply a muted selection style to the application. Keep Enter returning `input_field.text`.

- [ ] **Step 4: Run the focused regression tests**

Run: `pytest tests/test_terminal_input.py tests/test_cli_slash_commands.py tests/test_cli_lifecycle.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Stage `scripts/netzoo_agent_core/cli/terminal_input.py` and `tests/test_terminal_input.py`, then commit with message `fix: select inline execute default`.
