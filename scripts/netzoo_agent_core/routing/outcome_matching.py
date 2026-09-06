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
from ..contracts.artifact_semantics import outcome_consistency_issues
from ..interpretation.request_integrity import _scoped_clauses, input_mentions
from .method_rejections import rejected_methods_for


_UNKNOWN = "unknown"


def _produced_artifacts(
    capability: OutputCapabilityDefinition,
) -> frozenset[str]:
    """Return every artifact a workflow can deliberately expose to the user."""
    return capability.produced_artifacts or frozenset({capability.artifact_type})


def _accepts_inputs(outcome: RequestedOutcome, capability: OutputCapabilityDefinition) -> bool:
    requested = set(outcome.input_artifacts) - {_UNKNOWN}
    return (
        requested.issubset(capability.input_artifacts)
        and not requested.intersection(capability.incompatible_input_artifacts)
    )


def explicit_input_artifacts(task: str) -> frozenset[str]:
    """Share the validator's current-input scope, including on fallback paths."""
    return frozenset(
        mention.artifact for mention in input_mentions(task)
        if mention.status == "current"
    )


def match_registry_guidance_features(
    task: str,
    capabilities=OUTPUT_CAPABILITIES,
    *,
    input_artifacts: Sequence[str] | None = None,
) -> CapabilityMatch | None:
    """Recover one read-only capability from multiple registry-owned signals.

    This is deliberately stricter than keyword routing: a workflow must have at
    least two independent capability signals, be the unique top score, and not
    reject an explicitly named input artifact. The result grants guidance only;
    execution authorization remains downstream.
    """
    normalized = task.casefold()
    task_inputs = (
        explicit_input_artifacts(task)
        if input_artifacts is None else frozenset(input_artifacts)
    )
    ranked: list[tuple[int, int, RecommendedAction]] = []
    for index, (action, capability) in enumerate(capabilities.items()):
        incompatible_inputs = frozenset(capability.incompatible_input_artifacts)
        compatible_inputs = task_inputs & frozenset(capability.input_artifacts)
        if input_artifacts is not None and (
            task_inputs & incompatible_inputs
            or not task_inputs.issubset(capability.input_artifacts)
        ):
            continue
        if task_inputs & incompatible_inputs and not compatible_inputs:
            continue
        phrase_hits = {
            phrase.casefold()
            for phrase in capability.selection_phrases
            if phrase.casefold() in normalized
        }
        input_hits = compatible_inputs
        evidence_count = len(phrase_hits) + len(input_hits)
        if evidence_count < 2:
            continue
        score = 3 * len(input_hits) + 2 * len(phrase_hits)
        ranked.append((score, -index, action))
    if not ranked:
        return None
    ranked.sort(reverse=True)
    if len(ranked) > 1 and ranked[0][0] == ranked[1][0]:
        return None
    return CapabilityMatch(status="fallback", match_basis="registry_features", matched_actions=[ranked[0][2]])


def _is_not_applicable(outcome: RequestedOutcome) -> bool:
    return (
        outcome.operation == _UNKNOWN
        and outcome.artifact_type == _UNKNOWN
        and outcome.granularity == "not_applicable"
        and not outcome.input_artifacts
        and not outcome.entity_types
        and not outcome.regulator_types
        and not outcome.target_types
        and not outcome.unresolved_dimensions
    )


def _has_unknown(outcome: RequestedOutcome) -> bool:
    return bool(
        outcome.unresolved_dimensions
        or _UNKNOWN in {outcome.operation, outcome.artifact_type, outcome.granularity}
        or _UNKNOWN in outcome.entity_types
        or _UNKNOWN in outcome.input_artifacts
        or _UNKNOWN in outcome.regulator_types
        or _UNKNOWN in outcome.target_types
    )


def _matches(
    outcome: RequestedOutcome,
    capability: OutputCapabilityDefinition,
) -> bool:
    if _has_unknown(outcome) or outcome_consistency_issues(outcome):
        return False
    return (
        outcome.operation == capability.operation
        and _accepts_inputs(outcome, capability)
        and outcome.artifact_type in _produced_artifacts(capability)
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
        and _accepts_inputs(outcome, capability)
        and (
            outcome.artifact_type == _UNKNOWN
            or outcome.artifact_type in _produced_artifacts(capability)
        )
        and (
            outcome.granularity == _UNKNOWN
            or outcome.granularity in capability.granularities
        )
        and _known_set_matches(outcome.entity_types, capability.entity_types)
        and _known_set_matches(outcome.regulator_types, capability.regulator_types)
        and _known_set_matches(outcome.target_types, capability.target_types)
    )


def _complete_guidance_match(outcome, capability) -> bool:
    """Only explanatory operation may be omitted for an exact guidance match."""
    return _matches(outcome.model_copy(update={
        "operation": capability.operation,
        "unresolved_dimensions": [value for value in outcome.unresolved_dimensions if value != "operation"],
    }), capability)


def _explicit_evidence_values(
    hypothesis: OutcomeHypothesis,
) -> dict[str, set[str]]:
    """Group user-quoted semantic constraints independently of model inferences."""
    grouped: dict[str, set[str]] = {}
    for item in hypothesis.evidence:
        if item.source != "explicit" or item.value == _UNKNOWN:
            continue
        grouped.setdefault(item.dimension, set()).add(item.value)
    return grouped


def _matches_explicit_evidence(
    evidence: Mapping[str, set[str]],
    capability: OutputCapabilityDefinition,
) -> bool:
    """Treat explicit user evidence as hard constraints on registry capabilities."""
    scalar_constraints = (
        ("operation", {capability.operation}),
        ("input_artifact", set(capability.input_artifacts) - set(capability.incompatible_input_artifacts)),
        ("artifact_type", set(_produced_artifacts(capability))),
        ("granularity", set(capability.granularities)),
        ("entity_type", set(capability.entity_types)),
        ("regulator_type", set(capability.regulator_types)),
        ("target_type", set(capability.target_types)),
    )
    return all(
        not evidence.get(dimension)
        or evidence[dimension].issubset(supported)
        for dimension, supported in scalar_constraints
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
    if outcome.input_artifacts and not any(
        _accepts_inputs(outcome, item)
        and (outcome.artifact_type == _UNKNOWN or outcome.artifact_type in _produced_artifacts(item))
        for item in values
    ):
        mismatches.append("input_artifacts")
    if not any(
        outcome.artifact_type in _produced_artifacts(item) for item in values
    ):
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
    issues = outcome_consistency_issues(outcome)
    if issues:
        return CapabilityMatch(status="unsupported", mismatch_dimensions=list(issues))
    if _is_not_applicable(outcome):
        return CapabilityMatch(status="not_applicable")
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


def _explicit_evidence_specificity_penalty(
    evidence: Mapping[str, set[str]],
    capability: OutputCapabilityDefinition,
) -> int:
    """Rank evidence-compatible candidates without reintroducing inferred fields."""
    requested_entities = evidence.get("entity_type", set())
    requested_regulators = evidence.get("regulator_type", set())
    requested_targets = evidence.get("target_type", set())
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
            tuple(sorted(item.input_artifacts)),
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


def _stated_dimensions_match(
    outcome: RequestedOutcome, capability: OutputCapabilityDefinition,
) -> bool:
    """Whether every dimension the outcome actually states matches.

    `unknown` means the outcome does not constrain that dimension, so it cannot
    disqualify a capability. Guidance requests reach the matcher with their
    operation deliberately blanked -- asking which capability can produce a
    result is not itself an operation -- so requiring an operation here would
    require what the caller just removed.
    """
    return (
        outcome.operation in {_UNKNOWN, capability.operation}
        and outcome.artifact_type in {_UNKNOWN, capability.artifact_type}
        and (
            capability.granularities is None
            or outcome.granularity in {_UNKNOWN, *capability.granularities}
        )
    )


def _tag_discriminated_action(
    hypotheses: Sequence[OutcomeHypothesis],
    candidates: Sequence[RecommendedAction],
    capabilities: Mapping[RecommendedAction, OutputCapabilityDefinition],
    ignore_tags: frozenset[str] = frozenset(),
) -> RecommendedAction | None:
    """Break a tie with the registry tags the outcome declared, or return None.

    `selection_tags` is defined by the contract, requested by the prompt and
    checked by the evidence validator, and the matcher never read it. A round on
    a stronger model made that visible: it expressed the one discriminating fact
    as a registry tag rather than as a regulator role, and two equally
    compatible capabilities stayed tied with no action at all.

    The contract says tags "do not select or authorize a workflow by
    themselves", so this only chooses among candidates the scientific dimensions
    have already qualified: a survivor must carry every declared tag *and* match
    each dimension the outcome states. The set can only shrink -- no capability
    becomes reachable that was not already a candidate, and one whose stated
    dimensions differ is never rescued.

    Known limitation, accepted deliberately and pinned by a test: a tag the
    request does not support still discriminates, because tags need no evidence.
    Sixteen of sixteen tags in the live record were catalogue entries naming the
    expected tool, and the live criterion vetoes on any wrong recommendation.
    """
    # A tag the harness moved into the field is bookkeeping, not a choice the
    # model made about the outcome, and a repair must never pick a tool.
    declared = {
        tag for item in hypotheses for tag in item.outcome.selection_tags
    } - ignore_tags
    if not declared or len(candidates) < 2:
        return None
    outcomes = [item.outcome for item in hypotheses]
    survivors = [
        action for action in candidates
        if (capability := capabilities.get(action)) is not None
        and declared <= capability.selection_tags
        and any(_stated_dimensions_match(outcome, capability) for outcome in outcomes)
    ]
    return survivors[0] if len(survivors) == 1 else None


def match_outcome_hypotheses(
    hypotheses: Sequence[OutcomeHypothesis],
    capabilities: Mapping[
        RecommendedAction, OutputCapabilityDefinition
    ] = OUTPUT_CAPABILITIES,
    *,
    assumed_guidance: bool = False,
    ignore_tags: frozenset[str] = frozenset(),
) -> CapabilityMatch:
    """Match complete outcomes strictly and incomplete hypotheses advisably."""
    issues = list(dict.fromkeys(
        issue for item in hypotheses for issue in outcome_consistency_issues(item.outcome)
    ))
    if issues:
        return CapabilityMatch(status="unsupported", mismatch_dimensions=issues[:5])
    if hypotheses and all(_is_not_applicable(item.outcome) for item in hypotheses):
        return CapabilityMatch(status="not_applicable")
    exact: list[RecommendedAction] = []
    assumed_exact: list[RecommendedAction] = []
    evidence_exact: list[RecommendedAction] = []
    advisory: list[tuple[int, float, int, int, RecommendedAction]] = []
    for hypothesis in hypotheses:
        strict = match_requested_outcome(hypothesis.outcome, capabilities)
        if strict.status == "exact":
            # An assumption marks an unconfirmed interpretation of the request,
            # so it can never yield an exact match. It is still a single named
            # candidate, and withholding the registry guidance leaves the user
            # with less than an outright interpretation failure would give.
            (exact if not hypothesis.assumptions else assumed_exact).extend(
                strict.matched_actions
            )
        score = _hypothesis_evidence_score(hypothesis)
        explicit_evidence = _explicit_evidence_values(hypothesis)
        if strict.status != "exact" and explicit_evidence.get("artifact_type"):
            explicit_candidates = [
                (index, action, capability)
                for index, (action, capability) in enumerate(capabilities.items())
                if _matches_explicit_evidence(explicit_evidence, capability)
            ]
            if len(explicit_candidates) == 1:
                evidence_exact.append(explicit_candidates[0][1])
            else:
                advisory.extend(
                    (
                        score,
                        hypothesis.confidence,
                        -_explicit_evidence_specificity_penalty(
                            explicit_evidence,
                            capability,
                        ),
                        index,
                        action,
                    )
                    for index, action, capability in explicit_candidates
                )
        for index, (action, capability) in enumerate(capabilities.items()):
            if _partially_compatible(hypothesis.outcome, capability):
                advisory.append(
                    (
                        score,
                        hypothesis.confidence,
                        -_advisory_specificity_penalty(
                            hypothesis.outcome,
                            capability,
                        ),
                        index,
                        action,
                    )
                )

    unique_exact = list(dict.fromkeys([*exact, *evidence_exact]))
    if len(unique_exact) == 1:
        return CapabilityMatch(
            status="exact" if unique_exact[0] in exact else "fallback",
            match_basis="semantic" if unique_exact[0] in exact else "partial_evidence",
            matched_actions=unique_exact,
        )
    unique_assumed = list(dict.fromkeys(assumed_exact))
    # Only a lone, fully determined hypothesis may be surfaced this way. Several
    # hypotheses, or one that is still underdetermined, describe a real choice
    # the user has to make, and an execution request must gain no candidate at
    # all from an unconfirmed interpretation.
    if (
        assumed_guidance
        and len(hypotheses) == 1
        and not unique_exact
        and len(unique_assumed) == 1
    ):
        return CapabilityMatch(
            status="fallback",
            match_basis="assumed_outcome",
            matched_actions=unique_assumed,
            hypothesis_actions=unique_assumed,
        )
    if advisory:
        top_score = max(item[:3] for item in advisory)
        top_actions = [
            action
            for evidence_score, confidence, specificity_score, _, action in sorted(
                advisory,
                key=lambda item: item[3],
            )
            if (evidence_score, confidence, specificity_score) == top_score
        ]
        unique_top_actions = list(dict.fromkeys(top_actions))
        discriminated = _tag_discriminated_action(
            hypotheses, unique_top_actions, capabilities, ignore_tags,
        )
        if discriminated is not None:
            return CapabilityMatch(
                status="exact",
                match_basis="registry_features",
                matched_actions=[discriminated],
            )
        return CapabilityMatch(
            status="ambiguous",
            hypothesis_actions=unique_top_actions,
            clarification_question=(
                (
                    _granularity_only_question(hypotheses)
                    or "Which compatible network result do you mean?"
                )
                if len(unique_top_actions) > 1
                else None
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


def _workflow_name_pattern(action: str) -> str:
    words = re.split(r"[-_\s]+", ACTION_DEFINITIONS[action].workflow.casefold())
    return (
        r"(?<![a-z0-9])"
        + r"[\s_-]*".join(re.escape(word) for word in words)
        + r"(?![a-z0-9])"
    )


def _current_scope_text(task: str) -> str:
    """Return the request minus its historical clauses.

    A workflow the user reports having already run is not the workflow being
    asked about. `_match_semantic_request` already refuses to let a historical
    mention override a compatible typed outcome, but that guard needs an outcome
    to protect; after semantic validation fails there is none, and a live round
    recommended a forbidden PANDA to a request whose only mention of it was
    "Previously I used PANDA" and which said it did not want inferred networks.

    The clause scoping is the same deterministic pass `input_mentions` uses, so
    history is recognised here exactly as it is for input artifacts.
    """
    return " ".join(
        clause for clause, scope in _scoped_clauses(task) if scope != "historical"
    )


def named_workflow_action(task: str) -> RecommendedAction | None:
    """Resolve a currently written registered workflow name, longest first."""
    candidates = sorted(
        RUN_ACTIONS,
        key=lambda action: len(ACTION_DEFINITIONS[action].workflow),
        reverse=True,
    )
    current = _current_scope_text(task).casefold()
    for action in candidates:
        if re.search(_workflow_name_pattern(action), current):
            return action
    return None


def named_registered_action(task: str):
    """Resolve an explicitly written registry workflow label, longest first."""
    candidates = sorted(
        (
            (action, definition)
            for action, definition in ACTION_DEFINITIONS.items()
            if action != "no_tool"
        ),
        key=lambda item: len(item[1].workflow),
        reverse=True,
    )
    for action, definition in candidates:
        words = re.split(r"[-_\s]+", definition.workflow.casefold())
        pattern = (
            r"(?<![a-z0-9])"
            + r"[\s_-]*".join(re.escape(word) for word in words)
            + r"(?![a-z0-9])"
        )
        if re.search(pattern, task.casefold()):
            return action
    return None


def _enforce_input_compatibility(
    task: str,
    match: CapabilityMatch,
    *,
    request_mode: str,
    input_artifacts: Sequence[str] | None = None,
) -> CapabilityMatch:
    """Prevent a typed or named match from accepting a declared bad input."""
    if match.status != "exact":
        return match
    task_inputs = (
        explicit_input_artifacts(task)
        if input_artifacts is None else frozenset(input_artifacts)
    )
    incompatible_actions = [
        action
        for action in match.matched_actions
        if action in OUTPUT_CAPABILITIES
        and (
            task_inputs & OUTPUT_CAPABILITIES[action].incompatible_input_artifacts
            or (
                input_artifacts is not None
                and not task_inputs.issubset(OUTPUT_CAPABILITIES[action].input_artifacts)
            )
        )
    ]
    if not incompatible_actions:
        return match
    if request_mode == "guidance":
        registry_guidance = match_registry_guidance_features(
            task, OUTPUT_CAPABILITIES, input_artifacts=input_artifacts,
        )
        if registry_guidance is not None:
            return registry_guidance
    return CapabilityMatch(
        status="unsupported",
        mismatch_dimensions=["input_artifact"],
        clarification_question=(
            "The named input artifact is incompatible with the matched workflow. "
            "Which compatible data type should NetZoo analyze?"
        ),
    )


def _match_semantic_request(
    task: str,
    hypotheses: Sequence[OutcomeHypothesis],
    *,
    request_mode: str = "unknown",
    ignore_tags: frozenset[str] = frozenset(),
) -> CapabilityMatch:
    """Match typed meaning, using explicit registry identifiers only as a fallback."""
    marker = re.search(
        r"(?:CONFIRMED_OUTCOME_ACTION|PREVIOUS_ACTION)=(run_[a-z_]+)",
        task,
        flags=re.IGNORECASE,
    )
    if marker:
        action = marker.group(1).casefold()
        if action in OUTPUT_CAPABILITIES:
            return CapabilityMatch(status="exact", match_basis="confirmed_context", matched_actions=[action])

    current_inputs = (
        sorted({
            artifact for hypothesis in hypotheses
            for artifact in hypothesis.outcome.input_artifacts
            if artifact != _UNKNOWN
        })
        if any(hypothesis.outcome.input_artifacts for hypothesis in hypotheses)
        else None
    )
    matching_hypotheses = hypotheses
    if request_mode == "guidance":
        # Guidance asks which registered capability can produce the result; the
        # explanatory wording is not itself a workflow operation.
        matching_hypotheses = [
            hypothesis.model_copy(
                update={
                    "outcome": hypothesis.outcome.model_copy(
                        update={"operation": _UNKNOWN}
                    )
                }
            )
            for hypothesis in hypotheses
        ]
    match = match_outcome_hypotheses(
        matching_hypotheses,
        OUTPUT_CAPABILITIES,
        assumed_guidance=request_mode != "execute",
        ignore_tags=ignore_tags,
    )
    if match.status == "fallback" and match.match_basis == "partial_evidence":
        capability = OUTPUT_CAPABILITIES[match.matched_actions[0]]
        if request_mode == "guidance" and all(
            _complete_guidance_match(item.outcome, capability)
            for item in matching_hypotheses
        ):
            match = match.model_copy(update={"status": "exact", "match_basis": "semantic"})
        else:
            return match
    if match.status == "exact":
        return _enforce_input_compatibility(
            task,
            match,
            request_mode=request_mode,
            input_artifacts=current_inputs,
        )

    if (
        request_mode == "guidance"
        and match.status == "ambiguous"
        and len(hypotheses) == 1
        and len(match.hypothesis_actions) == 1
        and not any(
            not _complete_guidance_match(
                hypothesis.outcome,
                OUTPUT_CAPABILITIES[match.hypothesis_actions[0]],
            )
            for hypothesis in hypotheses
        )
    ):
        # A guidance question may omit the operation because it asks which
        # workflow to use. If every other requested dimension points to one
        # registry capability, expose that capability as an exact *guidance*
        # match. `assemble_task_decision` still blocks execution whenever the
        # semantic request mode is not `execute`.
        promoted = CapabilityMatch(
            status="exact",
            matched_actions=list(match.hypothesis_actions),
        )
        return _enforce_input_compatibility(
            task,
            promoted,
            request_mode=request_mode,
            input_artifacts=current_inputs,
        )

    if request_mode == "guidance":
        registry_guidance = match_registry_guidance_features(
            task, OUTPUT_CAPABILITIES, input_artifacts=current_inputs,
        )
        if registry_guidance is not None:
            return registry_guidance

    # A workflow name is a fallback identifier, not stronger evidence than the
    # requested scientific result. This keeps historical, questioned, or rejected
    # method mentions from overriding a uniquely compatible typed outcome.
    explicit_action = named_registered_action(task)
    if explicit_action is not None:
        capability = OUTPUT_CAPABILITIES.get(explicit_action)
        if capability is not None and matching_hypotheses and not any(
            _partially_compatible(hypothesis.outcome, capability)
            for hypothesis in matching_hypotheses
        ):
            # A name may disambiguate compatible methods, never redefine a
            # known output or bypass an input contract.
            return match
        named_match = CapabilityMatch(
            status="exact" if capability is None or match.status == "ambiguous" and matching_hypotheses and all(
                _complete_guidance_match(item.outcome, capability)
                if request_mode == "guidance" else _matches(item.outcome, capability)
                for item in matching_hypotheses
            ) else "fallback",
            match_basis="workflow_name", matched_actions=[explicit_action]
        )
        return _enforce_input_compatibility(
            task,
            named_match,
            request_mode=request_mode,
            input_artifacts=current_inputs,
        )
    return match


def match_semantic_request(
    task: str,
    hypotheses: Sequence[OutcomeHypothesis],
    *,
    request_mode: str = "unknown",
    ignore_tags: frozenset[str] = frozenset(),
) -> CapabilityMatch:
    """Carry rejected methods alongside the selected semantic or advisory path."""
    match = _match_semantic_request(
        task, hypotheses, request_mode=request_mode, ignore_tags=ignore_tags,
    )
    if match.status == "exact" and any(outcome_consistency_issues(item.outcome) for item in hypotheses):
        match = CapabilityMatch(status="unsupported", mismatch_dimensions=["outcome_consistency"])
    inputs = sorted({artifact for item in hypotheses for artifact in item.outcome.input_artifacts})
    rejections = rejected_methods_for(task, inputs, actions=match.matched_actions)
    rejected_actions = {item.action for item in rejections}
    if rejected_actions.intersection(match.matched_actions):
        match = CapabilityMatch(status="unsupported", mismatch_dimensions=["input_artifacts"])
    return match.model_copy(update={"rejected_methods": rejections})


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
    "explicit_input_artifacts",
    "guidance_actions_for",
    "has_granularity_only_ambiguity",
    "match_outcome_hypotheses",
    "match_semantic_request",
    "match_requested_outcome",
    "match_registry_guidance_features",
    "named_workflow_action",
    "named_registered_action",
]
