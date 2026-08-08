# Semantic Goal Inference Design

**Status:** Proposed for implementation

## Goal

Allow the Agent to infer a user's biological/network-analysis goal from free
text, recommend only registered workflows, explain that inference naturally,
and ask one minimal clarification when a safe single recommendation is not yet
possible.

## Design

The Router produces a typed semantic goal record: `goal`, `intent`, candidate
registered actions, known constraints, unresolved decision dimensions, and a
bounded public rationale. Python validates every candidate against the workflow
registry and removes unknown actions. A single validated candidate can become a
recommendation; several candidates produce a clarification; no candidates uses
the existing unsupported path.

The public reasoning summary is generated from the validated record, not raw
LLM reasoning. It says what goal was inferred, what registered approaches fit,
and what specific distinction is required when ambiguous. It never claims a
tool ran or creates new authority.

## Example

For a request for a sample-specific regulator network, the record can identify
sample-specific regulatory-network inference, return registered LIONESS-based
candidates, and state that the regulator modality is still needed before
selecting a single workflow. The wording is not tied to this example; the same
record supports future workflows registered in policy metadata.

## Verification

Tests cover an unambiguous semantic goal, a multi-candidate clarification, an
unknown candidate rejected by registry validation, and public summaries that
contain only validated facts.
