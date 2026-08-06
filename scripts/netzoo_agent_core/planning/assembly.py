"""Final clarification or executable plan assembly."""

from __future__ import annotations

from workflow_registry import CODE_VALIDATION_STEPS

from .context import _PlanningContext
from ..contracts import InputEvidence, WorkflowPlan, WorkflowStep

__all__: list[str] = []


def _assemble_workflow_plan(
    context: _PlanningContext,
    evidence: list[InputEvidence],
) -> WorkflowPlan:
    decision = context.decision
    action = context.action
    workflow = context.workflow
    workflow_spec = context.workflow_spec
    memory_notes = context.memory_notes
    policy_hash = context.policy_hash
    policy_notes = context.policy_notes
    missing = [item.field for item in evidence if item.status == "missing"]
    decision.missing_inputs = missing
    decision.should_execute = not missing
    if missing:
        question = (
            "Please provide the next missing input. The CLI wizard will ask for "
            "each unresolved field one at a time; advanced users may still enter "
            "field=value pairs for all remaining inputs."
        )
        return WorkflowPlan(
            workflow=workflow,
            objective=decision.reason,
            decision=decision.model_dump(),
            evidence=evidence,
            missing_inputs=missing,
            status="needs_input",
            question=question,
            memory_notes=memory_notes,
            policy_hash=policy_hash,
            policy_notes=policy_notes,
        )

    steps = []
    validation_actions = (
        list(workflow_spec.validation_steps)
        if workflow_spec is not None
        else CODE_VALIDATION_STEPS.get(action, [])
    )
    for validation_action in validation_actions:
        steps.append(
            WorkflowStep(
                action=validation_action,
                purpose="Validate input formats and identifier compatibility before execution.",
            )
        )
    execution_action = (
        workflow_spec.execution_step if workflow_spec is not None else action
    )
    steps.append(
        WorkflowStep(
            action=execution_action,
            purpose="Execute the requested NetZoo workflow.",
        )
    )
    return WorkflowPlan(
        workflow=workflow,
        objective=decision.reason,
        decision=decision.model_dump(),
        evidence=evidence,
        steps=steps,
        status="ready",
        memory_notes=memory_notes,
        policy_hash=policy_hash,
        policy_notes=policy_notes,
    )
