# LLM-Owned Guidance Response Design

**Status:** Approved direction; written for implementation review

## Goal

Make NetZoo guidance answers respect explicit user constraints and let the response
LLM decide whether clarification is necessary and how to phrase the answer. Keep
deterministic code responsible for registry validation, input safety, and execution
authorization, but not for ordinary conversational wording.

The motivating request is:

```text
if i want to get sample specific mi-RNA network data, what tools do i need?
```

This request already supplies sample-specific granularity. The Agent must not ask
whether the result should be aggregate or sample-specific. It should explain the
validated `PUMA → LIONESS-PUMA` composition, without inspecting files or running an
analysis.

## Current Failure

The Router repair can return competing hypotheses even when one contradicts an
explicit user constraint. In the saved failing session it returned:

- a sample-specific regulatory-network hypothesis with confidence `0.9`;
- an aggregate regulatory-network hypothesis with confidence `0.8`, incorrectly
  labelling aggregate granularity as explicit evidence.

The deterministic matcher then treats both candidates as advisory because the
sample-specific hypothesis contains an unrelated assumption about input files. The
matcher does not use hypothesis confidence to break the tie. Since the outcomes vary
only by granularity, it creates the fixed question `Should the result be aggregate or
sample-specific?`.

The response graph renders that fixed clarification and returns immediately. The
response LLM is never called. A second deterministic extractor also interprets the
ordinary phrase `network data` as `network_file="data"` even though no path was
provided.

## Considered Approaches

### 1. Fully deterministic clarification and response templates

Keep the current matcher and add more rules that recognize `sample-specific`, miRNA,
and similar wording. This is rejected because every new paraphrase or language would
need another rule, and the deterministic layer would continue owning semantic
conversation decisions.

### 2. Fully LLM-controlled routing, validation, and response

Let one model select workflows, decide whether to execute, and write the answer. This
is rejected because model output must not be able to invent workflow authority,
bypass required inputs, or authorize execution.

### 3. LLM-owned conversation with deterministic capability validation

This is the selected design. The Router LLM interprets the request into structured
outcome hypotheses. Deterministic code validates those hypotheses against the
registered workflow catalog and exposes only valid action identifiers and capability
facts. The response LLM receives the original latest user request plus that trusted
state and decides how to explain the result or whether a clarification is genuinely
needed. Deterministic code retains all execution gates.

## Architecture

### Routing and validation

The Router continues to return structured hypotheses and evidence. The capability
matcher continues to compute exact, advisory, and unsupported workflow relationships
from registry-owned definitions. Its result is trusted capability context, not final
conversation copy.

For guidance and ambiguous outcomes, the matcher may report candidates and unresolved
dimensions, but it must not construct the final user-facing clarification sentence.
The original request remains available to the response LLM so it can see that
`sample-specific` was already stated.

No advisory or ambiguous result can authorize planning or execution. Only an exact
registered match plus the existing direct-execution, input, Plan Evaluator, and
session-mode gates can reach the Executor.

### Response generation

The response graph must not early-return a deterministic outcome-clarification or
concept-guidance paragraph. Instead it builds trusted context containing:

- the validated `TaskDecision`;
- registered descriptions for exact, advisory, and alternative workflow actions;
- workflow predecessor relationships, such as `PUMA → LIONESS-PUMA`;
- the workflow plan and evaluation state;
- the original latest user request.

The response prompt instructs the model to:

1. answer the user's actual question directly;
2. treat explicit user constraints as settled unless they conflict internally;
3. never ask for a value that the user already supplied;
4. distinguish aggregate predecessor workflows from the requested final granularity;
5. ask only the smallest unresolved scientific question;
6. use only validated workflow names and capability facts from trusted context;
7. state accurately that no files were inspected and no analysis ran when applicable.

Deterministic responses remain appropriate for safety and state-machine outcomes such
as missing required inputs, preference confirmation, rejected plans, completed tool
execution, and provider failure fallback. These report code-owned facts rather than
interpret user meaning.

### Path extraction

An input alias followed by an ordinary noun is not sufficient evidence of a path.
The file-role-aware `_task_path()` layer must accept `_extract_named_path()` output
only when the captured value is path-like or the alias is explicitly bound to a
value. Keeping that check at `_task_path()` preserves the generic named-value parser
used for non-file fields such as `prefix`. Natural-language phrases such as `network
data`, `miRNA network data`, and `expression data` must not populate file fields.

Existing explicit forms must continue to work, including:

```text
network_file=data/network.tsv
network: data/network.tsv
use data/network.tsv as the network
```

## Data Flow

```text
latest user request
  → Router LLM: structured hypotheses and evidence
  → deterministic registry matcher: valid capability facts and execution status
  → response LLM: direct answer or minimal necessary clarification
  → CLI

exact executable request
  → existing input validation
  → Plan Evaluator
  → current-session execution authorization
  → Executor
```

## Error Handling

- If the response LLM fails, use a deterministic fallback that reports the validated
  candidate workflow names and failure state without inventing a clarification.
- If the Router fails, preserve the existing fail-closed `no_tool` behavior.
- If the Router supplies contradictory hypotheses, expose the contradiction to the
  response LLM as untrusted interpretation alongside the original request; do not let
  it expand execution authority.
- Invalid or unknown action identifiers are omitted from trusted workflow context.
- Response generation failure never triggers workflow execution.

## Test Seams

Tests use public behavior at two seams:

1. **Graph response seam:** given a validated ambiguous or guidance `TaskDecision`,
   `respond()` invokes the response model with the original request and validated
   workflow context instead of returning fixed clarification copy. The resulting CLI
   answer must not repeat a granularity question when the supplied response model
   resolves the explicit sample-specific constraint.
2. **Task hydration seam:** hydrating the motivating request leaves
   `network_file=None`; explicit network paths continue to populate it.

Unit tests may separately verify that the trusted response context includes advisory
workflow specifications, but they must not assert an exact natural-language answer.

## Acceptance Criteria

1. The motivating request reaches the response LLM rather than a deterministic
   clarification renderer.
2. The answer identifies the validated `PUMA → LIONESS-PUMA` composition and does
   not ask aggregate versus sample-specific again.
3. No file inspection or analysis runs for this guidance request.
4. `network data` does not become `network_file="data"`.
5. Explicit file paths are still extracted.
6. Ambiguous guidance cannot authorize execution.
7. Provider-failure, plan-rejection, missing-input, and execution-result fallbacks
   remain deterministic and safe.
8. Focused routing, response, CLI, and path-safety tests pass, followed by the full
   test suite.
