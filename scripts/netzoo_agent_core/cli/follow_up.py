"""Outcome-aware next-turn interaction."""

from __future__ import annotations

import re

from workflow_registry import (
    OUTPUT_CAPABILITIES,
    REQUIRED_INPUTS,
    workflow_name as _workflow_name,
)

from ..contracts import (
    NextTurnPrompt,
    OUTPUT_ROLE_FIELDS,
    PlanEvaluationResult,
    TaskDecision,
    ToolExecutionResult,
    WorkflowPlan,
    _ui_text,
)
from ..interpretation import INPUT_LABELS
from ..outcomes import effective_results, terminal_failed

__all__ = [
    "initial_next_turn_prompt",
    "build_next_turn_prompt",
    "follow_up_declined",
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

    if plan_evaluation and plan_evaluation.status == "rejected":
        return NextTurnPrompt(
            kind="plan_rejected",
            question=_ui_text(
                "Would you like to revise the rejected plan or describe a different deliverable?"
            ),
        )

    if decision.capability_match_status == "ambiguous":
        return NextTurnPrompt(
            kind="clarify_outcome",
            question=_ui_text(
                "Reply with the clarification above, or describe another NetZoo goal."
            ),
        )

    if (
        decision.capability_match_status == "unsupported"
        and decision.alternative_actions
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
                "Reply yes if you want the supported alternative above, or describe "
                "another goal."
            ),
            alternative_action=action,
            alternative_granularity=(
                requested_granularity
                if requested_granularity in capability.granularities
                else None
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
                "Reply with the clarification above, or describe another NetZoo goal."
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
        field_hint = (
            f" or provide the {INPUT_LABELS.get(expected_field, expected_field)} path"
            if expected_field
            else ""
        )
        return NextTurnPrompt(
            kind="recommended_workflow",
            question=_ui_text(
                f"Would you like to continue with the recommended {workflow} workflow? "
                f"Reply yes to start{field_hint}, or type a new request."
            ),
            continuation_action=action,
            expected_field=expected_field,
        )

    if (
        terminal_failed(results, result_evaluation)
    ):
        return NextTurnPrompt(
            kind="failed",
            question=_ui_text(
                f"The {plan.workflow} workflow stopped. Would you like to correct "
                "its inputs or try a different workflow?"
            ),
        )

    if any(item.status == "dry_run" for item in results):
        return NextTurnPrompt(
            kind="dry_run",
            question=_ui_text(
                f"The {plan.workflow} command preview is ready. Would you like to "
                "adjust its inputs or explore another workflow? Enter /execute to "
                "enable execution in this session."
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
            "Would you like to ask a follow-up about this answer or describe another "
            "NetZoo goal?"
        ),
    )

def follow_up_declined(answer: str) -> bool:
    return answer.strip().casefold() in {
        "n",
        "no",
        "nope",
        "不用",
        "不要",
        "否",
        "先不要",
    }

def render_next_turn_prompt(prompt: NextTurnPrompt) -> str:
    """Render navigation help without repeating it inside every outcome template."""
    if prompt.kind == "initial":
        return prompt.question
    return "\n".join(
        [
            prompt.question,
            _ui_text("Controls: Enter/back = main prompt | exit = close"),
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

def resolve_next_turn_input(prompt: NextTurnPrompt, answer: str) -> str:
    """Turn a short acceptance or direct path into a resumable workflow request."""
    stripped = answer.strip()
    normalized = stripped.casefold()
    affirmative = normalized in {
        "y",
        "yes",
        "ok",
        "okay",
        "start",
        "continue",
        "好",
        "好的",
        "可以",
        "繼續",
        "開始",
        "要",
    }
    if prompt.alternative_action and affirmative:
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
    if not prompt.continuation_action:
        return stripped
    looks_like_path = bool(
        re.search(r"[/\\]|\.(?:tsv|tab|txt|csv|npy)$", stripped, flags=re.IGNORECASE)
    )
    if not affirmative and not looks_like_path:
        return stripped

    continuation = (
        f"PREVIOUS_ACTION={prompt.continuation_action}. Continue the recommended "
        f"{_workflow_name(prompt.continuation_action)} workflow. The user accepted "
        "the previous capability recommendation."
    )
    if looks_like_path and prompt.expected_field:
        continuation += f" {prompt.expected_field} is {stripped}."
    return continuation
