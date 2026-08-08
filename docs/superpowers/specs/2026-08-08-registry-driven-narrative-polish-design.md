# Registry-Driven Narrative Polish Design

**Status:** Approved design; awaiting specification review

## Objective

Remove repeated ambiguity questions, internal action IDs, and generic goal
fallbacks from `netzoo-chat` while keeping all user-visible workflow names and
descriptions derived from validated registry metadata.

## Behavior

When a response has already stated the minimal clarification question, the CLI
follow-up only invites the user to provide that distinction or start a new goal;
it does not restate the question or select a candidate workflow. Timeline
summaries display registered workflow names and descriptions, not `run_*` IDs.

The semantic summary uses the validated candidate list and unresolved dimensions.
If the Router does not supply a goal label, it says that several registered
approaches fit the requested goal, rather than claiming a generic search for the
best workflow.

No UI branch names a specific workflow or biological modality. New registered
workflows participate through their existing name and description metadata.

## Verification

Tests cover multi-candidate follow-up without a continuation action, no repeated
clarification sentence, registry display names rather than action IDs, and a
generic multi-candidate summary without hardcoded workflow labels.
