# Single-Stream CLI Activity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render one live public activity line that turns into one permanent completion, without the three-stage state-machine block.

**Architecture:** `presentation.py` normalizes current structured public events into a single active row and commits completion/failure rows. Existing graph event producers remain the source of truth; tool cards remain detailed permanent output.

**Tech Stack:** Python 3, pytest, ANSI terminal output.

## Global Constraints

- Render public facts only; never LLM rationale or private content.
- Active `●` is replaced by one `✓`, `✗`, or `?` entry.
- Do not render `Understand request`, `Match workflow capabilities`, `Choose next step`, or `Router response received` in normal mode.
- Keep tool cards unchanged.

---

### Task 1: Replace state-machine output with one active event

**Files:**
- Modify: `scripts/netzoo_agent_core/presentation.py`
- Test: `tests/test_presentation_timeline.py`

**Interfaces:**
- Produces: `_render_public_activity(event: dict) -> str` and one-row redraw behavior.

- [ ] **Step 1: Write failing tests**

```python
presentation._trace("router", "Router classification started", router_started)
assert "● Classifying requested outcome…" in capsys.readouterr().out
assert "Understand request" not in output
```

Add assertions that registry completion is one `✓ Matched workflows` row and
a clarification is exactly `? Clarification needed` plus its indented question.

- [ ] **Step 2: Run focused test**

Run: `pytest tests/test_presentation_timeline.py -k single_stream -v`

Expected: FAIL because the three-stage block is still rendered.

- [ ] **Step 3: Implement the single-stream renderer**

```python
def _set_active_activity(text: str) -> None:
    _render_or_update_progress_state(text)

def _commit_public_activity(key: str, text: str) -> None:
    _clear_active_activity()
    print(text, flush=True)
```

Map router, repair, registry, next-step, and failure facts to the approved
copy. Remove normal-mode rendering of internal state-stage labels.

- [ ] **Step 4: Run focused test**

Run: `pytest tests/test_presentation_timeline.py -k single_stream -v`

Expected: PASS.

### Task 2: Preserve tool cards and regressions

**Files:**
- Modify: `tests/test_presentation_timeline.py`

- [ ] **Step 1: Add a tool-card regression assertion**

```python
assert "Tool: run_lioness_puma" in output
assert "✓ Run LIONESS-PUMA" in output
assert "Understand request" not in output
```

- [ ] **Step 2: Run presentation tests**

Run: `pytest tests/test_presentation_timeline.py -v`

Expected: PASS.

- [ ] **Step 3: Run full suite**

Run: `pytest -q`

Expected: PASS with only existing skips or warnings.

- [ ] **Step 4: Commit**

```bash
git add scripts/netzoo_agent_core/presentation.py tests/test_presentation_timeline.py && git commit -m "feat: simplify CLI activity stream"
```
