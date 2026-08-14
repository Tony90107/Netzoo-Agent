"""Semantic consistency checks for bounded Router outcome hypotheses."""

from __future__ import annotations

import re
from collections.abc import Sequence

from ..contracts import OutcomeHypothesis
from ..routing import has_direct_execution_intent, is_workflow_information_request

__all__ = ["needs_outcome_repair", "select_primary_hypothesis"]


_TOOL_SELECTION_PATTERN = re.compile(
    r"(?:\b(?:what|which).{0,40}\b(?:tools?|methods?|workflows?)\b|"
    r"(?:哪個|哪些|什麼).{0,20}(?:工具|方法|workflow))",
    flags=re.IGNORECASE | re.DOTALL,
)


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
    task: str,
    hypotheses: Sequence[OutcomeHypothesis],
) -> bool:
    """Return True when a scientific request was collapsed into no usable facts."""
    scientific_intent = bool(
        is_workflow_information_request(task)
        or has_direct_execution_intent(task)
        or _TOOL_SELECTION_PATTERN.search(task)
    )
    return scientific_intent and not any(
        _has_usable_evidence(item) for item in hypotheses
    )


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
