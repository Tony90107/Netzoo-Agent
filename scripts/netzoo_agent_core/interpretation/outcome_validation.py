"""Generic validation for LLM-produced scientific outcome evidence."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import re
import unicodedata

from ..contracts import OutcomeHypothesis, RequestedOutcome
from ..contracts.artifact_semantics import ARTIFACT_SEMANTICS, outcome_consistency_issues
from .request_integrity import request_integrity_issues

__all__: list[str] = []


@dataclass(frozen=True, slots=True)
class OutcomeValidation:
    """Deterministic acceptance result for semantic hypotheses."""

    valid: bool
    issues: tuple[str, ...]
    recoverable: bool = False


def _normalized(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    # CJK words can be wrapped without a word separator. This is typography
    # normalization, not translation or synonym inference.
    text = re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", text)
    return re.sub(r"[\W_]+", " ", text).strip()


def _grounded_span(span: str, task: str) -> bool:
    if not span:
        return False
    left = r"(?<![a-z0-9])" if span[0].isascii() and span[0].isalnum() else ""
    right = r"(?![a-z0-9])" if span[-1].isascii() and span[-1].isalnum() else ""
    return re.search(left + re.escape(span) + right, task) is not None


def _outcome_values(outcome: RequestedOutcome) -> dict[str, set[str]]:
    return {
        "operation": {outcome.operation},
        "input_artifact": set(outcome.input_artifacts),
        "artifact_type": {outcome.artifact_type},
        "entity_type": set(outcome.entity_types),
        "regulator_type": set(outcome.regulator_types),
        "target_type": set(outcome.target_types),
        "granularity": {outcome.granularity},
        "selection_tag": set(outcome.selection_tags),
    }


def _entailed_by_artifact(outcome: RequestedOutcome) -> tuple[frozenset[str], str | None]:
    """Return the entity set and granularity the chosen artifact alone fixes.

    Where the ontology permits exactly one value, `outcome_consistency_issues`
    already rejects every other, so a separate evidence entry for it repeats
    what choosing the artifact_type has established. Artifacts that permit
    several values are excluded: there the value is a real choice.
    """
    rule = ARTIFACT_SEMANTICS.get(outcome.artifact_type)
    entities = (
        rule.entities
        if rule is not None and rule.entities is not None and len(rule.entities) == 1
        else frozenset()
    )
    granularity = (
        next(iter(rule.granularities))
        if rule is not None and rule.granularities is not None and len(rule.granularities) == 1
        else None
    )
    return entities, granularity


def _required_evidence(outcome: RequestedOutcome) -> list[tuple[str, str]]:
    required: list[tuple[str, str]] = []
    entailed_entities, entailed_granularity = _entailed_by_artifact(outcome)
    if outcome.operation != "unknown":
        required.append(("operation", outcome.operation))
    if outcome.artifact_type != "unknown":
        required.append(("artifact_type", outcome.artifact_type))
    required.extend(
        ("input_artifact", value) for value in outcome.input_artifacts
        if value != "unknown"
    )
    if outcome.granularity not in {"unknown", "not_applicable", entailed_granularity}:
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
        if value != "unknown"
        and value not in role_entities
        and value not in entailed_entities
    )
    return required


def _is_not_applicable(outcome: RequestedOutcome) -> bool:
    return (
        outcome.operation == "unknown"
        and outcome.artifact_type == "unknown"
        and outcome.granularity == "not_applicable"
        and not outcome.input_artifacts
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
        issues.extend(
            f"hypothesis[{index}].{issue}"
            for issue in request_integrity_issues(user_task, hypothesis.outcome)
        )
        issues.extend(
            f"hypothesis[{index}].{issue}"
            for issue in outcome_consistency_issues(hypothesis.outcome)
        )
        outcome_values = _outcome_values(hypothesis.outcome)
        required_evidence = _required_evidence(hypothesis.outcome)
        if (
            hypothesis.outcome.granularity == "not_applicable"
            and hypothesis.outcome.artifact_type == "unknown"
            and not _is_not_applicable(hypothesis.outcome)
        ):
            issues.append(f"hypothesis[{index}].inconsistent_not_applicable_outcome")
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
                if not _grounded_span(span, normalized_task):
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
    recoverable = bool(unique_issues) and all(
        ".ungrounded_evidence:" in issue for issue in unique_issues
    )
    return OutcomeValidation(not unique_issues, unique_issues, recoverable)
