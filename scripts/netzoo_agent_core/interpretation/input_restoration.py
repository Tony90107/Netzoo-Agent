"""Restore current inputs the request's own witnesses located, before validation.

This is the one place the deterministic layer writes an outcome field, and it
requires **two independent sources to agree** before it writes anything:

1. `input_mentions` located the artifact in the request text and scoped it as
   current -- the same witnesses the validator already trusts enough to waive
   the evidence requirement, and the same call that raises
   `missing_current_input`; and
2. the model's own evidence cites that artifact, so it demonstrably read the
   request and only failed to copy the value into the field.

Requiring (2) is what keeps `an interpretation that omits an explicitly stated
current input must not pass` intact. A model that never mentioned the artifact
at all still fails, exactly as before; only the model that said it in the wrong
place is repaired. A first cut that used the witness alone silently removed that
invariant and fifteen tests written to guard it went red.

It never adds `unknown`, never touches a role field, and never removes anything.
Historical mentions cannot arrive here: a clause scoped to the past yields
`noncurrent_input`, the opposite direction. The result faces the identical
strict validation, so this changes which hypotheses survive, not what is valid.
"""

from __future__ import annotations

from ..contracts.outcomes import SemanticInterpretation
from .request_integrity import input_mentions

__all__ = ["restore_confirmed_inputs"]

_UNKNOWN = "unknown"
_MAX_INPUT_ARTIFACTS = 4


def restore_confirmed_inputs(
    user_task: str, interpretation: SemanticInterpretation,
) -> tuple[SemanticInterpretation, list[dict[str, object]]]:
    """Return the interpretation with witnessed current inputs added, plus a record."""
    witnessed: dict[str, str] = {}
    for item in input_mentions(user_task):
        if item.status == "current" and item.artifact != _UNKNOWN:
            witnessed.setdefault(item.artifact, item.text_span)
    if not witnessed:
        return interpretation, []

    restored: list[dict[str, object]] = []
    hypotheses = []
    for index, hypothesis in enumerate(interpretation.outcome_hypotheses):
        present = set(hypothesis.outcome.input_artifacts)
        # Only what this hypothesis itself claimed as an input elsewhere.
        claimed = {
            item.value for item in hypothesis.evidence
            if item.dimension == "input_artifact"
        }
        missing = [
            artifact for artifact in sorted(witnessed)
            if artifact not in present and artifact in claimed
        ]
        # The field is bounded, and an outcome already naming four inputs is not
        # the shape this repair was written for. Report the overflow instead of
        # silently dropping it or raising on a live round.
        room = _MAX_INPUT_ARTIFACTS - len(hypothesis.outcome.input_artifacts)
        if not missing or room <= 0:
            hypotheses.append(hypothesis)
            continue
        added = missing[:room]
        restored.extend(
            {
                "hypothesis": index,
                "artifact": artifact,
                "text_span": witnessed[artifact],
                "dropped_for_bound": False,
            }
            for artifact in added
        )
        restored.extend(
            {
                "hypothesis": index,
                "artifact": artifact,
                "text_span": witnessed[artifact],
                "dropped_for_bound": True,
            }
            for artifact in missing[room:]
        )
        hypotheses.append(
            hypothesis.model_copy(
                update={
                    "outcome": hypothesis.outcome.model_copy(
                        update={
                            "input_artifacts": [
                                *hypothesis.outcome.input_artifacts, *added,
                            ]
                        }
                    )
                }
            )
        )
    if not restored:
        return interpretation, []
    return (
        interpretation.model_copy(update={"outcome_hypotheses": hypotheses}),
        restored,
    )
