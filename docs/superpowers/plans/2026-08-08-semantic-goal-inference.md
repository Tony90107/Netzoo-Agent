# Semantic Goal Inference Implementation Plan

**Goal:** Infer registered workflow recommendations from free-text goals without hardcoded prompt-specific branches.

1. Add a typed semantic-goal contract plus registry validator; write tests for one candidate, several candidates, and unknown actions.
2. Extend Router structured output and repair/hydration to emit validated candidates, unresolved dimensions, and one clarification question.
3. Render natural timeline summaries from the validated semantic-goal record; retain verbose and quiet behavior.
4. Run focused routing/presentation tests, then `pytest -q`.
