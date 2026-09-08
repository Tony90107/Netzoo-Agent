"""Merge a field-scoped review patch onto the first-pass interpretation.

The review used to return a whole replacement structure. Across 83 live
attempt-1/attempt-2 pairs it introduced an issue absent from attempt 1 in 71 of
them, and 22 of those new issues were `schema_validation` -- a class that can
never be the consequence of a correct semantic repair, only of re-typing a
structure that was already well formed. The same window shows the review fixing
2 such issues. This module keeps the review's judgement and removes the retyping.

Boundaries, all of which the merge preserves:

- No value is invented. Every carried-forward field is a value the first-pass
  model wrote itself; every changed field is a value the review wrote itself.
- Nothing is relaxed. The merged interpretation goes through the identical
  `validate_outcome_hypotheses` and `outcome_consistency_issues`.
- Completeness is untouched. A required evidence pair that neither pass supplied
  is still `missing_evidence` on the merged result.

The one deletion the merge performs on its own is stale evidence: when the patch
overrides a dimension, an evidence entry naming a value that dimension no longer
holds describes a claim the review just withdrew, and keeping it could only
raise `conflicting_evidence` about a merge artifact rather than about anything a
model asserted. Every such entry is returned so the caller can record it; none
is silently dropped.
"""
from __future__ import annotations

from collections.abc import Sequence

from ..contracts.outcomes import (
    OutcomeHypothesis, RequestedOutcome, SemanticInterpretation, SemanticPatch,
)

__all__: list[str] = []


# Patch field -> the evidence dimension that field's values are cited under.
# display_entities and unresolved_dimensions carry no evidence of their own.
_EVIDENCE_DIMENSIONS = {
    "operation": "operation",
    "input_artifacts": "input_artifact",
    "artifact_type": "artifact_type",
    "entity_types": "entity_type",
    "regulator_types": "regulator_type",
    "target_types": "target_type",
    "granularity": "granularity",
    "selection_tags": "selection_tag",
}


def _values(value) -> set[str]:
    return set(value) if isinstance(value, list) else {value}


def patched_hypothesis_index(proposal: SemanticInterpretation, patch: SemanticPatch) -> int:
    """Resolve the adjudicated hypothesis, clamped to what the proposal has."""
    return min(patch.hypothesis_index, len(proposal.outcome_hypotheses) - 1)


def evidence_only_repair(issues: Sequence[str]) -> bool:
    """Whether the rejection asked for citations and nothing else.

    `missing_evidence` says a value has no supporting entry. It does not say the
    value is wrong -- other codes do that, and say which dimension
    (`conflicting_evidence`, `artifact_granularity`, `role_entity`,
    `terminal_goal_conflict`). Asked only for citations, the review rewrote the
    whole outcome in 14 of 24 recorded patches and introduced
    `entity_types=["sample"]` on the way, which raised `role_entity` 38 times
    across 36 trials and is this study's only recorded source of a wrong tool.
    """
    return bool(issues) and all(".missing_evidence:" in issue for issue in issues)


def apply_semantic_patch(
    proposal: SemanticInterpretation,
    patch: SemanticPatch,
    *,
    evidence_only: bool = False,
) -> tuple[SemanticInterpretation, list[dict]]:
    """Return the merged interpretation and the stale evidence the patch retired.

    `evidence_only` drops the patch's outcome overrides and keeps its evidence
    changes. It is set when every issue was `missing_evidence`, so the review was
    answering a question about citations; changing values there answers a
    question nobody asked.
    """
    index = patched_hypothesis_index(proposal, patch)
    base = proposal.outcome_hypotheses[index]
    overrides = {} if evidence_only else {
        name: value
        for name, value in patch.outcome.model_dump().items()
        if value is not None
    }
    outcome = RequestedOutcome(**{**base.outcome.model_dump(), **overrides})

    withdrawn = {(item.dimension, item.value) for item in patch.evidence_removals}
    evidence = []
    retired: list[dict] = []
    for item in base.evidence:
        if (item.dimension, item.value) in withdrawn:
            continue
        field = next(
            (name for name, dimension in _EVIDENCE_DIMENSIONS.items()
             if dimension == item.dimension),
            None,
        )
        if (
            field in overrides
            and item.value not in _values(getattr(outcome, field))
        ):
            retired.append({"dimension": item.dimension, "value": item.value, "field": field})
            continue
        evidence.append(item)
    evidence.extend(patch.evidence_additions)

    hypothesis = OutcomeHypothesis(
        outcome=outcome,
        confidence=base.confidence if patch.confidence is None else patch.confidence,
        evidence=evidence,
        assumptions=base.assumptions if patch.assumptions is None else patch.assumptions,
    )
    return (
        SemanticInterpretation(
            request_mode=proposal.request_mode if patch.request_mode is None else patch.request_mode,
            semantic_goal=proposal.semantic_goal if patch.semantic_goal is None else patch.semantic_goal,
            outcome_hypotheses=[hypothesis],
        ),
        retired,
    )
