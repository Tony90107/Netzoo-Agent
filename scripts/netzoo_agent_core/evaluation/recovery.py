"""Allow-listed and bounded workflow-plan recovery."""

from __future__ import annotations

from pathlib import Path

from ..contracts import (
    EvaluationResult,
    InputEvidence,
    MAX_RECOVERY_ATTEMPTS,
    TaskDecision,
    WorkflowPlan,
    WorkflowStep,
)

def recover_workflow_plan(
    plan: WorkflowPlan,
    step_index: int,
    evaluation: EvaluationResult,
) -> tuple[WorkflowPlan, int]:
    """Apply allow-listed, bounded repairs; never let the LLM invent shell actions."""
    if evaluation.recovery_action != "format_expression_headerless":
        return plan, step_index

    decision = TaskDecision.model_validate(plan.decision)
    if not decision.expression_file or not decision.output_file:
        return plan, step_index
    source = Path(decision.expression_file)
    output_parent = Path(decision.output_file).parent
    derived = str(output_parent / f"{source.stem}.puma-expression.tsv")
    original_run_action = plan.steps[step_index].action
    decision.expression_file = derived
    plan.decision = decision.model_dump()
    expression_evidence = next(
        (item for item in plan.evidence if item.field == "expression_file"),
        None,
    )
    recovery_reason = (
        "The prior PUMA attempt rejected the expression header, so the bounded "
        "recovery derived a headerless expression file."
    )
    if expression_evidence is None:
        plan.evidence.append(
            InputEvidence(
                field="expression_file",
                status="discovered",
                value=derived,
                reason=recovery_reason,
            )
        )
    else:
        expression_evidence.status = "discovered"
        expression_evidence.value = derived
        expression_evidence.reason = recovery_reason
        expression_evidence.candidates = []
    recovery_steps = [
        WorkflowStep(
            action="format_expression",
            purpose="Remove the expression header rejected by PUMA and create a derived input file.",
            arguments={
                "expression_file": str(source),
                "output_file": derived,
                "genes_axis": "auto",
                "with_header": False,
            },
        ),
        WorkflowStep(
            action="inspect_inputs",
            purpose="Revalidate the repaired expression file against the prior and PPI inputs.",
        ),
        WorkflowStep(
            action=original_run_action,
            purpose="Retry the PUMA workflow with the repaired input.",
        ),
    ]
    plan.steps = [*plan.steps[:step_index], *recovery_steps]
    plan.recovery_action = "format_expression_headerless"
    plan.recovery_step_index = step_index
    plan.recovery_attempt = min(
        plan.recovery_attempt + 1,
        MAX_RECOVERY_ATTEMPTS,
    )
    return plan, step_index
