# Router and Registry Progress Events Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show real Router invocation and workflow-registry matching activity in the default NetZoo CLI state-machine display.

**Architecture:** The routing graph emits structured public progress facts at the actual Router provider-call and registry-match boundaries. The presentation layer maps those facts to its existing three stages, showing concise activity while work is in progress and factual outcomes when it completes.

**Tech Stack:** Python 3, pytest, existing NetZoo graph tracing and ANSI/non-TTY presentation code.

## Global Constraints

- Default output shows only public, verifiable events; never prompt contents, model rationale, or chain-of-thought.
- No artificial sleep or minimum-display-duration logic.
- A failed or skipped Router call must not produce Router-success or registry-match-success output.
- Existing actual-tool activity and terminal-width-safe redraw behavior remains unchanged.

---

### Task 1: Emit public Router and registry activity facts

**Files:**
- Modify: `scripts/netzoo_agent_core/graph/router_invocation.py:82-210`
- Modify: `scripts/netzoo_agent_core/graph/routing_planning.py:23-58`
- Test: `tests/test_graph_tracing.py`

**Interfaces:**
- Consumes: `_trace(stage: str, message: str, detail: str | dict | None)` from `contracts.py`.
- Produces: structured details with `kind` values `router_activity` and `registry_activity`, consumed by `_apply_public_progress_event`.

- [ ] **Step 1: Write the failing graph-tracing test**

```python
def test_classify_task_emits_router_and_registry_public_events(...):
    classify_task(context, state)
    assert ("router", "Router classification started", {
        "kind": "router_activity", "status": "started"
    }) in captured_traces
    assert ("reasoning", "Checking registered workflow capabilities", {
        "kind": "registry_activity", "status": "started"
    }) in captured_traces
```

Add a provider-error assertion that `Router classification completed` and `registry_activity/status=completed` are absent when `context.router.invoke` raises a recoverable exception.

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `pytest tests/test_graph_tracing.py -k 'router or registry' -v`

Expected: FAIL because the named structured trace events are not emitted.

- [ ] **Step 3: Emit minimal structured events at actual boundaries**

```python
_trace("router", "Router classification started", {
    "kind": "router_activity", "status": "started",
})
structured = context.router.invoke(messages)
_trace("router", "Router classification completed", {
    "kind": "router_activity", "status": "completed",
})
```

In `classify_task`, emit registry activity only after `invoke_router` returns with `reason_code == "provider"`; emit matching completion with workflow names from `classification_progress_detail`. Do not emit a completed match for a fallback or failed provider call.

- [ ] **Step 4: Run the focused test to verify it passes**

Run: `pytest tests/test_graph_tracing.py -k 'router or registry' -v`

Expected: PASS.

- [ ] **Step 5: Commit the graph events**

```bash
git add scripts/netzoo_agent_core/graph/router_invocation.py scripts/netzoo_agent_core/graph/routing_planning.py tests/test_graph_tracing.py && git commit -m "feat: trace router and registry progress events"
```

### Task 2: Render Router and registry events in the state machine

**Files:**
- Modify: `scripts/netzoo_agent_core/presentation.py:130-177`
- Test: `tests/test_presentation_timeline.py:95-174`

**Interfaces:**
- Consumes: `router_activity` and `registry_activity` facts emitted by Task 1.
- Produces: state-machine lines using the existing `ProgressState.activate` and `ProgressState.complete` methods.

- [ ] **Step 1: Write the failing presentation test**

```python
def test_state_machine_shows_router_activity_then_registry_match(...):
    presentation._trace("router", "Router classification started", {
        "kind": "router_activity", "status": "started"
    })
    presentation._trace("reasoning", "Checking registered workflow capabilities", {
        "kind": "registry_activity", "status": "started"
    })
    output = capsys.readouterr().out
    assert "● Understand request — Calling Router to classify" in output
    assert "● Match workflow capabilities — Comparing against registered workflows" in output
```

Add a failure test that a Router-error trace leaves matching pending and never shows workflow names.

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `pytest tests/test_presentation_timeline.py -k 'router_activity or registry_match' -v`

Expected: FAIL because the state-machine mapper does not recognize the facts.

- [ ] **Step 3: Map only recognized public facts**

```python
if isinstance(detail, dict) and detail.get("kind") == "router_activity":
    if detail.get("status") == "started":
        state.activate("understand", "Calling Router to classify the requested outcome")
        return True
```

Use the equivalent `registry_activity/status=started` mapping to activate matching with `Comparing against registered workflows`. Keep the existing classification fact responsible for completing understanding, and matching completion responsible for showing actual workflow names. Keep unmapped events hidden in normal state-machine mode.

- [ ] **Step 4: Run the focused test to verify it passes**

Run: `pytest tests/test_presentation_timeline.py -k 'router_activity or registry_match' -v`

Expected: PASS.

- [ ] **Step 5: Commit the presentation behavior**

```bash
git add scripts/netzoo_agent_core/presentation.py tests/test_presentation_timeline.py && git commit -m "feat: render router and registry progress"
```

### Task 3: Run regression and CLI acceptance verification

**Files:**
- Test: `tests/test_graph_tracing.py`
- Test: `tests/test_presentation_timeline.py`

**Interfaces:**
- Consumes: graph facts and state-machine mapping from Tasks 1–2.
- Produces: regression evidence and an observed default CLI transcript.

- [ ] **Step 1: Run focused regression tests**

Run: `pytest tests/test_graph_tracing.py tests/test_presentation_timeline.py -v`

Expected: PASS, including non-TTY fallback, TTY redraw, truncation, tool activity, Router activity, and registry activity tests.

- [ ] **Step 2: Run the full suite**

Run: `pytest -q`

Expected: PASS with only the repository's pre-existing skipped tests or warnings.

- [ ] **Step 3: Verify a default CLI interaction manually**

Run: `printf 'help me to find mi-RNA regulator network with the data i have currently.\nquit\n' | ./netzoo-chat`

Expected: Router activity is visible while awaiting the provider; the result contains the classified outcome, registry activity, matched workflows, and no private rationale. No local analysis tool runs for this clarification request.

