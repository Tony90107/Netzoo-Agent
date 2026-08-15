# CLI State-Machine Progress Design

## Goal

Replace the current stream of independent timeline messages with a compact,
stateful progress display that shows verifiable agent activity while a request
is running. The normal CLI view should make the current stage obvious, retain a
short audit trail after completion, and never expose model chain-of-thought.

## User experience

The normal progress display has three task-level stages:

```text
✓ Understand request
● Match workflow capabilities
○ Choose next step
```

The active stage uses `●`; incomplete stages use `○`; completed stages use
`✓`. A stage that requires a user decision uses `!` and includes only its
public, validated reason, for example `! Choose next step — clarification
required`.

Stages are updated in place when the terminal supports ANSI cursor movement.
Once a final answer, an input request, or a terminal failure is reached, the
final state-machine block remains visible above the answer. Non-TTY output
falls back to one concise, permanent state line per changed stage.

## Verifiable activity

Only graph events that correspond to a public action or a deterministic,
public decision may update the state machine. The display may show:

- request classification completion;
- registered-capability matching completion;
- selection of a next action or an input clarification;
- started and completed input-validation or execution tools;
- bounded public result summaries.

It must not display raw prompts, hidden reasoning, private state, memory
contents, provider payloads, or a tool invocation that did not occur.

Actual tools appear beneath the state list as permanent event blocks:

```text
● Run LIONESS-PUMA
  Tool: run_lioness_puma
  Input: expression.tsv, motif.tsv, ppi.tsv, mirna.txt
```

Completion replaces the activity marker with `✓` and adds a bounded result
summary. Paths and values continue to use existing output-safety rules.

## Presentation modes

- Default interactive mode uses the state-machine display.
- `--timeline` remains a compatible alias for permanent event blocks during
  the transition; it does not reveal extra private information.
- `--verbose` retains the existing detailed evidence ledger and graph events.
- `--quiet` prints no progress output.
- Non-interactive streams retain deterministic, line-oriented output suitable
  for logs and tests.

## Architecture

`presentation.py` owns a small state model and terminal renderer. It accepts
existing `_trace(stage, message, detail)` events, maps only recognized public
events to one of the three task-level stages, and redraws the block only when a
stage changes. Tool start/completion events are rendered as separate,
permanent, fact-grounded records rather than as simulated reasoning.

The graph and routing layers continue emitting their existing event taxonomy;
this feature changes presentation, not routing authority, workflow selection,
or tool execution. Tests cover state transitions, TTY redraw behavior,
non-TTY fallback, terminal finalization, and suppression of unknown/private
events.

## Error handling

If an event is not recognized as public, it is ignored in normal mode. If
terminal cursor control is unavailable, the renderer emits compact permanent
lines rather than ANSI sequences. A failed tool marks its corresponding stage
as failed and preserves the existing safe recovery/final-answer path.

## Acceptance criteria

1. During a normal interactive request, exactly one task-level stage is active
   until the request finishes or needs input.
2. The final state list remains visible before the answer or clarification.
3. Tool records appear only for tool start/completion events actually emitted
   by the graph.
4. Default output contains no raw model reasoning or private graph payload.
5. `--verbose`, `--quiet`, and non-TTY behavior remain compatible with their
   existing purposes.
