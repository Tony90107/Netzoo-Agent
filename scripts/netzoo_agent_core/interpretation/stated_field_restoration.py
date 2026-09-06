"""Move values the hypothesis already stated into the fields that carry them.

This is the one place the deterministic layer writes an outcome field, and the
rule it follows is narrow enough to state in one line: it may **move** a value
the hypothesis wrote in its own evidence, and it may never **invent** one.

The failure it repairs was the largest single family in the live record on both
models: the model says the same thing twice, in evidence and in the outcome
fields, and any mismatch rejects the whole interpretation. It cites the input
artifact and leaves `input_artifacts` empty; it cites `regulator_type=mirna` and
leaves `regulator_types` empty. The run then falls back to a registry guess
carrying no outcome at all.

Five structural guarantees, not promises:

1. A candidate value must appear verbatim in this hypothesis's own evidence
   under the matching dimension. Nothing is derived from a tool name, from the
   registry, or from matching the request text.
2. `input_artifact` additionally requires the request's own witnesses to have
   scoped that artifact as current -- two independent sources. Role fields have
   no such witness, so they are only ever moved, never witnessed into place.
3. `unknown` is never written.
4. The result is re-validated through `RequestedOutcome.model_validate`, not
   copied past validation, so a value outside the closed vocabulary cannot be
   written at all.
5. A candidate is applied only if it removes no fewer consistency issues than it
   creates: any addition that introduces a new `outcome_consistency_issues`
   entry is reverted individually.

Historical mentions cannot arrive here: a past-scoped clause yields
`noncurrent_input`, the opposite direction. Nothing is ever removed, no field
outside the three below is touched, and the result faces the identical strict
validation afterwards.
"""

from __future__ import annotations

from ..contracts.artifact_semantics import outcome_consistency_issues
from ..contracts.outcomes import RequestedOutcome, SemanticInterpretation
from .request_integrity import input_mentions

__all__ = ["restore_stated_fields"]

_UNKNOWN = "unknown"
# (evidence dimension, outcome field). Order is the order candidates are tried.
_MOVABLE = (
    ("input_artifact", "input_artifacts"),
    ("regulator_type", "regulator_types"),
    ("target_type", "target_types"),
)


def _witnessed_current(user_task: str) -> dict[str, str]:
    witnessed: dict[str, str] = {}
    for item in input_mentions(user_task):
        if item.status == "current" and item.artifact != _UNKNOWN:
            witnessed.setdefault(item.artifact, item.text_span)
    return witnessed


def _with_value(outcome: RequestedOutcome, field: str, value: str) -> RequestedOutcome | None:
    """Re-validate rather than copy past validation; None when the value cannot be written."""
    payload = outcome.model_dump()
    payload[field] = [*payload[field], value]
    try:
        return RequestedOutcome.model_validate(payload)
    except Exception:
        return None


def restore_stated_fields(
    user_task: str, interpretation: SemanticInterpretation,
) -> tuple[SemanticInterpretation, list[dict[str, object]]]:
    """Return the interpretation with stated values moved into place, plus a record."""
    witnessed = _witnessed_current(user_task)
    restored: list[dict[str, object]] = []
    hypotheses = []
    for index, hypothesis in enumerate(interpretation.outcome_hypotheses):
        outcome = hypothesis.outcome
        baseline = set(outcome_consistency_issues(outcome))
        for dimension, field in _MOVABLE:
            stated = [
                item.value for item in hypothesis.evidence
                if item.dimension == dimension and item.value != _UNKNOWN
            ]
            for value in dict.fromkeys(stated):
                if value in getattr(outcome, field):
                    continue
                if dimension == "input_artifact" and value not in witnessed:
                    continue
                candidate = _with_value(outcome, field, value)
                if candidate is None:
                    continue
                if set(outcome_consistency_issues(candidate)) - baseline:
                    # This move would trade one rejection for another.
                    continue
                outcome = candidate
                restored.append({
                    "hypothesis": index,
                    "field": field,
                    "value": value,
                    "witnessed_span": witnessed.get(value),
                })
        hypotheses.append(
            hypothesis if outcome is hypothesis.outcome
            else hypothesis.model_copy(update={"outcome": outcome})
        )
    if not restored:
        return interpretation, []
    return interpretation.model_copy(update={"outcome_hypotheses": hypotheses}), restored
