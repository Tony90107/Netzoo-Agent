"""Assemble validated semantic, registry, and intent facts into one task decision."""

from __future__ import annotations

from ..contracts import IntentDecision, TaskDecision
from ..contracts.outcomes import CapabilityMatch, SemanticInterpretation
from workflow_registry import ACTION_DEFINITIONS, OUTPUT_CAPABILITIES
from ..routing.outcome_matching import guidance_actions_for
from ..routing.capability import validate_task_text
from .outcome_consistency import select_primary_hypothesis
from .registry_guidance import preferred_registry_composition_actions
from ..handoff import build_bonobo_handoff

__all__ = ["assemble_task_decision"]


def assemble_task_decision(
    interpretation: SemanticInterpretation,
    match: CapabilityMatch,
    intent: IntentDecision,
    *,
    task: str,
) -> TaskDecision:
    """Combine facts in authority order without letting intent choose a workflow."""
    primary = select_primary_hypothesis(interpretation.outcome_hypotheses)
    exact_action = (
        match.matched_actions[0]
        if match.status == "exact" and len(match.matched_actions) == 1
        else None
    )
    semantic_execution_missing = interpretation.request_mode != "execute"
    execute = (
        intent.mode == "execute"
        and exact_action is not None
        and not semantic_execution_missing
    )
    execution_rejection = (
        "Semantic interpretation did not classify this request as explicit execution; "
        "no analysis was authorized."
        if semantic_execution_missing and intent.mode == "execute"
        else None
    )
    rejection = (
        validate_task_text(
            task,
            exact_action,
            matched_actions=match.matched_actions,
        )
        if execute and exact_action is not None
        else None
    )
    if rejection:
        execute = False
    recommended_actions = (
        guidance_actions_for(match.matched_actions[0])
        if match.status in {"exact", "fallback"} and len(match.matched_actions) == 1
        and match.matched_actions[0] in OUTPUT_CAPABILITIES
        else []
    )
    workflow_candidates = list(
        dict.fromkeys(
            [
                *match.matched_actions,
                *match.hypothesis_actions,
                *match.alternative_actions,
            ]
        )
    )
    candidate_actions = [*workflow_candidates[:5], "no_tool"]
    clarification = match.clarification_question
    # An assumed outcome names one candidate and a complete requested result;
    # the only thing withheld is the exact-match claim, so there is nothing for
    # this question to collect.
    if (
        intent.mode == "execute"
        and exact_action is None
        and not clarification
        and match.match_basis != "assumed_outcome"
    ):
        clarification = "What supported NetZoo result do you want the agent to produce?"

    decision = TaskDecision(
        action=exact_action if execute else "no_tool",
        in_scope=match.status != "unsupported",
        should_execute=execute,
        intent_type="run_analysis" if execute else "answer_question",
        confidence=intent.confidence,
        reason=execution_rejection or rejection or intent.reason,
        candidate_actions=candidate_actions,
        recommended_actions=recommended_actions,
        requested_outcome=primary.outcome if primary else None,
        outcome_hypotheses=interpretation.outcome_hypotheses,
        capability_match_status=match.status,
        match_basis=match.match_basis,
        rejected_methods=match.rejected_methods,
        matched_actions=match.matched_actions,
        hypothesis_actions=match.hypothesis_actions,
        alternative_actions=match.alternative_actions,
        mismatch_dimensions=match.mismatch_dimensions,
        clarification_question=clarification,
    )
    bonobo_handoff = build_bonobo_handoff(task, decision, ACTION_DEFINITIONS)
    if bonobo_handoff is not None:
        if bonobo_handoff.status != "validated":
            return decision.model_copy(
                update={
                    "action": "no_tool",
                    "should_execute": False,
                    "intent_type": "answer_question",
                    "reason": bonobo_handoff.reason,
                    "recommended_actions": ["run_bonobo"],
                }
            )
        decision = decision.model_copy(
            update={
                "recommended_actions": [
                    "run_bonobo",
                    *(item for item in [bonobo_handoff.consumer_action] if item),
                ],
            }
        )
    composition_actions = preferred_registry_composition_actions(
        task,
        decision,
        ACTION_DEFINITIONS,
    )
    has_direct_artifact_handoff = any(
        consumer in ACTION_DEFINITIONS[producer].output_capability.handoff_targets
        for producer, consumer in zip(
            composition_actions,
            composition_actions[1:],
        )
        if ACTION_DEFINITIONS[producer].output_capability is not None
    )
    if execute and has_direct_artifact_handoff:
        return decision.model_copy(
            update={
                "action": "no_tool",
                "should_execute": False,
                "intent_type": "answer_question",
                "reason": (
                    "The registered artifact handoff requires stage-by-stage "
                    "preparation. NetZoo will plan, inspect, confirm, and execute "
                    "the producer before it validates a ready downstream plan."
                ),
                "recommended_actions": composition_actions,
            }
        )
    return decision.model_copy(update={"recommended_actions": composition_actions})
