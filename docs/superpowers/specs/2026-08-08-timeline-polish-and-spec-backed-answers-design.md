# Timeline Polish and Spec-Backed Concept Answers Design

**Date:** 2026-08-08

**Status:** Approved design; awaiting specification review

**Scope:** Improve `netzoo-chat` timeline signal quality and make basic,
in-scope workflow-purpose questions reliably answerable from registered workflow
metadata. Execution authority, tool selection, workflow schemas, and persisted
trace formats remain unchanged.

## Objective

The default timeline should explain task-relevant agent work without setup noise
or misleading completion messages. Questions such as "what is the function of
PANDA" must receive an accurate answer instead of being rejected, without
hardcoding a separate Python knowledge base for every workflow.

## Timeline behavior

Timeline mode renders only recognized, task-relevant stages:

- request understanding and routing decision;
- plan creation, missing input, and plan review;
- tool start/completion, evaluation, and recovery.

It suppresses session creation/resume, policy load, memory retrieval or
consolidation, cleanup, token accounting, generic done events, and unmatched
events. Those events remain available through `--verbose` and persisted traces.
The final answer remains the natural terminal completion marker, so no separate
`[Completion]` block is rendered in timeline mode.

## Spec-backed concept answer behavior

When a no-tool, in-scope request is a basic purpose/function question that names
a registered workflow, the response layer generates a deterministic answer from
the validated `ProjectPolicySnapshot` workflow specification:

1. match the named workflow against registered workflow/action metadata;
2. state its registered description;
3. list the registered required input roles, when present; and
4. state that no files were inspected and no analysis ran.

For all other conceptual questions, retain the existing response-model path.
If that response incorrectly claims an explicitly registered workflow concept is
unsupported, use the same spec-backed answer as a safe fallback. A newly
registered workflow automatically participates through its existing workflow
metadata; no dedicated renderer or hardcoded tool-specific prose is added.

## Architecture

Keep `presentation._trace` as the event rendering seam. Its timeline renderer
may return `None` for suppressed/unrecognized stages; `_trace` then produces no
text. Verbose and compact branches retain their current behavior.

Add a focused concept-answer module under `netzoo_agent_core/interpretation/`.
It accepts the user task, typed `TaskDecision`, and validated project policy,
returning either a deterministic answer string or `None`. It must inspect only
policy metadata, not raw traces or model text.

The response node checks this result before invoking the response model for a
matching basic purpose/function question. It also applies it as a fallback only
when the model answer rejects the known concept. The renderer never authorizes
tools or turns a guidance question into execution.

## Safety and tests

- Timeline never renders unknown raw messages or details in default mode.
- `--verbose` still renders setup, token, and audit detail; `--quiet` still
  renders no progress.
- Spec-backed answers use English-only agent-authored text and bounded metadata.
- Tests cover suppression of the observed noisy events, the absence of duplicate
  completion blocks, PANDA purpose rendering from the workflow spec, a newly
  constructed policy workflow without a hardcoded branch, and the unchanged
  response-model path for non-basic questions.
