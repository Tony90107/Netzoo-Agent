"""Assemble validated semantic, registry, and intent facts into one task decision."""

from __future__ import annotations

from ..contracts import IntentDecision, TaskDecision
from ..contracts.outcomes import CapabilityMatch, SemanticInterpretation
from workflow_registry import OUTPUT_CAPABILITIES
from ..routing.outcome_matching import guidance_actions_for
from ..routing.capability import validate_task_text
from .outcome_consistency import select_primary_hypothesis

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
    execute = intent.mode == "execute" and exact_action is not None
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
        guidance_actions_for(exact_action)
        if exact_action is not None and exact_action in OUTPUT_CAPABILITIES
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
    if intent.mode == "execute" and exact_action is None and not clarification:
        clarification = "What supported NetZoo result do you want the agent to produce?"

    return TaskDecision(
        action=exact_action if execute else "no_tool",
        in_scope=match.status != "unsupported",
        should_execute=execute,
        intent_type="run_analysis" if execute else "answer_question",
        confidence=intent.confidence,
        reason=rejection or intent.reason,
        candidate_actions=candidate_actions,
        recommended_actions=recommended_actions,
        requested_outcome=primary.outcome if primary else None,
        outcome_hypotheses=interpretation.outcome_hypotheses,
        capability_match_status=match.status,
        matched_actions=match.matched_actions,
        hypothesis_actions=match.hypothesis_actions,
        alternative_actions=match.alternative_actions,
        mismatch_dimensions=match.mismatch_dimensions,
        clarification_question=clarification,
    )
