# Registry-Driven Narrative Polish Implementation Plan

**Goal:** Make multi-candidate reasoning and clarification concise, non-repetitive, and registry-driven.

1. Add tests for display names, generic multi-candidate summary, and clarification-only follow-up.
2. Pass validated candidate display metadata to timeline summaries.
3. Suppress duplicate clarification wording in CLI follow-up while preserving no-continuation safety.
4. Run `pytest -q` and commit.
