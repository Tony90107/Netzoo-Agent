"""Allow-listed and bounded workflow-plan recovery orchestration."""

from __future__ import annotations

from ..contracts import (
    EvaluationResult,
    MAX_RECOVERY_ATTEMPTS,
    TaskDecision,
    WorkflowPlan,
)
from .recovery_registry import get_recovery_strategy


def recover_workflow_plan(
    plan: WorkflowPlan,
    step_index: int,
    evaluation: EvaluationResult,
) -> tuple[WorkflowPlan, int]:
    """Delegate a typed replan request to one code-registered strategy."""
    if evaluation.status != "replan" or plan.recovery_attempt >= MAX_RECOVERY_ATTEMPTS:
        return plan, step_index
    strategy = get_recovery_strategy(evaluation.recovery_action)
    if strategy is None:
        return plan, step_index
    try:
        decision = TaskDecision.model_validate(plan.decision)
    except Exception:
        return plan, step_index
    if not strategy.accepts(
        action=decision.action,
        error_code=evaluation.recovery_error_code,
    ):
        return plan, step_index
    return strategy.apply(plan, step_index, evaluation)
