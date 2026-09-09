"""Deterministic matching between requested outcomes and workflow capabilities."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re

from workflow_registry import (
    ACTION_BY_METHOD_LABEL,
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
from .candidate_ranking import (
    _advisory_specificity_penalty, _explicit_evidence_specificity_penalty,
    _hypothesis_evidence_score, _specificity_score, stated_dimension_score,
)
from .method_rejections import rejected_methods_for
from .named_labels import (
    _current_scope_text,
    _workflow_name_pattern,
    named_registered_action,
    named_workflow_action,
    solely_named_run_action,
)


# Defined beside the ranking preferences that also need it.
from .candidate_ranking import _UNKNOWN  # noqa: E402


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
    """Deprecated compatibility entry point; lexical hits are not tool evidence."""
    return None


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
        winner = dict(candidates)[ranked[0][2]]
        # It has to win the ranking, and win it on something the request said.
        # Without the second half this system's own preference for the narrower
        # capability settles the choice and the result is still reported as an
        # exact match, so a run that named no distinguishing dimension scored
        # exactly like one that did. The preference still orders candidates; it
        # just no longer certifies the answer.
        if len(ranked) == 1 or (
            ranked[0][0] < ranked[1][0]
            and all(
                stated_dimension_score(outcome, winner)
                < stated_dimension_score(outcome, capability)
                for action, capability in candidates if action != ranked[0][2]
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
        mismatch_dimensions=_mismatch_dimensions(outcome, capabilities),
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
    if len(survivors) == 1:
        return survivors[0]
    # Nested tag sets: three capabilities carry a superset of a baseline's tags
    # (OTTER and GIRAFFE over PANDA, BONOBO over LIONESS-coexpression), so
    # "exactly one survivor" could never select the baseline and PANDA was
    # unreachable outright. A request naming no specialisation is asking for the
    # baseline, so the unique minimum under subset order wins; no unique minimum
    # leaves the tie unresolved.
    minimal = [
        action for action in survivors
        if all(
            capabilities[action].selection_tags <= capabilities[other].selection_tags
            for other in survivors
        )
    ]
    return minimal[0] if len(minimal) == 1 else None


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


def _compatible_candidate_count(
    outcome, capabilities=OUTPUT_CAPABILITIES,
) -> int:
    """How many registered capabilities the typed outcome is compatible with.

    `match_requested_outcome` reports `exact` both when one capability is
    compatible and when several are and a specificity preference picks a winner.
    Those are different claims, and only the first should outrank an explicit
    workflow name.
    """
    return sum(1 for capability in capabilities.values() if _matches(outcome, capability))


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
        # `exact` means two different things here: exactly one capability is
        # compatible, or several are and `_specificity_score` picked a winner.
        # Only the first outranks an explicit workflow name. Left conflated, a
        # request naming LIONESS-COEXPRESSION for execution resolved to BONOBO,
        # because the preference favours the narrower granularity set and this
        # early return runs before name disambiguation is even reached.
        named = named_registered_action(_current_scope_text(task))
        if (
            named is not None
            and named not in match.matched_actions
            and (named_capability := OUTPUT_CAPABILITIES.get(named)) is not None
            and matching_hypotheses
            and all(
                _matches(item.outcome, named_capability)
                for item in matching_hypotheses
            )
            and any(
                _compatible_candidate_count(item.outcome) > 1
                for item in matching_hypotheses
            )
        ):
            match = CapabilityMatch(
                status="exact",
                match_basis="workflow_name",
                matched_actions=[named],
            )
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


    # The reading itself says the request named a method, and the contract has
    # already held that claim to an explicit quote which is in the request and
    # contains the label. So this is the model's judgement, checked, rather than
    # a scan of the text: the interpretation decided that the mention is what the
    # user wants run rather than work they have finished, and the registry -- not
    # the model, and not this function -- says what that method produces.
    #
    # Two named methods are a question, not a fact, and fall through to the
    # ordinary ambiguity handling. A reading that contradicts the method it names
    # never reaches here: `named_method_conflict` rejects it during validation.
    asserted = {
        label for hypothesis in matching_hypotheses
        for label in hypothesis.outcome.named_methods
    }
    if len(asserted) == 1:
        action = ACTION_BY_METHOD_LABEL.get(next(iter(asserted)))
        capability = OUTPUT_CAPABILITIES.get(action) if action else None
        if capability is not None and all(
            _partially_compatible(hypothesis.outcome, capability)
            for hypothesis in matching_hypotheses
        ):
            return _enforce_input_compatibility(
                task,
                CapabilityMatch(
                    status="exact", match_basis="named_method",
                    matched_actions=[action],
                ),
                request_mode=request_mode,
                input_artifacts=current_inputs,
            )

    # Nothing was interpreted at all. A reading with every dimension unknown is
    # how this system encodes "out of scope", and the interpreter also produces
    # it whenever the request states something the outcome vocabulary has no
    # dimension for -- a method name being exactly that. When the requester wrote
    # one runnable label out by name, that label is the only fact the request
    # contains, it cannot contradict a reading that claims nothing, and reporting
    # the capability as unavailable is the one answer certain to be wrong.
    #
    # This is a registry lookup, not the phrase-count guess removed in `15cbaad`:
    # the label is matched on word boundaries after historical clauses are
    # stripped, two labels resolve to none, and the input contract below still
    # applies. Where the reading claims anything at all, the rule underneath is
    # untouched and a typed outcome still outranks a name.
    if hypotheses and all(_is_not_applicable(item.outcome) for item in hypotheses):
        sole_action = solely_named_run_action(task)
        if sole_action is not None:
            return _enforce_input_compatibility(
                task,
                CapabilityMatch(
                    status="exact", match_basis="workflow_name",
                    matched_actions=[sole_action],
                ),
                request_mode=request_mode,
                input_artifacts=current_inputs,
            )

    # A workflow name is a fallback identifier, not stronger evidence than the
    # requested scientific result. This keeps historical, questioned, or rejected
    # method mentions from overriding a uniquely compatible typed outcome.
    explicit_action = named_registered_action(_current_scope_text(task))
    if explicit_action is not None:
        capability = OUTPUT_CAPABILITIES.get(explicit_action)
        if capability is not None and matching_hypotheses and not any(
            _partially_compatible(hypothesis.outcome, capability)
            for hypothesis in matching_hypotheses
        ):
            # A name may disambiguate compatible methods, never redefine a
            # known output or bypass an input contract.
            return match
        # `exact` from a specificity preference among several compatible
        # capabilities is not the "uniquely compatible typed outcome" the rule
        # above means to protect. Left as-is it silently outranked an explicit
        # name: an execute request naming LIONESS-COEXPRESSION resolved to
        # BONOBO. Where exactly one capability is compatible, nothing changes.
        preference_resolved = match.status == "exact" and any(
            _compatible_candidate_count(item.outcome) > 1
            for item in matching_hypotheses
        )
        named_match = CapabilityMatch(
            status="exact" if capability is None or (
                match.status == "ambiguous" or preference_resolved
            ) and matching_hypotheses and all(
                _complete_guidance_match(item.outcome, capability)
                if request_mode == "guidance" else _matches(item.outcome, capability)
                for item in matching_hypotheses
            ) else "fallback",
            match_basis="workflow_name", matched_actions=[explicit_action]
        )
        if named_match.status != "exact":
            return match
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
