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

from ..contracts.outcomes import (
    OutcomeHypothesis, RequestedOutcome, SemanticInterpretation, SemanticPatch,
)
from ..contracts.artifact_semantics import fields_opened_by_artifact
from ..contracts.repair_scope import (
    DIMENSION_BY_FIELD, FIELD_BY_DIMENSION, OUTCOME_FIELDS,
)

__all__: list[str] = []


# Patch field -> the evidence dimension that field's values are cited under.
# display_entities and unresolved_dimensions carry no evidence of their own.
_EVIDENCE_DIMENSIONS = DIMENSION_BY_FIELD


def _values(value) -> set[str]:
    return set(value) if isinstance(value, list) else {value}


def patched_hypothesis_index(proposal: SemanticInterpretation, patch: SemanticPatch) -> int:
    """Resolve the adjudicated hypothesis without changing the review's target."""
    index = patch.hypothesis_index
    if index >= len(proposal.outcome_hypotheses):
        raise ValueError("Patch requires an existing hypothesis index")
    return index


def apply_semantic_patch(
    proposal: SemanticInterpretation,
    patch: SemanticPatch,
    *,
    permitted_fields: frozenset[str] | None = None,
) -> tuple[SemanticInterpretation, list[dict]]:
    """Return the merged interpretation and the stale evidence the patch retired.

    `permitted_fields` is what the rejection licensed, collected from the rules
    that fired rather than parsed out of their codes (`contracts.repair_scope`).
    `None` permits the whole outcome, which is what happens when nothing declared
    a scope. An empty set permits none of it, and that is the citation-only case:
    `missing_evidence` says a value has no supporting entry, not that the value is
    wrong, and asked only for citations the review rewrote the whole outcome in 14
    of 24 recorded patches, introducing `entity_types=["sample"]` on the way --
    38 `role_entity` rejections across 36 trials, this study's only recorded
    source of a wrong tool.

    A review allowed to correct `artifact_type` gets the fields that artifact's
    own ontology governs, or the correction would leave a combination the
    ontology forbids. That comes from `ARTIFACT_SEMANTICS`, not from a list.
    """
    index = patched_hypothesis_index(proposal, patch)
    base = proposal.outcome_hypotheses[index]
    allowed = OUTCOME_FIELDS if permitted_fields is None else frozenset(permitted_fields)
    requested = {
        name: value
        for name, value in patch.outcome.model_dump().items()
        if value is not None
    }
    replacement = requested.get("artifact_type")
    if (
        "artifact_type" in allowed
        and replacement is not None
        and replacement != base.outcome.artifact_type
    ):
        allowed |= fields_opened_by_artifact(replacement)
    overrides = {
        name: value for name, value in requested.items() if name in allowed
    }
    outcome = RequestedOutcome(**{**base.outcome.model_dump(), **overrides})

    # A citation-only repair leaves the outcome alone, so no evidence entry can
    # have gone stale -- and a withdrawal there takes support away from a value
    # the outcome still asserts, recreating the very issue being repaired.
    # Measured: in 8 of 11 residual failures the review withdrew exactly the
    # entries attempt 2 then reported missing, `('operation', 'infer')` and
    # `('artifact_type', 'regulatory_network')`, while adding only the two role
    # entries it was asked for.
    withdrawn = {
        (item.dimension, item.value) for item in patch.evidence_removals
        if DIMENSION_BY_FIELD.get(  # the field this dimension speaks about
            FIELD_BY_DIMENSION.get(item.dimension, ""), None
        ) is not None and FIELD_BY_DIMENSION[item.dimension] in allowed
    }
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
