# Single-Stream CLI Activity Display

## Goal

Replace the overlapping NetZoo state-machine block and activity history with
one clean, Codex-like public event stream.

## Layout

Only one live event is shown while work is active:

```text
● Refining outcome classification…
```

When it completes, the same work is committed as one permanent entry:

```text
✓ Classified requested outcome (1.18s)
✓ Refined outcome classification (6.52s)
✓ Matched workflows — PUMA, LIONESS-PUMA

? Clarification needed
  Should the result be aggregate or sample-specific?
```

The previous `Understand request`, `Match workflow capabilities`, and `Choose
next step` block is removed from normal state-machine output. `Router response
received` is not public output because it does not communicate useful work.

## Event policy

Only structured, verified router, router-repair, registry, validation, and
tool events are rendered. Active events use `●`; successful completed events
use `✓`; failures use `✗` plus a safe error type; a necessary user choice uses
`?`. Prompts, model reasoning, raw model output, secrets, and file contents
are never rendered.

Tool activity remains the existing detailed permanent card with Tool, Purpose,
Inputs, and Result. It is not duplicated as a short stream item.

## Rendering

TTY mode redraws only the one active event. Before a permanent event or final
clarification is printed, the active row is cleared. Non-TTY mode is naturally
append-only. Each lifecycle event has a stable key and can be committed once
per turn. Turn finalization clears temporary renderer state.

## Verification

Tests must prove that active Router repair displays one line, completed Router
and registry entries display once, the old three-stage labels are absent,
clarification is formatted as a two-line question, failure is safe, and tool
cards are unchanged.
