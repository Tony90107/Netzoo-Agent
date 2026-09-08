"""Tell "I never knew" apart from "I knew and stopped saying so".

An accepted outcome carrying `unknown` in a dimension is recorded today as one
undifferentiated fact, and two opposite situations reach it:

- the first pass never committed to that dimension either, or
- the first pass named a concrete value and the accepted interpretation no
  longer carries it.

Only the second is a loss of meaning the system already had, and it is the one
the evidence contract can create an incentive for: `unknown` requires no
evidence (`outcome_validation._required_evidence`), so dropping a value always
dissolves an `ungrounded_evidence` issue about it, while supplying a quote the
request actually contains may be impossible.

Nothing in the record distinguished the two. That gap let a rate measured on one
population (8-12% of accepted outcomes carrying `unknown` in `operation` or
`artifact_type`, over three mini rounds) be attributed to a mechanism observed on
a different prompt, and the attribution survived three documents unchallenged.
Re-derived from the same archives, none of those trials carried an
`ungrounded_evidence` issue on the first pass at all.

This module only measures. It changes no value, rejects nothing, and is not
consulted by validation or capability matching.

Two distinctions it is built to preserve:

- A drop is reported with the first pass's *grounding result* for that exact
  dimension and value (`absent`, `unmatched`, or none), so "dropped after its
  quote failed" never merges with "dropped for some other reason".
- When the hypotheses of the two interpretations cannot be put in
  correspondence, the report says so. "Not comparable" reported as "no
  downgrades" is the same class of error this module exists to expose.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ..contracts.outcomes import RequestedOutcome, SemanticInterpretation

__all__: list[str] = []


#: Outcome field -> the evidence dimension its values are cited under. Mirrors
#: `semantic_patch._EVIDENCE_DIMENSIONS`; the link is what lets a dropped value
#: be paired with the grounding result recorded against it.
#: `display_entities` and `unresolved_dimensions` carry no evidence and are not
#: scientific commitments, so they are absent.
_DIMENSION_OF: dict[str, str] = {
    "operation": "operation",
    "input_artifacts": "input_artifact",
    "artifact_type": "artifact_type",
    "entity_types": "entity_type",
    "regulator_types": "regulator_type",
    "target_types": "target_type",
    "granularity": "granularity",
    "selection_tags": "selection_tag",
}

_SCALAR_FIELDS = frozenset({"operation", "artifact_type", "granularity"})

#: Values that assert no scientific commitment. `not_applicable` is a real
#: granularity for a request with no analysis in it, but it is still not a
#: commitment to one, so a move from `sample_specific` to it is a drop. Which
#: one it landed on is kept verbatim in `to_value` rather than collapsed here.
_UNCOMMITTED = frozenset({"unknown", "not_applicable", ""})


@dataclass(frozen=True, slots=True)
class DowngradeReport:
    """What the accepted interpretation stopped committing to, and why.

    `comparable` false means the two interpretations could not be put in
    correspondence, and `downgrades` is then empty for that reason alone. A
    caller that reads the emptiness without the flag reproduces the very
    conflation this module was written to expose.
    """

    comparable: bool
    hypothesis_index: int | None = None
    downgrades: tuple[dict[str, str | None], ...] = ()
    #: Present only when `comparable` is false: the closed-vocabulary reason.
    reason: str | None = None


def _grounding_index(
    shapes: Sequence[Mapping[str, object]],
    hypothesis_index: int,
) -> dict[tuple[str, str], str]:
    """Map (dimension, value) -> span class, for one hypothesis of one attempt.

    Keyed on the value as well as the dimension: a hypothesis can cite two
    values under one dimension and have only one of them fail.
    """
    return {
        (str(shape.get("dimension")), str(shape.get("value"))): str(shape.get("span"))
        for shape in shapes
        if shape.get("hypothesis") == hypothesis_index
    }


def _dropped(field: str, before, after) -> list[tuple[str, str]]:
    """Return (from_value, to_value) for each commitment `field` no longer carries."""
    if field in _SCALAR_FIELDS:
        if str(before) in _UNCOMMITTED or before == after:
            return []
        return [(str(before), str(after))] if str(after) in _UNCOMMITTED else []
    kept = {str(value) for value in after or ()}
    committed = {str(value) for value in after or () if str(value) not in _UNCOMMITTED}
    # A value gone from a list that still names other concrete values was
    # narrowed, not abandoned; the outcome still commits to something in that
    # dimension. Kept apart because only the abandoning kind is a loss of
    # meaning, and merging them would inflate every count.
    landed = "empty" if not committed else "narrowed"
    return [
        (str(value), landed)
        for value in before or ()
        if str(value) not in _UNCOMMITTED and str(value) not in kept
    ]


def outcome_downgrades(
    before: RequestedOutcome,
    after: RequestedOutcome,
    grounding: Mapping[tuple[str, str], str] | None = None,
) -> tuple[dict[str, str | None], ...]:
    """Every commitment `before` made that `after` no longer carries.

    `grounding` supplies the first pass's own grounding result per
    (dimension, value); a value absent from it was never reported ungrounded,
    and its record carries `first_pass_span: None`.
    """
    grounding = grounding or {}
    before_fields = before.model_dump()
    after_fields = after.model_dump()
    return tuple(
        {
            "field": field,
            "dimension": dimension,
            "from_value": from_value,
            "to_value": to_value,
            "first_pass_span": grounding.get((dimension, from_value)),
        }
        for field, dimension in _DIMENSION_OF.items()
        for from_value, to_value in _dropped(
            field, before_fields.get(field), after_fields.get(field)
        )
    )


def interpretation_downgrades(
    proposal: SemanticInterpretation | None,
    accepted: SemanticInterpretation,
    first_pass_shapes: Sequence[Mapping[str, object]] = (),
    *,
    hypothesis_index: int | None = None,
) -> DowngradeReport:
    """Compare the accepted interpretation against the first pass it came from.

    `hypothesis_index` is the correspondence the caller already knows -- the
    index a field-scoped patch was merged onto. Without it, a correspondence
    exists only when the first pass offered a single hypothesis: a whole review
    returns one hypothesis and no index, so against a multi-hypothesis proposal
    there is nothing to say which one it replaced, and guessing would be
    inventing the comparison.
    """
    # A first pass that failed schema validation is kept as the raw payload the
    # provider returned, not as a parsed interpretation. There is no typed
    # outcome to compare against, and reading one out of the payload here would
    # be re-implementing the contract that just rejected it.
    if not isinstance(proposal, SemanticInterpretation):
        return DowngradeReport(False, reason="no_parsed_first_pass")
    if hypothesis_index is None:
        if len(proposal.outcome_hypotheses) != 1:
            return DowngradeReport(False, reason="hypothesis_correspondence_unknown")
        hypothesis_index = 0
    if not 0 <= hypothesis_index < len(proposal.outcome_hypotheses):
        return DowngradeReport(False, reason="hypothesis_index_out_of_range")
    if len(accepted.outcome_hypotheses) != 1 and hypothesis_index >= len(
        accepted.outcome_hypotheses
    ):
        return DowngradeReport(False, reason="hypothesis_correspondence_unknown")
    accepted_hypothesis = accepted.outcome_hypotheses[
        hypothesis_index if len(accepted.outcome_hypotheses) > 1 else 0
    ]
    return DowngradeReport(
        True,
        hypothesis_index,
        outcome_downgrades(
            proposal.outcome_hypotheses[hypothesis_index].outcome,
            accepted_hypothesis.outcome,
            _grounding_index(first_pass_shapes, hypothesis_index),
        ),
    )
