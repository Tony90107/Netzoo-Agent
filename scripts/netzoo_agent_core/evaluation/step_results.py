"""State transitions derived from structured workflow step results."""

from __future__ import annotations

from ..contracts import (
    EXECUTE_TOOLS,
    EvaluationResult,
    MAX_RECOVERY_ATTEMPTS,
    TaskDecision,
    ToolExecutionResult,
    WorkflowPlan,
)
from ..routing import structure_tool_result

def evaluate_step_result(
    plan: WorkflowPlan,
    step_index: int,
    result: ToolExecutionResult | dict | str,
    replan_count: int = 0,
) -> EvaluationResult:
    if isinstance(result, str):
        action = plan.steps[step_index].action
        try:
            decision = TaskDecision.model_validate(plan.decision)
        except Exception:
            decision = TaskDecision(
                action=action,
                in_scope=True,
                should_execute=True,
                confidence=1.0,
                reason="legacy evaluator input",
            )
        structured = structure_tool_result(action, decision, result)
    else:
        structured = ToolExecutionResult.model_validate(result)
    if structured.status == "failed":
        if (
            structured.retryable
            and structured.recovery_hint
            and replan_count < MAX_RECOVERY_ATTEMPTS
            and EXECUTE_TOOLS
        ):
            return EvaluationResult(
                status="replan",
                reason="The failure is recoverable; return to the Planner to insert an approved repair step.",
                recovery_action=structured.recovery_hint,
                recovery_error_code=structured.error_code,
            )
        return EvaluationResult(
            status="failed",
            reason="The structured tool result reports a validation or execution failure.",
        )
    if step_index + 1 < len(plan.steps):
        return EvaluationResult(
            status="continue",
            reason="This step passed; continue to the next planned step.",
        )
    return EvaluationResult(
        status="completed", reason="All planned steps completed successfully."
    )
