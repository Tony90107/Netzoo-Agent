"""Semantic consistency checks for bounded Router outcome hypotheses."""

from __future__ import annotations

from collections.abc import Sequence

from ..contracts import OutcomeHypothesis

__all__ = ["needs_outcome_repair", "select_primary_hypothesis"]


def _has_usable_evidence(hypothesis: OutcomeHypothesis) -> bool:
    outcome = hypothesis.outcome
    return bool(
        hypothesis.evidence
        or outcome.operation != "unknown"
        or outcome.artifact_type != "unknown"
        or outcome.granularity not in {"unknown", "not_applicable"}
        or set(outcome.entity_types) - {"unknown"}
        or set(outcome.regulator_types) - {"unknown"}
        or set(outcome.target_types) - {"unknown"}
    )


def needs_outcome_repair(
    hypotheses: Sequence[OutcomeHypothesis],
) -> bool:
    """Return True when a Router response has no usable semantic evidence.

    This deliberately inspects the typed response shape, not terms in the user's
    wording or the provider's `in_scope` flag.  Every under-classification gets
    one bounded repair attempt; if that attempt also lacks evidence, later gates
    keep the result at `no_tool`.
    """
    return not any(_has_usable_evidence(item) for item in hypotheses)


def select_primary_hypothesis(
    hypotheses: Sequence[OutcomeHypothesis],
) -> OutcomeHypothesis | None:
    """Select one evidence-leading hypothesis while preserving equal-score ties."""
    scored = sorted(
        (
            sum(
                2 if item.source == "explicit" else 1
                for item in hypothesis.evidence
            ),
            hypothesis.confidence,
            index,
            hypothesis,
        )
        for index, hypothesis in enumerate(hypotheses)
    )
    if not scored:
        return None
    best = scored[-1]
    if len(scored) > 1 and best[:2] == scored[-2][:2]:
        return None
    return best[3]
