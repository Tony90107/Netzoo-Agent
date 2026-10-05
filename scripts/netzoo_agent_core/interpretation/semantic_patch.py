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
    issues_for_hypothesis, permitted_fields as fields_for_issues, support_repair_pairs,
)

__all__: list[str] = []


# Patch field -> the evidence dimension that field's values are cited under.
# display_entities and unresolved_dimensions carry no evidence of their own.
_EVIDENCE_DIMENSIONS = DIMENSION_BY_FIELD

# The scalar fields that select a workflow (Log 210).
_VALIDATED_SCALARS = ("operation", "artifact_type", "granularity")


def _hold_unquoted_overrides(patch: SemanticPatch, base: RequestedOutcome, user_task: str):
    """Keep a validated first-pass scalar a tie review overturns without a quote (Log 210).

    Case 6: the first pass read aggregate co-expression and validated; the only
    issue was a tie, and the review asked to break it "re-check the original
    request for explicit ... granularity roles". It changed aggregate to
    sample_specific on an inferred rationale, which removed COBRA, the right
    answer. A change from one concrete value to another must quote the request;
    retreating to unknown or filling an unknown value is not overturning one.
    """
    from .outcome_validation import explicit_evidence_grounded

    held: list[dict] = []
    outcome = patch.outcome.model_copy()
    additions, removals = list(patch.evidence_additions), list(patch.evidence_removals)
    for field in _VALIDATED_SCALARS:
        new, old = getattr(patch.outcome, field), getattr(base, field)
        if new is None or new == old or "unknown" in (old, new):
            continue
        dimension = DIMENSION_BY_FIELD[field]
        if any(
            (item.dimension, item.value, item.source) == (dimension, new, "explicit")
            and explicit_evidence_grounded(user_task, item)
            for item in additions
        ):
            continue
        setattr(outcome, field, None)
        additions = [item for item in additions if (item.dimension, item.value) != (dimension, new)]
        removals = [item for item in removals if (item.dimension, item.value) != (dimension, old)]
        held.append({"dimension": dimension, "value": new, "field": field, "kept": old,
                     "reason": "override_of_validated_value_without_quote"})
    if not held:
        return patch, held
    return patch.model_copy(update={
        "outcome": outcome, "evidence_additions": additions, "evidence_removals": removals,
    }), held


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
    user_task: str = "",
    hold_validated: bool = False,
    validation_issues: tuple[str, ...] | None = None,
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

    `hold_validated` is set when the first pass already validated and the
    review was only asked to break a tie: a concrete scalar it changes without
    a grounded quote keeps its first-pass value (Log 210).

    Production callers pass `validation_issues`: scope is derived for this
    hypothesis alone, including exact pairs whose citations need repair.
    Scoped repairs preserve the interpretation's request mode and goal.
    """
    index = patched_hypothesis_index(proposal, patch)
    support_targets = frozenset()
    if validation_issues is not None:
        relevant = issues_for_hypothesis(validation_issues, index)
        permitted_fields = fields_for_issues(relevant)
        support_targets = support_repair_pairs(relevant)
    base = proposal.outcome_hypotheses[index]
    held: list[dict] = []
    if hold_validated:
        patch, held = _hold_unquoted_overrides(patch, base.outcome, user_task)
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
        ) is not None and (
            FIELD_BY_DIMENSION[item.dimension] in allowed
            or (item.dimension, item.value) in support_targets
        )
    }
    retired: list[dict] = list(held)
    retired.extend(
        {"field": name, "reason": "override_outside_repair_scope"}
        for name in requested if name not in allowed
    )
    if permitted_fields is not None:
        retired.extend(
            {"field": name, "reason": "override_outside_repair_scope"}
            for name in ("request_mode", "semantic_goal")
            if getattr(patch, name) is not None and getattr(patch, name) != getattr(proposal, name)
        )
    # A withdrawal of a grounded entry for a value the merged outcome still
    # asserts can only recreate `missing_evidence` for it; the citation-only
    # guard above covers the case with no licensed fields, this covers a licensed
    # field the patch left unchanged (Log 164). It is deliberately narrow, not a
    # licence to ignore removals: a withdrawal with a replacement quote for the
    # same value, or of an explicit quote the request does not contain, is
    # honoured, and so is any withdrawal for a value the patch changed.
    # A specifically rejected quote cannot simply disappear while its value
    # survives: even where evidence is optional, this would hide a failed check.
    # It must be replaced, or the licensed outcome value must change as well.
    from .outcome_validation import explicit_evidence_grounded

    added_pairs = {(item.dimension, item.value) for item in patch.evidence_additions}
    for dimension, value in sorted(withdrawn):
        field = FIELD_BY_DIMENSION.get(dimension)
        entries = [
            item for item in base.evidence
            if (item.dimension, item.value) == (dimension, value)
        ]
        if (
            field is not None
            and value in _values(getattr(outcome, field))
            and (dimension, value) not in added_pairs
            and entries
            and (
                (dimension, value) in support_targets
                or all(
                    item.source != "explicit" or explicit_evidence_grounded(user_task, item)
                    for item in entries
                )
            )
        ):
            withdrawn.discard((dimension, value))
            retired.append({"dimension": dimension, "value": value, "field": field,
                            "reason": "withdrawal_of_asserted_value"})
    evidence = []
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
    for item in patch.evidence_additions:
        field = FIELD_BY_DIMENSION.get(item.dimension)
        if (
            validation_issues is not None
            and field not in allowed
            and (item.dimension, item.value) not in support_targets
        ):
            retired.append({"dimension": item.dimension, "value": item.value,
                            "field": field, "reason": "evidence_outside_repair_scope"})
            continue
        if field is None or item.value in _values(getattr(outcome, field)):
            evidence.append(item)
            continue
        # A patch can return evidence for a field its licensed outcome patch
        # did not change. Carrying that unmatched claim creates a merge-only
        # conflict (for example, an input_artifact citation when the input field
        # was outside scope). Evidence is useful only when it supports a value
        # that survived the field-scoped merge; keep the dropped pair visible.
        retired.append({
            "dimension": item.dimension,
            "value": item.value,
            "field": field,
            "reason": "addition_does_not_match_merged_outcome",
        })

    hypothesis = OutcomeHypothesis(
        outcome=outcome,
        confidence=base.confidence if patch.confidence is None else patch.confidence,
        evidence=evidence,
        assumptions=base.assumptions if patch.assumptions is None else patch.assumptions,
    )
    # The patch adjudicates one hypothesis; the others are first-pass values
    # the review did not touch, so they are carried forward unchanged. Keeping
    # only the patched one discarded a valid reading whenever the rejection
    # was about a different hypothesis (Log 150).
    hypotheses = list(proposal.outcome_hypotheses)
    hypotheses[index] = hypothesis
    return (
        SemanticInterpretation(
            request_mode=(proposal.request_mode if permitted_fields is not None or patch.request_mode is None
                          else patch.request_mode),
            semantic_goal=(proposal.semantic_goal if permitted_fields is not None or patch.semantic_goal is None
                           else patch.semantic_goal),
            outcome_hypotheses=hypotheses,
        ),
        retired,
    )
