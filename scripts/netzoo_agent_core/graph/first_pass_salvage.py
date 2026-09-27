"""Keep a first pass whose only schema faults are individual evidence entries (Log 213).

A first pass that does not parse leaves nothing to patch, so the second call
falls back to a whole review -- the worse path, as `OutcomeEvidence` records
(a whole review introduced a fresh issue in 71 of 83 recorded pairs). Of 903
distinct recorded first-pass payloads 6 failed the schema and 5 of those ended
in `semantic_fallback`; every fault but one was an evidence entry: an explicit
entry without a quote, or a quote longer or shorter than allowed.

When every validation error lies inside `outcome_hypotheses[i].evidence[j]`
and is a content rule on a well-formed entry -- the explicit-needs-a-quote
rule (`value_error`) or a quote's length -- those entries are dropped and the
rest -- the outcome and all other evidence the model wrote -- is the proposal.
A malformed entry (a dimension that is not a string, a value outside the
vocabulary) stays a located schema failure, as the P0 malformed-payload
contract requires. Nothing is invented and nothing relaxed: the result is a
payload the model could have written by leaving those entries out, and it
meets the same validation -- a stated field is restored from its request
witness as for any omitted entry, any other value is reported
`missing_evidence`, and the second call asks for exactly that (Log 198).
Any other schema error keeps the original failure.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from pydantic import ValidationError

from ..contracts.outcomes import SemanticInterpretation

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


def validate_first_pass(payload) -> tuple[SemanticInterpretation, list[dict]]:
    """The first-pass interpretation, and the evidence entries dropped to parse it."""
    try:
        return SemanticInterpretation.model_validate(payload), []
    except ValidationError as error:
        faults = [(_evidence_location(tuple(item["loc"])), item) for item in error.errors()]
        if (
            not isinstance(payload, Mapping) or not faults
            or any(place is None or item["type"] not in _CONTENT_ERRORS for place, item in faults)
        ):
            raise
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
        try:
            return SemanticInterpretation.model_validate(cleaned), sorted(
                dropped, key=lambda item: (item["hypothesis"], str(item["dimension"])),
            )
        except ValidationError:
            raise error from None
