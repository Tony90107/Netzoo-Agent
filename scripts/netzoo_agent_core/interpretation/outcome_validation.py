"""Generic validation for LLM-produced scientific outcome evidence."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import re

from ..contracts import OutcomeHypothesis, RequestedOutcome

__all__: list[str] = []


@dataclass(frozen=True, slots=True)
class OutcomeValidation:
    """Deterministic acceptance result for semantic hypotheses."""

    valid: bool
    issues: tuple[str, ...]


def _normalized(value: str) -> str:
    return re.sub(r"[\W_]+", " ", value.casefold()).strip()


def _outcome_values(outcome: RequestedOutcome) -> dict[str, set[str]]:
    return {
        "operation": {outcome.operation},
        "artifact_type": {outcome.artifact_type},
        "entity_type": set(outcome.entity_types),
        "regulator_type": set(outcome.regulator_types),
        "target_type": set(outcome.target_types),
        "granularity": {outcome.granularity},
    }


def _required_evidence(outcome: RequestedOutcome) -> list[tuple[str, str]]:
    required: list[tuple[str, str]] = []
    if outcome.operation != "unknown":
        required.append(("operation", outcome.operation))
    if outcome.artifact_type != "unknown":
        required.append(("artifact_type", outcome.artifact_type))
    if outcome.granularity not in {"unknown", "not_applicable"}:
        required.append(("granularity", outcome.granularity))
    required.extend(
        ("regulator_type", value)
        for value in outcome.regulator_types
        if value != "unknown"
    )
    required.extend(
        ("target_type", value)
        for value in outcome.target_types
        if value != "unknown"
    )
    role_entities = set(outcome.regulator_types) | set(outcome.target_types)
    required.extend(
        ("entity_type", value)
        for value in outcome.entity_types
        if value != "unknown" and value not in role_entities
    )
    return required


def _is_not_applicable(outcome: RequestedOutcome) -> bool:
    return (
        outcome.operation == "unknown"
        and outcome.artifact_type == "unknown"
        and outcome.granularity == "not_applicable"
        and not outcome.entity_types
        and not outcome.regulator_types
        and not outcome.target_types
        and not outcome.unresolved_dimensions
    )


def validate_outcome_hypotheses(
    user_task: str,
    hypotheses: Sequence[OutcomeHypothesis],
) -> OutcomeValidation:
    """Validate evidence without selecting or naming a workflow."""
    if not hypotheses:
        return OutcomeValidation(False, ("missing_hypotheses",))

    issues: list[str] = []
    normalized_task = _normalized(user_task)
    for index, hypothesis in enumerate(hypotheses):
        outcome_values = _outcome_values(hypothesis.outcome)
        required_evidence = _required_evidence(hypothesis.outcome)
        if (
            not required_evidence
            and not hypothesis.evidence
            and not _is_not_applicable(hypothesis.outcome)
        ):
            issues.append(f"hypothesis[{index}].unusable_outcome")
        evidence_pairs: set[tuple[str, str]] = set()
        for item in hypothesis.evidence:
            normalized_value = _normalized(item.value)
            evidence_pairs.add((item.dimension, normalized_value))
            valid_values = {
                _normalized(value) for value in outcome_values[item.dimension]
            }
            if normalized_value not in valid_values:
                issues.append(
                    f"hypothesis[{index}].conflicting_evidence:"
                    f"{item.dimension}={item.value}"
                )
            if item.source == "explicit":
                span = _normalized(item.text_span or "")
                if not span or span not in normalized_task:
                    issues.append(
                        f"hypothesis[{index}].ungrounded_evidence:"
                        f"{item.dimension}={item.value}"
                    )

        for dimension, value in required_evidence:
            normalized_value = _normalized(value)
            if (dimension, normalized_value) not in evidence_pairs:
                issues.append(
                    f"hypothesis[{index}].missing_evidence:{dimension}={value}"
                )

    unique_issues = tuple(dict.fromkeys(issues))
    return OutcomeValidation(not unique_issues, unique_issues)
