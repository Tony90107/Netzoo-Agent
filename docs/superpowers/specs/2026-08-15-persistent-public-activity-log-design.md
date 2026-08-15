# Persistent Public Activity Log

## Goal

Make the default NetZoo CLI show both the current operation and a permanent,
compact history of completed work, comparable to the public activity entries
shown by coding agents.

## Display model

The output has two layers:

1. A transient three-stage `ProgressState` block at the bottom, showing what
   is currently running.
2. An append-only activity log above it. Completed public work is committed to
   this log and is never removed during the turn.

For example:

```text
✓ Called Router — classified requested outcome (1.35s)
✓ Refined outcome classification (6.60s)
✓ Matched workflows — PUMA, LIONESS-PUMA
● Preparing next-step question
```

Only the bottom current-state block is redrawn on an interactive TTY. On
non-TTY streams, both activity and current state are emitted as ordinary,
append-only text.

## Public event policy

The activity log accepts only structured, verifiable events from existing
application boundaries:

- Router provider call started, completed, or failed.
- Router repair call started, completed, or failed; this is labelled
  `Refined outcome classification` rather than a second indistinguishable
  Router call.
- Deterministic comparison against registered workflow capabilities.
- Input/file validation and actual local tool execution, including result.
- Final next-step preparation where no tool is run.

Entries must be derived from event fields, timing measurements, matched
workflow names, tool names, input roles, or safe error types. They must never
include user prompts, raw model responses, model rationale, hidden
chain-of-thought, secrets, or file contents.

## Event lifecycle

An operation starts by updating `ProgressState`; it does not create a permanent
history entry yet. On completion or failure, the presentation layer commits
one log entry and updates the active state. Repeated redraw calls must not
commit the same event twice.

For Router calls, structured activity details include a stable operation id,
kind (`router` or `router_repair`), status, and duration in milliseconds when
known. The initial Router call and repair call are independently visible. A
failed Router call is logged with a safe error type and must not cause a
successful classification or workflow-match log entry.

## Boundaries

- `graph/router_invocation.py` emits structured lifecycle events at the two
  actual provider call boundaries.
- `graph/routing_planning.py` emits structured workflow-match completion facts
  after a valid, provider-derived decision is available.
- `presentation.py` owns deduplication, current-state rendering, and permanent
  activity-log rendering. It does not inspect private LLM data.
- Existing tool activity cards remain public permanent entries and should be
  made visually consistent with the activity log rather than duplicated.

## Verification

Tests will prove that the default renderer:

1. Keeps completed Router, repair, workflow-match, and tool events visible.
2. Labels a repair separately from the initial Router call.
3. Emits each completed event exactly once despite repeated redraws.
4. Does not fabricate a completion or match after a Router failure.
5. Preserves current TTY redraw, non-TTY safety, width truncation, and tool
   activity behavior.
