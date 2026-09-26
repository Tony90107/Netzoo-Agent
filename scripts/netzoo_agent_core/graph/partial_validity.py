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

__all__ = ["keep_valid_hypotheses", "retain_valid_first_pass", "valid_first_pass_subset"]


def _valid_subset(user_task: str, interpretation: SemanticInterpretation):
    """The hypotheses that pass on their own, and those that do not."""
    kept, dropped = [], []
    for index, hypothesis in enumerate(interpretation.outcome_hypotheses):
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
    return kept, dropped


def valid_first_pass_subset(
    user_task: str,
    interpretation: SemanticInterpretation,
) -> SemanticInterpretation | None:
    """The valid part of a rejected first pass, kept for a review that fails (Log 158).

    Log 28 keeps a first pass that passed as a whole when the review is
    unusable. A first pass that was only partly valid had nothing kept, so a
    review whose patch did not even parse left no reading at all although one
    first-pass hypothesis had passed every check.
    """
    if len(interpretation.outcome_hypotheses) < 2:
        return None
    kept, dropped = _valid_subset(user_task, interpretation)
    if not kept or not dropped:
        return None
    reduced = interpretation.model_copy(update={"outcome_hypotheses": kept}, deep=True)
    if not validate_outcome_hypotheses(
        user_task, [h.model_copy(deep=True) for h in reduced.outcome_hypotheses],
        reduced.request_mode,
    ).valid:
        return None
    return reduced


def retain_valid_first_pass(context, state, validated, partial_first, attempt: int):
    """Use the valid first-pass subset only when no validated first pass exists."""
    if validated is not None or partial_first is None:
        return validated
    record_event(context, state, "routing.valid_first_pass_subset_retained", "classify", {
        "attempt": attempt + 1, "kept": len(partial_first.outcome_hypotheses),
    })
    return partial_first


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
    kept, dropped = _valid_subset(user_task, interpretation)
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
