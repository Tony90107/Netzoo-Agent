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


def _handoff_output_failures(
    plan: WorkflowPlan,
    result: ToolExecutionResult,
) -> list[str]:
    """Check that a successful producer result still matches its typed handoff."""
    handoff = plan.workflow_handoff
    if (
        handoff is None
        or handoff.status != "validated"
        or result.action != handoff.producer_action
        or result.status != "success"
    ):
        return []

    failures: list[str] = []
    expected_artifacts = {
        path
        for paths in handoff.artifact_paths.values()
        for path in paths
    }
    expected_artifacts.update(handoff.source_artifact_paths)
    reported_artifacts = set(result.artifacts)
    if not expected_artifacts:
        failures.append("validated handoff has no planned producer artifact paths")
    else:
        missing_artifacts = sorted(expected_artifacts - reported_artifacts)
        if missing_artifacts:
            failures.append(
                "producer result did not verify planned handoff artifacts: "
                + ", ".join(missing_artifacts)
            )

    sample_count = result.metrics.get("bonobo_samples")
    if sample_count is not None and sample_count != len(handoff.sample_ids):
        failures.append(
            "producer result sample count does not match the handoff sample identity"
        )
    gene_count = result.metrics.get("bonobo_genes")
    if gene_count is not None and gene_count != len(handoff.gene_ids):
        failures.append(
            "producer result gene count does not match the handoff gene order"
        )
    if sample_count is None or gene_count is None:
        failures.append(
            "producer result did not expose BONOBO sample/gene identity metrics"
        )
    return failures


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
    handoff_failures = _handoff_output_failures(plan, structured)
    if handoff_failures:
        return EvaluationResult(
            status="failed",
            reason="The verified producer output violated the workflow handoff contract: "
            + "; ".join(handoff_failures),
        )
    if step_index + 1 < len(plan.steps):
        return EvaluationResult(
            status="continue",
            reason="This step passed; continue to the next planned step.",
        )
    return EvaluationResult(
        status="completed", reason="All planned steps completed successfully."
    )
