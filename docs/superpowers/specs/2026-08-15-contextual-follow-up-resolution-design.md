# Contextual Follow-up Resolution Design

## Problem

After an informational NetZoo answer, the interactive CLI currently asks a generic
yes-or-no-shaped follow-up question. A short acknowledgement such as `yes` is then
submitted as a new scientific task. The Router intentionally sees only the latest
user message, so it cannot recover the prior conversational intent and may produce
an unrelated workflow clarification.

The guidance response also has split ownership of operational status. The response
LLM is instructed to mention that nothing ran, while deterministic response code
appends the same status. This can produce duplicate status paragraphs and an extra
LLM-authored call to action before the CLI's own next-turn prompt.

## Goals

- Resolve follow-up replies using bounded prior-turn context rather than language-
  specific checks for `yes`, `ok`, or equivalent acknowledgements.
- Keep scientific capability matching and execution authorization deterministic.
- Prevent an underspecified acknowledgement from entering the scientific Router.
- Preserve context for substantive follow-up questions and distinguish them from new
  goals or explicit workflow acceptance.
- Render operational status exactly once and keep next-turn navigation owned by the
  CLI.

## Non-goals

- General long-term conversational memory.
- Allowing the reply resolver to select or authorize tools.
- Passing prior free-form assistant output into the Router.
- Automatically starting a workflow from a generic acknowledgement when the prior
  prompt did not explicitly offer a concrete continuation.

## Architecture

### Structured interaction context

After each completed turn, the CLI retains a bounded, trusted context envelope:

- the prior user goal;
- the prior prompt kind and question;
- code-validated matched or recommended workflow actions;
- the concrete continuation action, when one was explicitly offered;
- the current user reply.

The envelope is derived from structured graph state and `NextTurnPrompt`, not from
the prior assistant prose. This avoids treating generated text as workflow authority
or exposing the Router to unnecessary historical content.

### Contextual reply resolver

A small structured-output LLM classifier resolves non-initial replies into one of:

- `follow_up`: a substantive question that depends on the prior goal;
- `new_goal`: a self-contained new NetZoo request;
- `accept_workflow`: acceptance of an explicitly offered concrete continuation;
- `needs_detail`: an acknowledgement or fragment that does not contain enough intent
  to route safely;
- `navigation`: a request to return to the main prompt or leave the interaction.

The resolver returns a bounded reason and, for `follow_up` or `new_goal`, a resolved
task. It interprets language but has no authority to add workflow actions. For a
follow-up, the resolved task includes only the minimum trusted context needed to make
the scientific request self-contained. An `accept_workflow` result is valid only when
the context envelope contains a concrete continuation action; otherwise it is reduced
to `needs_detail`.

Existing explicit CLI controls remain deterministic and are processed before the LLM
resolver. If the resolver is unavailable or returns invalid output, the safe fallback
is `needs_detail`, not a Router call or workflow execution.

### Conversation flow

1. The initial request goes directly to the existing scientific Router.
2. The response is rendered and the CLI creates a structured next-turn prompt.
3. A subsequent reply and the trusted context envelope go to the contextual reply
   resolver.
4. `needs_detail` produces a concise prompt asking for the actual follow-up question,
   input files, or new goal, without invoking the scientific Router.
5. `follow_up` and `new_goal` produce self-contained tasks for the existing Router.
6. `accept_workflow` uses the already validated continuation action and enters the
   existing input-collection path; it never executes a tool merely because the reply
   is affirmative.
7. `navigation` uses the existing CLI navigation behavior.

The default next-turn wording is imperative rather than yes-or-no-shaped, for example:
"Enter a follow-up question, provide the required input files, or describe another
NetZoo goal."

## Response ownership

The response LLM owns the scientific explanation only. Its prompt explicitly excludes:

- operational status such as whether files were inspected or tools ran;
- invitations to continue;
- next-turn questions.

For guidance turns with no results, deterministic response code appends exactly one
canonical footer: `No files were inspected and no analysis ran.` The CLI separately
renders exactly one next-turn prompt. The existing response-tail normalization remains
a defense against model-generated navigation text, but the prompt and renderer no
longer assign the same responsibility to two components.

## Safety constraints

- The contextual resolver cannot name an action that was absent from the trusted
  context envelope.
- An inferred acceptance cannot bypass missing-input validation, confirmation gates,
  execution mode, or the allow-listed workflow registry.
- Prior assistant prose is untrusted and is excluded from action authorization.
- Low-confidence, invalid, or unavailable reply resolution asks for detail instead of
  guessing.
- The scientific Router continues to receive a bounded, self-contained latest task.

## Public test seams

Tests exercise behavior through two public seams:

1. The contextual reply-resolution interface, using structured context and a fake
   structured-output model. It must classify semantically equivalent acknowledgements
   without enumerating phrases, preserve substantive follow-ups, distinguish new goals,
   and reject workflow acceptance when no continuation was offered.
2. The interactive conversation loop, using its injected reader and graph invocation
   function. It must prove that `needs_detail` does not invoke the scientific graph,
   that a substantive follow-up reaches the graph as a self-contained task, and that
   explicit continuation still uses the existing validation path.

Response tests additionally verify that a guidance answer contains one canonical
operational footer and no model-owned next-turn invitation.

## Success criteria

- A bare or semantically underspecified acknowledgement after an informational answer
  asks for a concrete follow-up and does not display scientific workflow ambiguity.
- The behavior works across languages and paraphrases without an affirmative phrase
  allow-list.
- A real follow-up question retains the necessary prior goal context.
- A new self-contained goal is routed independently.
- Explicit acceptance can continue only a workflow that the prior prompt actually
  offered.
- The sample-specific miRNA guidance answer recommends the PUMA to LIONESS-PUMA
  composition, contains one operational footer, and exposes one CLI-owned next step.
- Existing workflow safety, routing, and full-suite tests remain green.
