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

import re

from ..contracts.outcomes import SemanticInterpretation
from ..interpretation.outcome_validation import OutcomeValidation, validate_outcome_hypotheses
from .context import record_event

__all__ = ["keep_valid_hypotheses", "retain_valid_first_pass", "valid_first_pass_subset"]


def _valid_subset(user_task: str, interpretation: SemanticInterpretation, *, with_siblings: bool = False):
    """The hypotheses that pass on their own, and those that do not.

    `with_siblings` judges each against the other readings' inputs (Log 242);
    the caller revalidates the kept set, where only kept readings count.
    """
    kept, dropped = [], []
    hypotheses = interpretation.outcome_hypotheses
    for index, hypothesis in enumerate(hypotheses):
        siblings = frozenset().union(*(
            other.outcome.input_artifacts for position, other in enumerate(hypotheses)
            if position != index
        )) if with_siblings else frozenset()
        # The validator completes outcomes in place; judge a copy.
        alone = validate_outcome_hypotheses(
            user_task, [hypothesis.model_copy(deep=True)], interpretation.request_mode,
            sibling_inputs=siblings,
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
    for with_siblings in (True, False):
        kept, dropped = _valid_subset(user_task, interpretation, with_siblings=with_siblings)
        if not kept or not dropped:
            continue
        reduced = interpretation.model_copy(update={"outcome_hypotheses": kept}, deep=True)
        if validate_outcome_hypotheses(
            user_task, [h.model_copy(deep=True) for h in reduced.outcome_hypotheses],
            reduced.request_mode,
        ).valid:
            return reduced
    return None


def retain_valid_first_pass(context, state, validated, partial_first, attempt: int):
    """Use the valid first-pass subset only when no validated first pass exists."""
    if validated is not None or partial_first is None:
        return validated
    record_event(context, state, "routing.valid_first_pass_subset_retained", "classify", {
        "attempt": attempt + 1, "kept": len(partial_first.outcome_hypotheses),
    })
    return partial_first


def issue_indices(issues) -> set[int]:
    """Hypothesis positions named by validation issues ("hypothesis[1].missing…")."""
    return {int(match) for issue in issues for match in re.findall(r"hypothesis\[(\d+)\]", issue)}


def keep_valid_hypotheses(
    context,
    state,
    user_task: str,
    interpretation: SemanticInterpretation,
    validation: OutcomeValidation,
    attempt: int,
    *,
    primary: int | None = None,
    invalid_before_sibling_repair: frozenset[int] = frozenset(),
) -> tuple[SemanticInterpretation, OutcomeValidation]:
    hypotheses = interpretation.outcome_hypotheses
    if validation.valid or len(hypotheses) < 2:
        return interpretation, validation
    # Judged against the other readings' inputs first (Log 242); if what that
    # keeps does not stand on its own, the reading-by-reading judgement decides.
    for with_siblings in (True, False):
        kept, dropped = _valid_subset(user_task, interpretation, with_siblings=with_siblings)
        if not kept or not dropped:
            continue
        dropped_at = {item["hypothesis"] for item in dropped if "hypothesis" in item}
        kept_at = set(range(len(hypotheses))) - dropped_at
        if primary in dropped_at and kept_at and kept_at <= invalid_before_sibling_repair:
            # A sibling repair keeps alternatives beside the primary reading; it
            # must not replace it (Log 279: case 6 became exact SAMBAR this way).
            record_event(context, state, "routing.sibling_only_reduction_refused", "classify", {
                "attempt": attempt + 1, "primary": primary, "kept": sorted(kept_at),
            })
            return interpretation, validation
        reduced = interpretation.model_copy(update={"outcome_hypotheses": kept})
        revalidated = validate_outcome_hypotheses(
            user_task, reduced.outcome_hypotheses, reduced.request_mode,
        )
        if not revalidated.valid:
            continue
        record_event(context, state, "routing.invalid_hypotheses_dropped", "classify", {
            "attempt": attempt + 1, "kept": len(kept), "dropped": dropped,
        })
        return reduced, revalidated
    return interpretation, validation
