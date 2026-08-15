# Persistent Public Activity Log Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep completed public NetZoo work events visible while retaining a concise live current-state block.

**Architecture:** Structured Router, repair, registry, and tool lifecycle facts are normalized by the presentation layer into deduplicated activity entries. On TTYs, committed entries are printed above the redrawable state block; non-TTY output remains append-only.

**Tech Stack:** Python 3, pytest, NetZoo graph tracing, ANSI terminal rendering.

## Global Constraints

- Log only public verifiable facts; never prompts, raw LLM output, rationale, chain-of-thought, secrets, or file content.
- Do not use artificial timing delays.
- Router failure cannot produce a successful classification or workflow-match entry.
- Preserve width truncation, non-TTY rendering, and existing tool records.

---

### Task 1: Add structured Router lifecycle facts

**Files:**
- Modify: `scripts/netzoo_agent_core/graph/router_invocation.py:68-235`
- Test: `tests/test_presentation_timeline.py`

**Interfaces:**
- Produces: `{kind: "router_activity", operation: "router" | "router_repair", status: "started" | "completed" | "failed", duration_ms?: int, error_type?: str}`.
- Consumed by: presentation activity-log mapper.

- [ ] **Step 1: Write a failing lifecycle test**

```python
presentation._trace("router", "Router classification completed", {
    "kind": "router_activity", "operation": "router_repair",
    "status": "completed", "duration_ms": 6603,
})
assert "✓ Refined outcome classification (6.60s)" in capsys.readouterr().out
```

- [ ] **Step 2: Run it**

Run: `pytest tests/test_presentation_timeline.py -k router_repair -v`

Expected: FAIL because current facts have no operation or duration and no activity log exists.

- [ ] **Step 3: Emit accurate facts**

```python
detail = {
    "kind": "router_activity", "operation": "router_repair",
    "status": "completed", "duration_ms": elapsed_ms,
}
_trace("router", "Router classification completed", detail)
```

Emit the analogous `router` facts for the initial call, and a `failed` fact with only safe `error_type` after recoverable provider failures.

- [ ] **Step 4: Run it again**

Run: `pytest tests/test_presentation_timeline.py -k router_repair -v`

Expected: PASS.

### Task 2: Implement deduplicated permanent public activity rendering

**Files:**
- Modify: `scripts/netzoo_agent_core/presentation.py:20-235`
- Test: `tests/test_presentation_timeline.py`

**Interfaces:**
- Consumes: Task 1 Router facts, existing `classification`, `registry_activity`, and tool events.
- Produces: `_commit_public_activity(key: str, text: str) -> None` and a resettable per-turn set of committed keys.

- [ ] **Step 1: Write failing rendering tests**

```python
presentation._trace("router", "Router classification completed", router_completed)
presentation._trace("router", "Router classification completed", router_completed)
output = capsys.readouterr().out
assert output.count("✓ Called Router") == 1
assert "✓ Matched workflows — PUMA, LIONESS-PUMA" in output
```

Add a failure test asserting `✗ Router classification failed — TimeoutError` is permanent and does not contain workflow names.

- [ ] **Step 2: Run focused tests**

Run: `pytest tests/test_presentation_timeline.py -k 'activity_log or router_repair' -v`

Expected: FAIL because completed public states are overwritten or omitted.

- [ ] **Step 3: Add the minimal renderer**

```python
def _commit_public_activity(key: str, text: str) -> None:
    if key in _COMMITTED_ACTIVITY_KEYS:
        return
    _commit_live_progress_block()
    print(_truncate_terminal_line(text), flush=True)
    _COMMITTED_ACTIVITY_KEYS.add(key)
```

Map completed initial Router, repair Router, registry match, tool result, and
safe failure facts to distinct keys and labels. Clear the key set in
`_finalize_progress_state` so a new user turn can log the same operation type.

- [ ] **Step 4: Run focused tests**

Run: `pytest tests/test_presentation_timeline.py -k 'activity_log or router_repair' -v`

Expected: PASS.

- [ ] **Step 5: Commit implementation and tests**

```bash
git add scripts/netzoo_agent_core/graph/router_invocation.py scripts/netzoo_agent_core/presentation.py tests/test_presentation_timeline.py && git commit -m "feat: retain public CLI activity history"
```

### Task 3: Regression and terminal acceptance

**Files:**
- Test: `tests/test_presentation_timeline.py`

- [ ] **Step 1: Run targeted regression**

Run: `pytest tests/test_presentation_timeline.py -v`

Expected: PASS, including TTY, non-TTY, truncation, tool events, activity history, and deduplication.

- [ ] **Step 2: Run full test suite**

Run: `pytest -q`

Expected: PASS with only pre-existing skips or warnings.

- [ ] **Step 3: Run container acceptance**

Run: `docker compose run --rm -T netzoo python scripts/netzoo_agent.py`

Expected: A request needing router repair visibly leaves separate `Called Router` and `Refined outcome classification` entries, followed by workflow match and the live next-step status.
