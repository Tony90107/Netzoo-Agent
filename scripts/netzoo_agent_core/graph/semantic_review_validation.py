"""Strict decoding helpers for semantic review and patch payloads."""

from __future__ import annotations

from collections.abc import Mapping
from typing import get_args

from pydantic import ValidationError

from ..contracts.outcomes import (
    EvidenceDimension,
    SemanticPatch,
    SemanticReview,
)


#: The closed vocabulary a removal instruction must name to mean anything.
_EVIDENCE_DIMENSIONS = frozenset(get_args(EvidenceDimension))


def _honourable_removals(payload) -> tuple[object, list[dict]]:
    """Set aside evidence-list instructions that cannot be carried out.

    Two shapes cost the whole repair -- including the well-formed additions that
    were the repair -- for the sake of one instruction that could never have had
    an effect. Both were the entire residual of a matched-control round: 5 trials
    of the first and 6 of the second, out of 14 failures in 36.

    A removal names one (dimension, value) to withdraw. When its `dimension` is
    outside the closed vocabulary, or its string value is blank, it names nothing
    that can exist in the evidence list. Honouring it and ignoring it are therefore
    the same act -- while rejecting the patch over it is not. Only removals are
    treated this way: a malformed *addition* is the repair itself failing, and
    stays strict.

    The second shape is the same list at the root and nested inside `outcome`
    with different contents. The nesting is an accommodation for a provider that
    puts it there, not a second source of truth, so when the two disagree the
    field the contract declares is the one it meant. `SemanticPatch` still
    raises on anything this has not set aside.

    Nothing is dropped silently: what was set aside is returned for the caller
    to record beside the patch it applied.
    """
    if not isinstance(payload, Mapping):
        return payload, []
    normalized, ignored = dict(payload), []
    nested = normalized.get("outcome")
    if isinstance(nested, Mapping):
        nested = dict(nested)
        for field in ("evidence_additions", "evidence_removals"):
            if field in nested and field in normalized and normalized[field] != nested[field]:
                ignored.append({"reason": "nested_list_disagreed", "field": field})
                nested.pop(field)
        normalized["outcome"] = nested
    removals = normalized.get("evidence_removals")
    if isinstance(removals, list):
        kept = []
        for item in removals:
            dimension = item.get("dimension") if isinstance(item, Mapping) else None
            if isinstance(item, Mapping) and dimension not in _EVIDENCE_DIMENSIONS:
                ignored.append(
                    {
                        "reason": "removal_names_no_dimension",
                        "field": "evidence_removals",
                    }
                )
                continue
            value = item.get("value") if isinstance(item, Mapping) else None
            if isinstance(value, str) and not value.strip():
                ignored.append(
                    {
                        "reason": "removal_names_no_value",
                        "field": "evidence_removals",
                    }
                )
                continue
            kept.append(item)
        normalized["evidence_removals"] = kept
    return normalized, ignored


def _as_semantic_patch(payload) -> tuple[SemanticPatch | None, list[dict]]:
    """Return the payload as a patch, or None when it is a whole review.

    `SemanticPatch` and `SemanticReview` are structurally disjoint: a review must
    carry `outcome_hypothesis`, which the patch forbids, and a patch's root
    `outcome` is not a review field. Accepting whichever arrived relaxes nothing
    -- both go through the identical `validate_outcome_hypotheses` afterwards --
    and it keeps a provider that answers with a complete structure working
    instead of turning its reply into a decoding failure.
    """
    prepared, ignored = _honourable_removals(payload)
    try:
        return SemanticPatch.model_validate(prepared), ignored
    except ValidationError:
        return None, ignored


def _validated_review(payload, *, patching: bool) -> SemanticReview:
    """Parse a whole-review reply, reporting against the contract we asked for.

    A reply that is neither shape must not be described by the review's missing
    fields when the call requested a patch: the diagnostics would name a contract
    this attempt never used, and a live round observed exactly that -- a patch
    reply reported as `outcome_hypothesis:missing`.
    """
    try:
        return SemanticReview.model_validate(payload)
    except ValidationError:
        if patching:
            SemanticPatch.model_validate(payload)
        raise
