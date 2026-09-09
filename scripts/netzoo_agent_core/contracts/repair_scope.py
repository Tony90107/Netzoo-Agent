"""What a rejection licenses the review to change.

A rejection names something wrong. It does not license rewriting everything: a
review asked to fix one ontology field rewrote the whole outcome in the record
and introduced failures the first pass did not have, which is how a request that
was right except for `granularity` ended as a validation error the user saw.

The scope could have been a table from issue code to field list. It is not, for
a reason that outlives this change: such a table is read far from the rule that
raises the issue, so it drifts from what the rule actually examines, and it makes
the system act on the text of a code rather than on the check behind it. Instead
each rule declares its own scope beside the fields it reads, and `Issue` carries
that declaration to the merge. Two parts are derived rather than declared -- the
field behind an evidence dimension, kept here, and the fields an ontology opens
when the artifact type legitimately changes, which belongs beside the ontology
itself in `artifact_semantics`.
"""
from __future__ import annotations

from collections.abc import Iterable

__all__ = [
    "DIMENSION_BY_FIELD", "FIELD_BY_DIMENSION", "Issue", "NO_OUTCOME_FIELDS",
    "OUTCOME_FIELDS", "permitted_fields",
]

#: Every field of `RequestedOutcome` a review may be permitted to change. A rule
#: that inspects the outcome as a whole declares all of them.
OUTCOME_FIELDS = frozenset({
    "operation", "input_artifacts", "artifact_type", "entity_types",
    "display_entities", "regulator_types", "target_types", "selection_tags",
    "granularity", "unresolved_dimensions", "named_methods",
})

#: Which outcome field an evidence dimension speaks about. One copy, because a
#: second one drifts: the merge, the validator and the scope all need it.
DIMENSION_BY_FIELD = {
    "operation": "operation",
    "input_artifacts": "input_artifact",
    "artifact_type": "artifact_type",
    "entity_types": "entity_type",
    "regulator_types": "regulator_type",
    "target_types": "target_type",
    "granularity": "granularity",
    "selection_tags": "selection_tag",
    "named_methods": "named_method",
}
FIELD_BY_DIMENSION = {v: k for k, v in DIMENSION_BY_FIELD.items()}

#: A rule about the evidence rather than the outcome. Nothing in the outcome was
#: questioned, so nothing in it may be rewritten.
NO_OUTCOME_FIELDS: frozenset[str] = frozenset()


class Issue(str):
    """An issue code that remembers which outcome fields its rule examined.

    Subclassing `str` is deliberate. Issue codes travel through prefixing,
    de-duplication, provider feedback and tests as plain strings, and every one
    of those callers keeps working untouched; only the merge asks for `.fields`.
    """

    __slots__ = ("fields",)

    def __new__(cls, code: str, fields: Iterable[str] = ()) -> "Issue":
        unknown = frozenset(fields) - OUTCOME_FIELDS
        if unknown:
            raise ValueError(f"Not outcome fields: {sorted(unknown)}")
        issue = super().__new__(cls, code)
        issue.fields = frozenset(fields)
        return issue

    def prefixed(self, prefix: str) -> "Issue":
        """Re-wrap after prefixing, which would otherwise drop the declaration."""
        return Issue(f"{prefix}{self}", self.fields)


def permitted_fields(issues: Iterable[str]) -> frozenset[str]:
    """The union of what the rules that fired examined.

    An issue that carries no declaration permits everything, which is what the
    code did before any rule declared anything. That is the safe direction for a
    stray code -- it withholds the restriction rather than the repair -- and
    `validate_outcome_hypotheses` is held to declaring one for every issue it
    raises, so the case does not arise from its own output.
    """
    fields: set[str] = set()
    for issue in issues:
        declared = getattr(issue, "fields", None)
        if declared is None:
            return OUTCOME_FIELDS
        fields |= declared
    return frozenset(fields)
