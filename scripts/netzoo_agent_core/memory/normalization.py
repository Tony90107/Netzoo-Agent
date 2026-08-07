"""Pure episode metadata normalization and compact rendering."""

from __future__ import annotations

from workflow_registry import REQUIRED_INPUTS, WORKFLOW_MEMORY_METADATA

from ..contracts.decisions import TaskDecision
from ..contracts.memory import Episode
from ..contracts.planning import WorkflowPlan
from ..contracts.results import EvaluationResult, ToolExecutionResult
from ..outcomes import effective_results
from ..presentation import _is_demo_request
from ..settings import INPUT_ROLE_FIELDS, OUTPUT_ROLE_FIELDS, PARAMETER_FIELDS

__all__: list[str] = []


def _episode_intent_type(decision: TaskDecision, task: str) -> str:
    """Prefer router intent, with deterministic fallback for older/router-less tests."""
    if decision.intent_type != "unknown":
        return decision.intent_type
    if _is_demo_request(task):
        return "demo_run"
    if decision.action.startswith("run_"):
        return "run_analysis"
    if decision.action.startswith("inspect_"):
        return "inspect_input"
    if decision.action in {"format_expression", "convert_expression"}:
        return "prepare_input"
    return "unknown"


def _meaningful_parameter_value(value) -> bool:
    return value not in (None, False, "auto", "", [])


def normalize_episode_memory(
    task: str,
    plan: WorkflowPlan,
    results: list[ToolExecutionResult],
    evaluation: EvaluationResult,
) -> dict:
    """Build workflow-agnostic memory metadata from typed harness contracts."""
    results = effective_results(results)
    decision = TaskDecision.model_validate(plan.decision)
    required = REQUIRED_INPUTS.get(decision.action, ())
    intent_type = _episode_intent_type(decision, task)
    input_roles = [
        field_name
        for field_name in required
        if field_name in INPUT_ROLE_FIELDS and getattr(decision, field_name, None)
    ]
    output_roles = [
        field_name
        for field_name in required
        if field_name in OUTPUT_ROLE_FIELDS and getattr(decision, field_name, None)
    ]
    parameters = [
        field_name
        for field_name in sorted(PARAMETER_FIELDS)
        if _meaningful_parameter_value(getattr(decision, field_name, None))
    ]
    validation_steps = [
        step.action for step in plan.steps if step.action.startswith("inspect_")
    ]
    execution_steps = [
        step.action for step in plan.steps if step.action.startswith("run_")
    ]
    validation_results = [
        result for result in results if result.action.startswith("inspect_")
    ]
    if any(result.status == "failed" for result in validation_results):
        validation_status = "failed"
    elif validation_results:
        validation_status = "passed"
    else:
        validation_status = "not_applicable"
    execution_mode = (
        "dry_run"
        if any(result.status == "dry_run" for result in results)
        else "executed"
    )
    domain_metadata = WORKFLOW_MEMORY_METADATA.get(decision.action, {})
    tags = [
        f"workflow:{plan.workflow.casefold()}",
        f"action:{decision.action}",
        f"intent:{intent_type}",
        f"evaluation:{evaluation.status}",
        f"mode:{execution_mode}",
        f"validation:{validation_status}",
        *[f"input:{field_name}" for field_name in input_roles],
        *[f"output:{field_name}" for field_name in output_roles],
        *[f"param:{field_name}" for field_name in parameters],
        *[
            f"{key}:{value}"
            for key, value in sorted(domain_metadata.items())
            if value
        ],
    ]
    readable_workflow = plan.workflow.replace("-", " ")
    task_summary = (
        f"{readable_workflow} {intent_type.replace('_', ' ')}; "
        f"mode={execution_mode}; validation={validation_status}; "
        f"inputs={','.join(input_roles) or 'none'}."
    )
    return {
        "task_summary": task_summary[:500],
        "raw_task_excerpt": task[:500],
        "action": decision.action,
        "intent_type": intent_type,
        "input_roles": input_roles,
        "output_roles": output_roles,
        "parameters": parameters,
        "validation_steps": validation_steps,
        "execution_steps": execution_steps,
        "validation_status": validation_status,
        "execution_mode": execution_mode,
        "memory_tags": tags,
        "domain_metadata": domain_metadata,
    }


def compact_episode_payload(episode: Episode) -> dict:
    """Human-friendly memory-status view; verbose mode can still dump the full model."""
    inferred_action = episode.action
    if not inferred_action:
        inferred_action = "run_" + episode.workflow.casefold().replace("-", "_")
    execution_mode = (
        "dry_run" if episode.status == "dry_run" else episode.execution_mode
    )
    input_roles = episode.input_roles or [
        field_name for field_name in episode.inputs if field_name in INPUT_ROLE_FIELDS
    ]
    memory_tags = episode.memory_tags or [
        f"workflow:{episode.workflow.casefold()}",
        f"action:{inferred_action}",
        f"status:{episode.status}",
        f"mode:{execution_mode}",
        *[f"input:{field_name}" for field_name in input_roles],
    ]
    return {
        "episode_id": episode.episode_id,
        "created_at": episode.created_at,
        "workflow": episode.workflow,
        "action": inferred_action,
        "intent_type": episode.intent_type,
        "status": episode.status,
        "execution_mode": execution_mode,
        "validation_status": episode.validation_status,
        "input_roles": input_roles,
        "output_roles": episode.output_roles,
        "parameters": episode.parameters,
        "inputs": episode.inputs,
        "artifacts": episode.artifacts,
        "memory_tags": memory_tags,
        "policy_hash": episode.policy_hash,
    }
