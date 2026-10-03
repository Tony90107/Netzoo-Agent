"""Keep a first pass whose only schema faults leave its meaning intact (Logs 213, 215).

A first pass that does not parse leaves nothing to patch, so the second call
falls back to a whole review -- the worse path, as `OutcomeEvidence` records
(a whole review introduced a fresh issue in 71 of 83 recorded pairs). Of 903
distinct recorded first-pass payloads 6 failed the schema: 5 on an evidence
entry (an explicit entry without a quote, or a quote longer or shorter than
allowed), all of which ended in `semantic_fallback`, and 1 on `assumptions`
written beside its only hypothesis instead of inside it.

Two repairs, and nothing else:

- Evidence (Log 213). When every validation error lies inside
  `outcome_hypotheses[i].evidence[j]` and is a content rule on a well-formed
  entry -- the explicit-needs-a-quote rule (`value_error`) or a quote's length
  -- those entries are dropped and the rest is the proposal. The result is a
  payload the model could have written by leaving them out, and it meets the
  same validation: a stated field is restored from its request witness as for
  any omitted entry, any other value is reported `missing_evidence`, and the
  second call asks for exactly that (Log 198).
- Nesting (Log 215). Root-level `assumptions` of a draft with exactly one
  hypothesis are moved into it -- the equivalent nesting `SemanticReview`
  already accepts, under the same rule: never when the hypothesis carries
  different assumptions of its own, and never with several hypotheses, where
  it is unknown which one they belong to.

A malformed entry (a dimension that is not a string, a value outside the
vocabulary) and any other schema error keep the original located failure, as
the P0 malformed-payload contract requires; `SemanticInterpretation` itself is
not relaxed. Log 325 adds one narrow exception, by the user's decision: a
missing hypothesis confidence or an out-of-vocabulary `outcome.artifact_type`
becomes a placeholder in a draft that only a patch can complete
(`schema_placeholders`); the draft itself is never accepted.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from pydantic import ValidationError

from ..contracts.outcomes import SemanticInterpretation
from .schema_placeholders import placeholder_draft

__all__ = ["validate_first_pass"]

#: Errors of a well-formed entry that breaks a content rule.
_CONTENT_ERRORS = frozenset({"value_error", "string_too_long", "string_too_short"})


def _evidence_location(location: tuple) -> tuple[int, int] | None:
    if (
        len(location) >= 4 and location[0] == "outcome_hypotheses" and location[2] == "evidence"
        and isinstance(location[1], int) and isinstance(location[3], int)
    ):
        return location[1], location[3]
    return None


def _nested_assumptions(payload: Mapping) -> dict | None:
    """The payload with root `assumptions` inside its only hypothesis, if that is unambiguous."""
    hypotheses = payload.get("outcome_hypotheses")
    if (
        "assumptions" not in payload or not isinstance(hypotheses, list) or len(hypotheses) != 1
        or not isinstance(hypotheses[0], Mapping)
        or ("assumptions" in hypotheses[0] and hypotheses[0]["assumptions"] != payload["assumptions"])
    ):
        return None
    nested = {key: value for key, value in payload.items() if key != "assumptions"}
    nested["outcome_hypotheses"] = [{**hypotheses[0], "assumptions": payload["assumptions"]}]
    return nested


def _without_faulty_evidence(payload: Mapping, error: ValidationError) -> tuple[dict, list[dict]] | None:
    faults = [(_evidence_location(tuple(item["loc"])), item) for item in error.errors()]
    if not faults or any(place is None or item["type"] not in _CONTENT_ERRORS for place, item in faults):
        return None
    errors_at: dict[tuple[int, int], list[str]] = {}
    for place, item in faults:
        errors_at.setdefault(place, []).append(item["type"])
    cleaned = deepcopy(dict(payload))
    dropped = []
    # Highest index first, so earlier indexes stay valid while popping.
    for (hypothesis, entry), types in sorted(errors_at.items(), reverse=True):
        evidence = cleaned["outcome_hypotheses"][hypothesis]["evidence"]
        if entry < len(evidence):
            removed = evidence.pop(entry)
            dropped.append({
                "hypothesis": hypothesis,
                "dimension": removed.get("dimension") if isinstance(removed, Mapping) else None,
                "value": removed.get("value") if isinstance(removed, Mapping) else None,
                "errors": sorted(set(types)),
            })
    return cleaned, sorted(dropped, key=lambda item: (item["hypothesis"], str(item["dimension"])))


def validate_first_pass(payload) -> tuple[SemanticInterpretation, dict]:
    """The first-pass interpretation, and what was repaired to parse it (empty if nothing)."""
    try:
        return SemanticInterpretation.model_validate(payload), {}
    except ValidationError as error:
        if not isinstance(payload, Mapping):
            raise
        salvage: dict = {}
        candidate = _nested_assumptions(payload)
        if candidate is None:
            candidate, remaining = payload, error
        else:
            salvage["nested"] = ["assumptions"]
            try:
                return SemanticInterpretation.model_validate(candidate), salvage
            except ValidationError as still:
                remaining = still
        # Log 325: a missing confidence or an out-of-vocabulary artifact becomes
        # a placeholder the patch must write; the draft is never accepted as is.
        placed = placeholder_draft(candidate, remaining)
        if placed is not None:
            candidate, placeholders = placed
            salvage["placeholders"] = placeholders.record()
            try:
                return SemanticInterpretation.model_validate(candidate), salvage
            except ValidationError as still:
                remaining = still
        repaired = _without_faulty_evidence(candidate, remaining)
        if repaired is None:
            raise error from None
        cleaned, salvage["dropped_evidence"] = repaired
        try:
            return SemanticInterpretation.model_validate(cleaned), salvage
        except ValidationError:
            raise error from None
