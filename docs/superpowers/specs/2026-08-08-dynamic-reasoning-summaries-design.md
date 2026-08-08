# Dynamic Reasoning Summaries Design

**Date:** 2026-08-08

**Status:** Approved design; awaiting specification review

**Scope:** Replace the default `netzoo-chat` timeline's fixed status-oriented
blocks with concise, natural-language reasoning summaries. This does not expose
private model chain-of-thought or alter tool authority, workflow execution,
policy, or persisted trace contracts.

## Objective

Make the Agent feel actively intelligible: before its answer or tool result, it
should explain in natural language what it is determining, why it chose the
next action, and what it learned. The wording adapts to the task rather than
following a visibly rigid UI template.

## Model

The visible text is a public reasoning summary, not hidden chain-of-thought.
Every summary must be grounded in one of the existing validated facts:

- the user task and the typed Router/Task decision;
- the generated workflow plan and evidence ledger;
- the exact selected tool, typed tool result, and evaluation result; or
- registered workflow-policy metadata for a no-tool concept answer.

The Agent may choose natural wording, but it cannot claim that a file was read,
a tool was run, an output exists, or a conclusion was reached unless the typed
state supports it.

## Architecture

Add a small, bounded progress-summary generator at the presentation boundary.
It receives a structured event plus a sanitized, bounded fact payload and
returns one or two public sentences. The summary generator can be LLM-backed
when the provider is available, but it must have deterministic fact-preserving
fallbacks so a provider failure never delays or removes meaningful progress.

To avoid adding a model call for every graph event, the generator batches
compatible adjacent facts into a single summary and has a strict per-task token
budget. Tool events remain immediate. The current `--verbose` continues to
show raw structured audit detail; `--quiet` remains final-answer-only.

## Example

For `what is the function of PANDA`, show:

```text
I’m checking whether this is a request to run an analysis or a high-level
question about PANDA.

This only needs an explanation, so I will not inspect files or run tools. I’m
using the registered PANDA workflow description as the answer source.
```

For an execution request, show natural summaries such as:

```text
I found the required inputs and am validating identifier overlap before I
prepare the PANDA command.
```

## Guardrails

- Never display private chain-of-thought, raw prompts, raw LLM output, secrets,
  unbounded stdout/stderr, memory records, or hidden trace state.
- Summaries are English-only, bounded, and explicitly distinguish dry-run from
  execution.
- A summary cannot add tool authority; action selection stays code-enforced.
- The deterministic fallback must never claim more than the typed event.
- Summary failure is non-fatal and cannot block execution or final rendering.

## Verification

Tests must prove that summaries are generated from sanitized allowed facts;
unsupported claims and sensitive fields never appear; tool completion,
needs-input, recovery, dry-run, and no-tool concept paths each get a natural
summary; fallback behavior remains truthful; and verbose/quiet behavior remains
unchanged.
