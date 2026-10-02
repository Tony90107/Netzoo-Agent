"""One typed interpretation of step arguments for review and execution."""

from __future__ import annotations

from ..contracts import TaskDecision, WorkflowPlan


_RECOVERY_FORMAT_FIELDS = frozenset({
    "expression_file", "output_file", "genes_axis", "with_header",
})
_PROTECTED_FIELDS = frozenset({"action", "should_execute", "missing_inputs"})


def effective_step_decision(plan: WorkflowPlan, step_index: int) -> TaskDecision:
    """Reject an unreviewed override and return the executor's typed arguments."""
    step = plan.steps[step_index]
    decision = TaskDecision.model_validate(plan.decision)
    authorized_recovery = (
        plan.recovery_action == "format_expression_headerless"
        and step_index == plan.recovery_step_index
        and step.action == "format_expression"
    )
    updates = {}
    for field_name, value in step.arguments.items():
        if field_name not in TaskDecision.model_fields or field_name in _PROTECTED_FIELDS:
            raise ValueError(f"Step {step_index} has an unsupported argument: {field_name}.")
        if authorized_recovery:
            if field_name not in _RECOVERY_FORMAT_FIELDS:
                raise ValueError(f"Recovery step has an unsupported argument: {field_name}.")
        elif getattr(decision, field_name) != value:
            raise ValueError(f"Step {step_index} overrides reviewed {field_name}.")
        updates[field_name] = value
    return TaskDecision.model_validate({
        **decision.model_dump(), **updates,
        "action": step.action, "should_execute": True, "missing_inputs": [],
    })
