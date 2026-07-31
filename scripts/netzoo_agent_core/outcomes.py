"""Terminal-outcome selection across execution and recovery attempts."""

from __future__ import annotations

from .contracts import EvaluationResult, ToolExecutionResult

__all__ = [
    "effective_results",
    "supersede_triggering_failure",
    "terminal_failed",
]


def effective_results(
    results: list[ToolExecutionResult | dict],
) -> list[ToolExecutionResult]:
    """Return results that still contribute to the workflow's terminal outcome."""
    models = [ToolExecutionResult.model_validate(item) for item in results]
    return [item for item in models if not item.superseded]


def terminal_failed(
    results: list[ToolExecutionResult | dict],
    evaluation: EvaluationResult | dict | None,
) -> bool:
    """Resolve terminal failure from the evaluator before inspecting attempts."""
    if evaluation is not None:
        status = (
            evaluation.status
            if isinstance(evaluation, EvaluationResult)
            else evaluation.get("status")
        )
        if status == "completed":
            return False
        if status == "failed":
            return True
    return any(item.status == "failed" for item in effective_results(results))


def supersede_triggering_failure(
    results: list[ToolExecutionResult | dict],
    next_attempt: int,
) -> list[ToolExecutionResult]:
    """Mark the latest effective failure as historical recovery evidence."""
    models = [ToolExecutionResult.model_validate(item) for item in results]
    for item in reversed(models):
        if item.status == "failed" and not item.superseded:
            item.superseded = True
            item.superseded_reason = (
                f"superseded by recovery attempt {next_attempt}"
            )
            break
    return models
