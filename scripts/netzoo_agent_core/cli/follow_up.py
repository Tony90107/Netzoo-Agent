"""Outcome-aware next-turn interaction."""

from __future__ import annotations

import re

from workflow_registry import (
    ACTION_DEFINITIONS,
    OUTPUT_CAPABILITIES,
    REQUIRED_INPUTS,
    workflow_name as _workflow_name,
)

from ..contracts import (
    ContextualReplyResolution,
    FollowUpContext,
    NextTurnPrompt,
    OUTPUT_ROLE_FIELDS,
    PlanEvaluationResult,
    TaskDecision,
    ToolExecutionResult,
    WorkflowConversationFact,
    WorkflowPlan,
    _ui_text,
)
from ..interpretation import INPUT_LABELS
from ..outcomes import effective_results, terminal_failed

__all__ = [
    "initial_next_turn_prompt",
    "build_follow_up_context",
    "build_next_turn_prompt",
    "render_next_turn_prompt",
    "follow_up_returns_to_main",
    "resolve_next_turn_input",
]


def initial_next_turn_prompt() -> NextTurnPrompt:
    return NextTurnPrompt(
        kind="initial",
        question=_ui_text("What would you like to accomplish with NetZoo?"),
    )


def build_next_turn_prompt(state: dict) -> NextTurnPrompt:
    """Choose the next CLI question from the completed turn's structured outcome."""
    plan = WorkflowPlan.model_validate(state["plan"])
    decision = TaskDecision.model_validate(plan.decision)
    plan_evaluation = (
        PlanEvaluationResult.model_validate(state["plan_evaluation"])
        if state.get("plan_evaluation")
        else None
    )
    results = [
        ToolExecutionResult.model_validate(item)
        for item in state.get("tool_results", [])
    ]
    results = effective_results(results)
    result_evaluation = state.get("evaluation")
    semantic_goal = state.get("semantic_goal") or {}
    semantic_candidates = semantic_goal.get("candidates") or []
    semantic_relationship = semantic_goal.get("relationship")
    request_mode = semantic_goal.get("request_mode")

    if plan_evaluation and plan_evaluation.status == "rejected":
        return NextTurnPrompt(
            kind="plan_rejected",
            question=_ui_text(
                "Would you like to revise the rejected plan or describe a different deliverable?"
            ),
        )

    if (
        decision.capability_match_status == "unsupported"
        and decision.alternative_actions
        and request_mode != "guidance"
    ):
        action = decision.alternative_actions[0]
        capability = OUTPUT_CAPABILITIES[action]
        requested_granularity = (
            decision.requested_outcome.granularity
            if decision.requested_outcome
            else None
        )
        return NextTurnPrompt(
            kind="alternative_outcome",
            question=_ui_text(
                "State whether you want the supported alternative above, or describe "
                "another NetZoo goal."
            ),
            alternative_action=action,
            alternative_granularity=(
                requested_granularity
                if requested_granularity in capability.granularities
                else None
            ),
        )

    if decision.action == "no_tool" and request_mode == "guidance":
        return NextTurnPrompt(
            kind="completed",
            question=_ui_text(
                "Enter a follow-up question, provide inputs only if you want to "
                "execute the complete recommended pipeline, or describe another "
                "NetZoo goal."
            ),
        )

    if (
        decision.action == "no_tool"
        and semantic_relationship == "alternatives"
        and len(semantic_candidates) > 1
    ):
        return NextTurnPrompt(
            kind="recommended_workflow",
            question=_ui_text(
                "Enter the requested clarification or describe another NetZoo goal."
            ),
        )

    if (
        decision.capability_match_status == "ambiguous"
        and decision.clarification_question
    ):
        return NextTurnPrompt(
            kind="clarify_outcome",
            question=_ui_text(
                "Enter the requested clarification or describe another NetZoo goal."
            ),
        )

    if decision.action == "no_tool" and decision.recommended_actions:
        action = decision.recommended_actions[-1]
        required_inputs = [
            field_name
            for field_name in REQUIRED_INPUTS.get(action, ())
            if field_name not in OUTPUT_ROLE_FIELDS
        ]
        expected_field = required_inputs[0] if required_inputs else None
        workflow = _workflow_name(action)
        workflow_start = (
            f"provide the {INPUT_LABELS.get(expected_field, expected_field)} path "
            f"to start the recommended {workflow} workflow"
            if expected_field
            else f"ask to start the recommended {workflow} workflow"
        )
        return NextTurnPrompt(
            kind="recommended_workflow",
            question=_ui_text(
                f"Enter a follow-up question, {workflow_start}, or describe another "
                "NetZoo goal."
            ),
            continuation_action=action,
            expected_field=expected_field,
        )

    if terminal_failed(results, result_evaluation):
        validation_errors = [
            error
            for item in results
            if item.action.startswith("inspect_")
            for error in item.errors
        ]
        if validation_errors:
            detail = validation_errors[0]
            question = (
                f"Input validation did not pass: {detail} "
                "Are these local files intended for this workflow? "
                "If not, provide the correct role=path assignments."
            )
        else:
            question = (
                f"The {plan.workflow} workflow stopped. Would you like to correct "
                "its inputs or try a different workflow?"
            )
        return NextTurnPrompt(
            kind="failed",
            question=_ui_text(question),
        )

    if any(item.status == "dry_run" for item in results):
        return NextTurnPrompt(
            kind="dry_run",
            question=_ui_text(
                f"Your {plan.workflow} plan is ready. Enter /execute to execute and "
                "confirm this validated workflow.\n"
                "Or describe the input changes you want."
            ),
        )

    if decision.action in {"query_context7", "web_search"}:
        return NextTurnPrompt(
            kind="retrieval",
            question=_ui_text(
                "Would you like to ask about these sources or connect them to a "
                "NetZoo workflow?"
            ),
        )

    if results and result_evaluation.get("status") == "completed":
        return NextTurnPrompt(
            kind="completed",
            question=_ui_text(
                f"The {plan.workflow} workflow is complete. Would you like to inspect "
                "or refine the result, or start another workflow?"
            ),
        )

    if decision.action == "no_tool" and not decision.in_scope:
        return NextTurnPrompt(
            kind="unsupported",
            question=_ui_text(
                "Would you like to see the supported capabilities or describe a "
                "different NetZoo deliverable?"
            ),
        )

    return NextTurnPrompt(
        kind="completed",
        question=_ui_text(
            "Enter a follow-up question or describe another NetZoo goal."
        ),
    )


def build_follow_up_context(
    state: dict,
    prompt: NextTurnPrompt,
    prior_user_goal: str,
) -> FollowUpContext:
    """Build trusted conversational context without prior assistant prose."""
    plan = WorkflowPlan.model_validate(state["plan"])
    decision = TaskDecision.model_validate(plan.decision)
    candidates = list(
        dict.fromkeys(
            decision.recommended_actions
            or decision.matched_actions
            or decision.hypothesis_actions
        )
    )
    return FollowUpContext(
        prior_user_goal=prior_user_goal[-4000:],
        prompt_kind=prompt.kind,
        prompt_question=prompt.question,
        candidate_actions=candidates,
        candidate_workflows=[
            WorkflowConversationFact(
                action=action,
                workflow=ACTION_DEFINITIONS[action].workflow,
                required_inputs=list(ACTION_DEFINITIONS[action].required_inputs),
                granularities=sorted(
                    OUTPUT_CAPABILITIES[action].granularities
                    if action in OUTPUT_CAPABILITIES
                    else ()
                ),
            )
            for action in candidates
        ],
        continuation_action=prompt.continuation_action,
        expected_field=prompt.expected_field,
        alternative_action=prompt.alternative_action,
    )


def render_next_turn_prompt(prompt: NextTurnPrompt) -> str:
    """Render navigation help without repeating it inside every outcome template."""
    if prompt.kind == "initial":
        return prompt.question
    return "\n".join(
        [
            "----------------------------------------",
            _ui_text("Next step"),
            prompt.question,
            _ui_text("Enter/back: start a new task | exit: close"),
        ]
    )


def follow_up_returns_to_main(prompt: NextTurnPrompt, answer: str) -> bool:
    if prompt.kind == "initial":
        return False
    return answer.strip().casefold() in {
        "",
        "back",
        "menu",
        "new",
        "main",
        "返回",
        "主選單",
        "新任務",
    }


def resolve_next_turn_input(
    prompt: NextTurnPrompt,
    resolution: ContextualReplyResolution,
    original_reply: str,
) -> str | None:
    """Turn validated reply intent into a bounded scientific Router task."""
    if resolution.kind in {"follow_up", "new_goal"}:
        return resolution.resolved_task
    if resolution.kind != "accept_workflow":
        return None
    if prompt.kind == "clarify_outcome":
        if not resolution.selected_action:
            return resolution.resolved_task
        granularity = (
            f" CONFIRMED_GRANULARITY={resolution.selected_granularity}."
            if resolution.selected_granularity
            else ""
        )
        return (
            f"CONFIRMED_OUTCOME_ACTION={resolution.selected_action}.{granularity} "
            "Explain the confirmed supported outcome and recommend its workflow. "
            "Do not execute it yet."
        )
    if prompt.alternative_action:
        granularity = (
            f" CONFIRMED_GRANULARITY={prompt.alternative_granularity}."
            if prompt.alternative_granularity
            else ""
        )
        return (
            f"CONFIRMED_OUTCOME_ACTION={prompt.alternative_action}.{granularity} "
            "Explain the confirmed supported outcome and recommend its workflow. "
            "Do not execute it yet."
        )
    selected_action = resolution.selected_action or prompt.continuation_action
    if not selected_action:
        return None
    stripped = original_reply.strip()
    looks_like_path = bool(
        re.search(r"[/\\]|\.(?:tsv|tab|txt|csv|npy)$", stripped, flags=re.IGNORECASE)
    )
    continuation = (
        f"PREVIOUS_ACTION={selected_action}. Continue the recommended "
        f"{_workflow_name(selected_action)} workflow. The user accepted "
        "the previous capability recommendation."
    )
    if looks_like_path and prompt.expected_field:
        continuation += f" {prompt.expected_field} is {stripped}."
    return continuation
