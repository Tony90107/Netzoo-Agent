# Router and Registry Progress Events

## Goal

Make the default NetZoo CLI progress display show the real work that occurs
before an answer is produced. The display must be comparable to a coding-agent
status view without exposing private model reasoning.

## Scope

The default state-machine display will surface two verifiable, pre-existing
operations:

1. Calling the Router model to classify the requested scientific outcome.
2. Comparing the classified outcome with registered workflow capabilities.

The existing tool activity display remains unchanged. It continues to show a
tool name, purpose, provided input roles, and result only when an actual tool
is executed.

## Event and display design

The graph emits structured public events at the boundaries of the two
operations. The presentation layer maps those events to its three existing
stages; it does not infer events from response wording.

During the model request, the active first stage reads:

```text
● Understand request — Calling Router to classify the requested outcome
○ Match workflow capabilities
○ Choose next step
```

When the Router returns a valid classification, the first stage is completed
with the classified outcome. Workflow matching then becomes active:

```text
✓ Understand request — miRNA regulatory network
● Match workflow capabilities — Comparing against registered workflows
○ Choose next step
```

When matching completes, compatible workflows are shown as the completed
stage detail. The next-step stage then presents either a selected action, a
clarifying question, or a no-tool result.

```text
✓ Understand request — miRNA regulatory network
✓ Match workflow capabilities — PUMA, LIONESS-PUMA
! Choose next step — Select aggregate or sample-specific
```

The output contains no prompt text, model rationale, hidden chain-of-thought,
or artificial waiting period. A Router failure is represented by the existing
error path; it must not report a successful Router completion or workflow
match.

## Implementation boundaries

- `graph/router_invocation.py` owns emitting Router start/completion facts at
  the actual provider-call boundary.
- `graph/routing_planning.py` owns emitting registry-comparison activity after
  a valid decision is available.
- `presentation.py` owns mapping these structured public facts to concise,
  terminal-width-safe state-machine lines.
- The default CLI mode stays `state_machine`; timeline and verbose modes remain
  opt-in alternatives.

## Verification

Tests will verify that:

1. Router-start events activate the understanding stage with the public Router
   activity label.
2. A successful Router result completes that stage only after a classification
   exists.
3. Registry comparison activates and completes the matching stage with actual
   matched workflow names.
4. Failed Router calls do not fabricate success or matching events.
5. Existing TTY redraw, non-TTY output, terminal-width truncation, and actual
   tool activity behavior remain intact.

