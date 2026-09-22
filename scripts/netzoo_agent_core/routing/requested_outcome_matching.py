"""Fail-closed matching for one fully typed requested outcome."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from workflow_registry import (
    OUTPUT_CAPABILITIES,
    OutputCapabilityDefinition,
    RecommendedAction,
)

from ..contracts import CapabilityMatch, RequestedOutcome
from ..contracts.artifact_semantics import outcome_consistency_issues
from .candidate_ranking import _specificity_score, stated_dimension_score, _UNKNOWN
from .capability_compatibility import (
    InputAvailability,
    InputAvailabilityLike,
    _accepts_inputs,
    _has_unknown,
    _is_not_applicable,
    _matches,
    _partially_compatible,
    _supported_artifacts,
    _supported_entities,
)
from .clarification_planner import plan_clarification


def _selection_question(
    outcome: RequestedOutcome,
    candidates: list[tuple[RecommendedAction, OutputCapabilityDefinition]],
) -> str:
    decision = plan_clarification(
        [action for action, _ in candidates],
        outcomes=[outcome],
        capabilities=dict(candidates),
    )
    if decision is not None:
        return decision.question
    if outcome.artifact_type == "unknown":
        return "What artifact should NetZoo produce?"
    return "Which scientific result do you want NetZoo to produce?"


def _alternative_actions(
    outcome: RequestedOutcome,
    capabilities: Mapping[RecommendedAction, OutputCapabilityDefinition],
) -> list[RecommendedAction]:
    requested_entities = set(outcome.entity_types) - {_UNKNOWN}
    if not requested_entities:
        return []
    ranked: list[tuple[int, int, RecommendedAction]] = []
    for index, (action, capability) in enumerate(capabilities.items()):
        # A workflow can be a useful alternative to an unsupported acquisition
        # request when the user names a meaningful relationship (for example
        # miRNA + gene). A lone broad entity such as protein is not enough to
        # redirect an acquisition request to an unrelated inference workflow.
        if (
            capability.operation != outcome.operation
            and len(requested_entities) < 2
            and requested_entities.isdisjoint({"mirna", "tf", "gene"})
        ):
            continue
        entity_overlap = requested_entities & _supported_entities(
            outcome.artifact_type, capability
        )
        if not entity_overlap:
            continue
        score = 2 * len(entity_overlap)
        if outcome.granularity in capability.granularities:
            score += 2
        score += len(set(outcome.regulator_types) & capability.regulator_types)
        score += len(set(outcome.target_types) & capability.target_types)
        ranked.append((-score, index, action))
    ranked.sort()
    return [action for _, _, action in ranked[:2]]


def _mismatch_dimensions(
    outcome: RequestedOutcome,
    capabilities: Mapping[RecommendedAction, OutputCapabilityDefinition],
    available_inputs: InputAvailabilityLike = (),
) -> list[str]:
    values = list(capabilities.values())
    mismatches = []
    if not any(item.operation == outcome.operation for item in values):
        mismatches.append("operation")
    if outcome.input_artifacts and not any(
        _accepts_inputs(outcome, item, available_inputs)
        and (
            outcome.artifact_type == _UNKNOWN
            or outcome.artifact_type in _supported_artifacts(item)
        )
        for item in values
    ):
        mismatches.append("input_artifacts")
    if not any(
        outcome.artifact_type in _supported_artifacts(item) for item in values
    ):
        mismatches.append("artifact_type")
    if not any(outcome.granularity in item.granularities for item in values):
        mismatches.append("granularity")
    requested_entities = set(outcome.entity_types) - {_UNKNOWN}
    if requested_entities and not any(
        requested_entities.issubset(_supported_entities(outcome.artifact_type, item))
        for item in values
    ):
        mismatches.append("entity_types")
    requested_regulators = set(outcome.regulator_types) - {_UNKNOWN}
    if requested_regulators and not any(
        requested_regulators.issubset(item.regulator_types) for item in values
    ):
        mismatches.append("regulator_types")
    requested_targets = set(outcome.target_types) - {_UNKNOWN}
    if requested_targets and not any(
        requested_targets.issubset(item.target_types) for item in values
    ):
        mismatches.append("target_types")
    return mismatches


_INPUT_GAP_LABELS = {
    "expression_matrix": "gene-expression matrix",
    "mirna_prior": "miRNA prior",
    "motif_prior": "TF-motif prior",
    "ppi_prior": "PPI prior",
}


def _input_gap_question(
    outcome: RequestedOutcome,
    candidates: Sequence[tuple[RecommendedAction, OutputCapabilityDefinition]],
    availability: InputAvailability,
) -> str:
    """Explain the smallest explicit absence that eliminated every candidate."""
    requested_absent = (
        set(outcome.input_artifacts) - {_UNKNOWN}
    ) & set(availability.absent)
    missing_sets = [
        (set(capability.required_input_artifacts) & set(availability.absent))
        | requested_absent
        for _, capability in candidates
    ]
    missing_sets = [missing for missing in missing_sets if missing]
    common_missing = set.intersection(*missing_sets) if missing_sets else set()
    if common_missing:
        labels = [
            _INPUT_GAP_LABELS.get(value, value.replace("_", " "))
            for value in sorted(common_missing)
        ]
        subject = " and ".join(labels)
        pronoun = "them" if len(labels) > 1 else "it"
        return (
            f"Every otherwise compatible workflow requires {subject}, which you "
            f"marked unavailable. Can you provide {pronoun}, or should NetZoo "
            "target a different scientific result?"
        )
    return (
        "A required input was explicitly marked unavailable. "
        "Which compatible input bundle can you provide?"
    )


def match_requested_outcome(
    outcome: RequestedOutcome,
    capabilities: Mapping[
        RecommendedAction, OutputCapabilityDefinition
    ] = OUTPUT_CAPABILITIES,
    *,
    available_inputs: InputAvailabilityLike = (),
) -> CapabilityMatch:
    """Return a fail-closed match derived only from typed outcome dimensions."""
    issues = outcome_consistency_issues(outcome)
    if issues:
        return CapabilityMatch(status="unsupported", mismatch_dimensions=list(issues))
    if _is_not_applicable(outcome):
        return CapabilityMatch(status="not_applicable")
    candidates = [
        (action, capability)
        for action, capability in capabilities.items()
        if _matches(outcome, capability, available_inputs)
    ]
    if _has_unknown(outcome):
        partial_candidates = [
            (action, capability)
            for action, capability in capabilities.items()
            if _partially_compatible(outcome, capability, available_inputs)
        ]
        if (
            not partial_candidates
            and isinstance(available_inputs, InputAvailability)
            and available_inputs.absent
        ):
            candidates_without_availability = [
                (action, capability)
                for action, capability in capabilities.items()
                if _partially_compatible(outcome, capability, ())
            ]
            if not candidates_without_availability:
                return CapabilityMatch(
                    status="ambiguous",
                    hypothesis_actions=[],
                    clarification_question=_selection_question(outcome, []),
                )
            return CapabilityMatch(
                status="unsupported",
                mismatch_dimensions=["input_artifacts"],
                clarification_question=_input_gap_question(
                    outcome,
                    candidates_without_availability,
                    available_inputs,
                ),
            )
        return CapabilityMatch(
            status="ambiguous",
            hypothesis_actions=[action for action, _ in partial_candidates],
            clarification_question=_selection_question(outcome, partial_candidates),
        )
    if len(candidates) == 1:
        return CapabilityMatch(status="exact", matched_actions=[candidates[0][0]])
    if len(candidates) > 1:
        regulator_sets = {capability.regulator_types for _, capability in candidates}
        if not outcome.regulator_types and len(regulator_sets) > 1:
            return CapabilityMatch(
                status="ambiguous",
                clarification_question=_selection_question(outcome, candidates),
            )
        ranked = sorted(
            (
                _specificity_score(outcome, capability),
                index,
                action,
            )
            for index, (action, capability) in enumerate(candidates)
        )
        winner = dict(candidates)[ranked[0][2]]
        # A winner must win on a dimension the request stated. The matcher may
        # still use internal specificity to order candidates, but not to certify
        # an otherwise unstated choice as exact.
        if len(ranked) == 1 or (
            ranked[0][0] < ranked[1][0]
            and all(
                stated_dimension_score(outcome, winner)
                < stated_dimension_score(outcome, capability)
                for action, capability in candidates
                if action != ranked[0][2]
            )
        ):
            return CapabilityMatch(status="exact", matched_actions=[ranked[0][2]])
        return CapabilityMatch(
            status="ambiguous",
            clarification_question=_selection_question(outcome, candidates),
        )
    return CapabilityMatch(
        status="unsupported",
        alternative_actions=_alternative_actions(outcome, capabilities),
        mismatch_dimensions=_mismatch_dimensions(outcome, capabilities, available_inputs),
    )
