# NetZoo Readable Verbose Timeline Design

**Date:** 2026-08-08

**Status:** Approved design; awaiting specification review

**Scope:** The `netzoo-chat` terminal interaction experience and CLI progress
rendering. This design does not change workflow selection, execution authority,
plan evaluation, tool contracts, trace persistence, or model prompting.

## 1. Objective

Make `netzoo-chat` explain its observable work before it prints the final result.
The default interaction must render a short, permanent, readable block for each
meaningful Agent phase: request understanding, planning, input validation, tool
execution, evaluation, recovery, and completion.

The experience should resemble an agent activity timeline: users can see what
the Agent is doing, which tool it selected, the concise outcome, and the
decision summary without terminal control sequences or a full-screen TUI.

The feature must not disclose private model chain-of-thought. It reports only
structured decisions, validated evidence, tool metadata, and deterministic
summaries already permitted by the Agent's contracts.

## 2. Context and constraints

The project already produces structured progress through `presentation._trace`,
and it persists a redacted, hash-chained execution trace. The current modes are:

- normal mode: compact progress, sometimes rendered as a transient status line;
- `--verbose`: full graph/evidence/evaluator/log detail;
- `--quiet`: final answer only.

The `netzoo-chat` launcher currently injects `--transient-trace`, so users do
not retain a readable account of the work once the final answer appears. Full
`--verbose` is valuable for debugging but is too noisy for default use.

The implementation must preserve:

- `--quiet` as final-answer-only output;
- `--verbose` as the full diagnostic/audit mode;
- all trace redaction, output-language, plan-gate, and tool-authority rules;
- non-interactive commands and existing exit behavior;
- compatibility with redirected stdout and ordinary terminals; and
- the user's unrelated, uncommitted work.

No third-party terminal UI dependency is needed.

## 3. Considered approaches

### 3.1 Recommended: readable, permanent timeline blocks

Add a display mode between compact and full verbose. `netzoo-chat` selects it
by default. Each event becomes a small permanent text block with a stable phase
label, an action/result line, and no more than the useful user-facing details.

Advantages:

- gives every user a reviewable explanation of Agent activity;
- avoids escape-sequence requirements and works in logs/redirected output;
- reuses existing structured events and redaction boundaries;
- keeps full audit detail opt-in through `--verbose`.

Cost: presentation needs a new renderer and carefully bounded event summaries.

### 3.2 Rejected: make the existing `--verbose` output the default

This is mechanically small, but prints evidence ledgers, graph internals,
token/memory details, and log paths for every task. It is suited to diagnosis,
not ordinary interactive use.

### 3.3 Rejected: full-screen interactive terminal UI

A TUI could provide expandable panels, but it introduces terminal-state,
accessibility, copy/paste, and CI/redirection complexity. The requested behavior
is direct text output with short blocks, so a TUI is unnecessary.

## 4. User-visible behavior

`./netzoo-chat` must print blocks as work occurs and retain them above the
final result. A successful dry-run can read as follows:

```text
[1/5] Understanding request
  Goal: Run PANDA with the supplied data.
  Decision: In-scope analysis request.

[2/5] Preparing plan
  Workflow: PANDA · Mode: dry run
  Inputs: expression, motif, and PPI supplied.

[3/5] Validating inputs
  Tool: inspect_inputs
  Result: passed.

[4/5] Preparing analysis
  Tool: run_panda
  Result: command preview ready.

[5/5] Evaluating result
  Decision: approved
  Reason: Planned steps completed successfully.

Result
...
```

The exact count is optional when a workflow can replan or add recovery steps;
the renderer may use a phase label rather than misleading totals. The renderer
must never invent a result, input, metric, or reason that is absent from the
typed state.

### 4.1 Phase mapping

| Existing structured stage | Timeline content |
| --- | --- |
| `intent` | user goal, supported/in-scope decision, concise routing reason |
| `plan` | chosen workflow, dry-run/execution mode, supplied/missing input summary |
| `input` | missing or ambiguous field and the required next response |
| `review` | evaluator approval/rejection and short typed reason |
| `tool` start | selected tool/action and operation being performed |
| `tool` completion | status plus bounded artifacts, metrics, warnings, or error summary |
| `recover` | recovery selected and why, without raw command output |
| `evaluate` | result evaluation, next workflow state, concise reason |
| `done` | completion/pause outcome; final response follows separately |

The output must label tool use explicitly, for example `Tool: inspect_inputs`
or `Tool: run_panda`. Unknown stages fall back to a safe generic block and must
not expose raw state.

### 4.2 Display-mode precedence

The three modes are mutually understandable:

| Invocation | Output |
| --- | --- |
| `./netzoo-chat` | readable permanent timeline, then final result |
| `./netzoo-chat --verbose` | current full diagnostic/audit detail, then final result |
| `./netzoo-chat --quiet` | final result only |
| direct `python scripts/netzoo_agent.py ...` without a display flag | existing compact behavior, preserving automation compatibility |

`netzoo-chat` must stop injecting `--transient-trace`; it instead requests the
new readable timeline display mode. Explicit `--verbose` and `--quiet` continue
to override it through argument validation rather than argument order.

## 5. Architecture

### 5.1 Runtime configuration

Introduce an explicit presentation-mode value owned by runtime/settings, with
three values: `compact`, `timeline`, and `verbose`. `quiet` remains a separate
trace-disable decision or is normalized to a no-output presentation mode before
rendering. The value must be passed through `configure_runtime` in the same way
as existing display flags, so graph nodes remain independent of CLI parsing.

The implementation should avoid adding a global boolean such as
`READABLE_VERBOSE_OUTPUT`; an enum-like mode prevents invalid combinations and
keeps precedence centralized.

### 5.2 Presentation renderer

`presentation._trace` remains the single public event-rendering seam for graph
nodes. It will dispatch by presentation mode:

- compact: preserve current material-progress behavior;
- timeline: render a permanent, blank-line-separated block from structured
  `stage`, `message`, and bounded `detail`;
- verbose: preserve the existing full detail output;
- disabled: render nothing.

The timeline formatter is deterministic. It parses only existing controlled
event formats and typed summaries. It must apply the existing English-output
guard to all agent-authored labels and avoid printing raw LLM responses, secrets,
full command stdout/stderr, memory payloads, or unbounded trace contents.

### 5.3 CLI and launcher

Add a display selection that lets `netzoo-chat` request timeline output while
preserving the Python CLI's current default. The launcher passes the selection
once, and the CLI rejects incompatible combinations in the same manner as the
existing display flags.

The help text and usage documentation must explain that timeline entries are
auditable activity summaries rather than private chain-of-thought. Full logs
remain available through current trace/log facilities.

## 6. Failure and edge-case behavior

- A `needs_input` plan prints a timeline block explaining what is missing, then
  the existing clarification prompt; it does not claim that execution occurred.
- Plan rejection prints the typed evaluator reason and preserves the existing
  final rejection renderer.
- Tool failure prints its action, status, bounded safe error/recovery hint, and
  any subsequent recovery block. Full stderr stays in the existing log path.
- A response-model failure after deterministic local execution leaves the
  timeline intact and uses the current deterministic final fallback.
- Non-TTY output receives the same permanent text blocks; no cursor movement,
  ANSI clearing, or timing delay is required for timeline mode.
- Trace-disabled/quiet operation emits none of the timeline blocks.

## 7. Verification

Add characterization tests that capture stdout for each mode and assert:

1. default `netzoo-chat` requests timeline mode rather than transient mode;
2. timeline mode emits permanent phase blocks in execution order;
3. tool-start and tool-completion blocks explicitly name the tool and bounded
   status;
4. timeline mode does not use terminal-clearing escape sequences;
5. `--quiet` emits no progress blocks;
6. `--verbose` retains the full current detail behavior;
7. malformed/unrecognized event detail falls back safely without raw state;
8. sensitive values and non-English agent-authored labels remain rejected or
   redacted under the existing output and trace protections.

Run the existing CLI, graph tracing, trace-redaction, and launcher tests in
addition to the new presentation tests.

## 8. Out of scope

- private or verbatim LLM chain-of-thought;
- a full-screen terminal UI, keyboard controls, or collapsible panels;
- changing OpenRouter prompts, models, provider streaming, tool authority, or
  plan/evaluator semantics;
- changing the Observer Dashboard; and
- altering persisted trace schemas except where an existing event summary is
  already available to the renderer.
