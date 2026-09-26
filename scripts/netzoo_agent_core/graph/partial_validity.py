"""Keep the valid readings when a final attempt still carries an invalid one (Log 156).

A review patch repairs the one hypothesis it names and carries the others
forward unchanged (Log 150). Validation requires every hypothesis to pass, so
an invalid reading nobody repaired used to sink a valid one beside it: Case 4
lost its sample-specific regulatory-network reading because an unrelated
expression-matrix reading still quoted evidence the request did not contain.

After the last attempt only, each hypothesis is validated on its own. The
valid ones are kept and the rest are dropped and recorded; the kept set is
validated again as a whole before it is used. Nothing is relaxed: every
remaining hypothesis passed the unchanged validator. Earlier attempts are left
alone so a repair can still turn an invalid reading into a valid one.
"""

from __future__ import annotations

from ..contracts.outcomes import SemanticInterpretation
from ..interpretation.outcome_validation import OutcomeValidation, validate_outcome_hypotheses
from .context import record_event

__all__ = ["keep_valid_hypotheses"]


def keep_valid_hypotheses(
    context,
    state,
    user_task: str,
    interpretation: SemanticInterpretation,
    validation: OutcomeValidation,
    attempt: int,
) -> tuple[SemanticInterpretation, OutcomeValidation]:
    hypotheses = interpretation.outcome_hypotheses
    if validation.valid or len(hypotheses) < 2:
        return interpretation, validation
    kept, dropped = [], []
    for index, hypothesis in enumerate(hypotheses):
        # The validator completes outcomes in place; judge a copy.
        alone = validate_outcome_hypotheses(
            user_task, [hypothesis.model_copy(deep=True)], interpretation.request_mode,
        )
        if alone.valid:
            kept.append(hypothesis)
        else:
            dropped.append({"hypothesis": index, "issues": [
                issue.replace("hypothesis[0].", f"hypothesis[{index}].") for issue in alone.issues
            ]})
    if not kept or not dropped:
        return interpretation, validation
    reduced = interpretation.model_copy(update={"outcome_hypotheses": kept})
    revalidated = validate_outcome_hypotheses(
        user_task, reduced.outcome_hypotheses, reduced.request_mode,
    )
    if not revalidated.valid:
        return interpretation, validation
    record_event(context, state, "routing.invalid_hypotheses_dropped", "classify", {
        "attempt": attempt + 1, "kept": len(kept), "dropped": dropped,
    })
    return reduced, revalidated
