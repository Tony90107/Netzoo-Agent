"""Deterministic matching between requested outcomes and workflow capabilities."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re

from workflow_registry import (
    ACTION_DEFINITIONS,
    OUTPUT_CAPABILITIES,
    OutputCapabilityDefinition,
    RecommendedAction,
    RUN_ACTIONS,
)

from ..contracts import (
    CapabilityMatch,
    OutcomeHypothesis,
    RequestedOutcome,
    TaskDecision,
)


_UNKNOWN = "unknown"


def _has_unknown(outcome: RequestedOutcome) -> bool:
    return bool(
        outcome.unresolved_dimensions
        or _UNKNOWN in {outcome.operation, outcome.artifact_type, outcome.granularity}
        or _UNKNOWN in outcome.entity_types
        or _UNKNOWN in outcome.regulator_types
        or _UNKNOWN in outcome.target_types
    )


def _matches(
    outcome: RequestedOutcome,
    capability: OutputCapabilityDefinition,
) -> bool:
    if _has_unknown(outcome):
        return False
    return (
        outcome.operation == capability.operation
        and outcome.artifact_type == capability.artifact_type
        and outcome.granularity in capability.granularities
        and set(outcome.entity_types).issubset(capability.entity_types)
        and set(outcome.regulator_types).issubset(capability.regulator_types)
        and set(outcome.target_types).issubset(capability.target_types)
    )


def _known_scalar_matches(requested: str, supported: str) -> bool:
    return requested == _UNKNOWN or requested == supported


def _known_set_matches(requested: Sequence[str], supported: frozenset[str]) -> bool:
    known = set(requested) - {_UNKNOWN}
    return known.issubset(supported)


def _partially_compatible(
    outcome: RequestedOutcome,
    capability: OutputCapabilityDefinition,
) -> bool:
    return (
        _known_scalar_matches(outcome.operation, capability.operation)
        and _known_scalar_matches(outcome.artifact_type, capability.artifact_type)
        and (
            outcome.granularity == _UNKNOWN
            or outcome.granularity in capability.granularities
        )
        and _known_set_matches(outcome.entity_types, capability.entity_types)
        and _known_set_matches(outcome.regulator_types, capability.regulator_types)
        and _known_set_matches(outcome.target_types, capability.target_types)
    )


def _selection_question(
    outcome: RequestedOutcome,
    candidates: list[tuple[RecommendedAction, OutputCapabilityDefinition]],
) -> str:
    regulator_sets = {item[1].regulator_types for item in candidates}
    if outcome.artifact_type == "regulatory_network" and (
        not outcome.regulator_types or len(regulator_sets) > 1
    ):
        return (
            "Which regulator type should the network model: transcription factors, "
            "miRNA regulators, or both?"
        )
    if outcome.artifact_type == "unknown":
        return "What artifact should NetZoo produce?"
    if outcome.granularity == "unknown":
        return "Should the result be aggregate or sample-specific?"
    return "Which of the registered result types do you want NetZoo to produce?"


def _specificity_score(
    outcome: RequestedOutcome,
    capability: OutputCapabilityDefinition,
) -> int:
    return (
        len(capability.entity_types - set(outcome.entity_types))
        + len(capability.regulator_types - set(outcome.regulator_types))
        + len(capability.target_types - set(outcome.target_types))
        + len(capability.granularities - {outcome.granularity})
        + len(capability.guidance_predecessors)
    )


def _alternative_actions(
    outcome: RequestedOutcome,
    capabilities: Mapping[RecommendedAction, OutputCapabilityDefinition],
) -> list[RecommendedAction]:
    requested_entities = set(outcome.entity_types) - {_UNKNOWN}
    if not requested_entities:
        return []
    ranked: list[tuple[int, int, RecommendedAction]] = []
    for index, (action, capability) in enumerate(capabilities.items()):
        entity_overlap = requested_entities & capability.entity_types
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
) -> list[str]:
    values = list(capabilities.values())
    mismatches = []
    if not any(item.operation == outcome.operation for item in values):
        mismatches.append("operation")
    if not any(item.artifact_type == outcome.artifact_type for item in values):
        mismatches.append("artifact_type")
    if not any(outcome.granularity in item.granularities for item in values):
        mismatches.append("granularity")
    requested_entities = set(outcome.entity_types) - {_UNKNOWN}
    if requested_entities and not any(
        requested_entities.issubset(item.entity_types) for item in values
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


def match_requested_outcome(
    outcome: RequestedOutcome,
    capabilities: Mapping[
        RecommendedAction, OutputCapabilityDefinition
    ] = OUTPUT_CAPABILITIES,
) -> CapabilityMatch:
    """Return a fail-closed match derived only from typed outcome dimensions."""
    candidates = [
        (action, capability)
        for action, capability in capabilities.items()
        if _matches(outcome, capability)
    ]
    if _has_unknown(outcome):
        return CapabilityMatch(
            status="ambiguous",
            clarification_question=_selection_question(outcome, candidates),
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
        if len(ranked) == 1 or ranked[0][0] < ranked[1][0]:
            return CapabilityMatch(status="exact", matched_actions=[ranked[0][2]])
        return CapabilityMatch(
            status="ambiguous",
            clarification_question=_selection_question(outcome, candidates),
        )
    return CapabilityMatch(
        status="unsupported",
        alternative_actions=_alternative_actions(outcome, capabilities),
        mismatch_dimensions=_mismatch_dimensions(outcome, capabilities),
    )


def _hypothesis_evidence_score(hypothesis: OutcomeHypothesis) -> int:
    return sum(2 if item.source == "explicit" else 1 for item in hypothesis.evidence)


def _advisory_specificity_penalty(
    outcome: RequestedOutcome,
    capability: OutputCapabilityDefinition,
) -> int:
    """Penalize extra biological roles only when the user specified that role."""
    requested_entities = set(outcome.entity_types) - {_UNKNOWN}
    requested_regulators = set(outcome.regulator_types) - {_UNKNOWN}
    requested_targets = set(outcome.target_types) - {_UNKNOWN}
    return (
        (len(capability.entity_types - requested_entities) if requested_entities else 0)
        + (
            len(capability.regulator_types - requested_regulators)
            if requested_regulators
            else 0
        )
        + (len(capability.target_types - requested_targets) if requested_targets else 0)
    )


def has_granularity_only_ambiguity(
    hypotheses: Sequence[OutcomeHypothesis],
) -> bool:
    """Return whether hypotheses preserve every requested fact except granularity."""
    if not hypotheses:
        return False
    outcomes = [item.outcome for item in hypotheses]
    granularities = {item.granularity for item in outcomes}
    signatures = {
        (
            item.operation,
            item.artifact_type,
            tuple(sorted(item.entity_types)),
            tuple(sorted(item.regulator_types)),
            tuple(sorted(item.target_types)),
        )
        for item in outcomes
    }
    # A partial hypothesis (unknown granularity) and explicit granularity
    # alternatives still describe the same missing choice.  Treat that as a
    # granularity question whenever no other scientific dimension changes.
    return (
        granularities <= {"unknown", "aggregate", "sample_specific"}
        and len(signatures) == 1
    )


def _granularity_only_question(
    hypotheses: Sequence[OutcomeHypothesis],
) -> str | None:
    """Return the sole clarification when only outcome granularity differs."""
    if has_granularity_only_ambiguity(hypotheses):
        return "Should the result be aggregate or sample-specific?"
    return None


def match_outcome_hypotheses(
    hypotheses: Sequence[OutcomeHypothesis],
    capabilities: Mapping[
        RecommendedAction, OutputCapabilityDefinition
    ] = OUTPUT_CAPABILITIES,
) -> CapabilityMatch:
    """Match complete outcomes strictly and incomplete hypotheses advisably."""
    exact: list[RecommendedAction] = []
    advisory: list[tuple[int, int, int, RecommendedAction]] = []
    for hypothesis in hypotheses:
        strict = match_requested_outcome(hypothesis.outcome, capabilities)
        if not hypothesis.assumptions and strict.status == "exact":
            exact.extend(strict.matched_actions)
        score = _hypothesis_evidence_score(hypothesis)
        for index, (action, capability) in enumerate(capabilities.items()):
            if _partially_compatible(hypothesis.outcome, capability):
                advisory.append(
                    (
                        score,
                        -_advisory_specificity_penalty(
                            hypothesis.outcome,
                            capability,
                        ),
                        index,
                        action,
                    )
                )

    unique_exact = list(dict.fromkeys(exact))
    if len(unique_exact) == 1:
        return CapabilityMatch(status="exact", matched_actions=unique_exact)
    if advisory:
        top_score = max(item[:2] for item in advisory)
        top_actions = [
            action
            for evidence_score, specificity_score, _, action in sorted(
                advisory,
                key=lambda item: item[2],
            )
            if (evidence_score, specificity_score) == top_score
        ]
        return CapabilityMatch(
            status="ambiguous",
            hypothesis_actions=list(dict.fromkeys(top_actions)),
            clarification_question=(
                _granularity_only_question(hypotheses)
                or "Which compatible network result do you mean?"
            ),
        )

    first_outcome = hypotheses[0].outcome if hypotheses else None
    if first_outcome is not None:
        return match_requested_outcome(first_outcome, capabilities)
    return CapabilityMatch(
        status="ambiguous",
        clarification_question="What scientific result do you want?",
    )


def guidance_actions_for(action: RecommendedAction) -> list[RecommendedAction]:
    """Expand one exact end-to-end action into its registered guidance sequence."""
    capability = OUTPUT_CAPABILITIES[action]
    return [*capability.guidance_predecessors, action]


def named_workflow_action(task: str) -> RecommendedAction | None:
    """Resolve an explicitly written registered workflow name, longest first."""
    candidates = sorted(
        RUN_ACTIONS,
        key=lambda action: len(ACTION_DEFINITIONS[action].workflow),
        reverse=True,
    )
    for action in candidates:
        words = re.split(r"[-_\s]+", ACTION_DEFINITIONS[action].workflow.casefold())
        pattern = (
            r"(?<![a-z0-9])"
            + r"[\s_-]*".join(re.escape(word) for word in words)
            + r"(?![a-z0-9])"
        )
        if re.search(pattern, task.casefold()):
            return action
    return None


def apply_outcome_match(decision: TaskDecision) -> TaskDecision:
    """Replace all workflow-match fields with deterministic registry results."""
    if decision.requested_outcome is None:
        return decision.model_copy(
            update={
                "capability_match_status": None,
                "matched_actions": [],
                "recommended_actions": [],
                "alternative_actions": [],
                "mismatch_dimensions": [],
                "clarification_question": decision.clarification_question,
            }
        )
    match = match_requested_outcome(decision.requested_outcome)
    guidance = (
        guidance_actions_for(match.matched_actions[0])
        if len(match.matched_actions) == 1
        else []
    )
    return decision.model_copy(
        update={
            "capability_match_status": match.status,
            "matched_actions": match.matched_actions,
            "recommended_actions": guidance,
            "alternative_actions": match.alternative_actions,
            "mismatch_dimensions": match.mismatch_dimensions,
            "clarification_question": match.clarification_question,
        }
    )


__all__ = [
    "apply_outcome_match",
    "guidance_actions_for",
    "has_granularity_only_ambiguity",
    "match_outcome_hypotheses",
    "match_requested_outcome",
    "named_workflow_action",
]
