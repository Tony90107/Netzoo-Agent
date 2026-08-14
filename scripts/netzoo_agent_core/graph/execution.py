"""Plan evaluation, tool execution, result evaluation, and recovery nodes."""

from __future__ import annotations

from datetime import datetime

from ..contracts import (
    AgentState,
    EXECUTE_TOOLS,
    EvaluationResult,
    MAX_RECOVERY_ATTEMPTS,
    TaskDecision,
    WorkflowPlan,
    _trace,
)
from ..evaluation import (
    evaluate_step_result,
    evaluate_workflow_plan,
    recover_workflow_plan,
    render_plan_evaluation,
)
from ..outcomes import supersede_triggering_failure
from ..planning import render_plan
from ..routing import execute_selected_tool, structure_tool_result
from .context import _GraphContext, record_event

__all__: list[str] = []


def evaluate_plan(context: _GraphContext, state: AgentState) -> dict:
    plan = WorkflowPlan.model_validate(state["plan"])
    evaluation = evaluate_workflow_plan(
        plan,
        str(state["messages"][-1].content),
        state.get("project_policy"),
    )
    _trace(
        "review",
        f"Plan evaluation {evaluation.status} ({evaluation.score}/100)",
        render_plan_evaluation(evaluation),
    )
    plan_event_type = {
        "approved": "plan.approved",
        "rejected": "plan.rejected",
        "deferred": "plan.deferred",
    }[evaluation.status]
    record_event(
        context,
        state,
        plan_event_type,
        "evaluate_plan",
        evaluation.model_dump(),
    )
    return {"plan_evaluation": evaluation.model_dump()}


def execute_tool(context: _GraphContext, state: AgentState) -> dict:
    plan = WorkflowPlan.model_validate(state["plan"])
    step_index = state.get("current_step", 0)
    step = plan.steps[step_index]
    decision = TaskDecision.model_validate(plan.decision)
    decision.action = step.action
    decision.should_execute = True
    decision.missing_inputs = []
    for field_name, value in step.arguments.items():
        if hasattr(decision, field_name):
            setattr(decision, field_name, value)
    _trace(
        "tool",
        f"Executor [{step_index + 1}/{len(plan.steps)}]: {step.action}",
        step.purpose,
    )
    record_event(
        context,
        state,
        "tool.started",
        "execute_tool",
        {
            "step_index": step_index,
            "action": step.action,
            "purpose": step.purpose,
            "arguments": step.arguments,
            "execution_mode": "execute" if EXECUTE_TOOLS else "dry_run",
            "attempt_id": state.get("replan_count", 0),
        },
    )
    execution_started_at = datetime.now().astimezone()
    raw_result = execute_selected_tool(decision)
    result = structure_tool_result(
        step.action,
        decision,
        raw_result,
        persist_log=True,
        attempt_id=state.get("replan_count", 0),
        execution_started_at=execution_started_at,
    )
    _trace(
        "tool",
        f"{step.action} → {result.status}",
        result.summary,
    )
    record_event(
        context,
        state,
        "tool.completed",
        "execute_tool",
        result.model_dump(exclude={"raw_output"}),
    )
    return {
        "tool_result": result.model_dump(),
        "tool_results": [*state.get("tool_results", []), result.model_dump()],
    }


def evaluate_result(context: _GraphContext, state: AgentState) -> dict:
    plan = WorkflowPlan.model_validate(state["plan"])
    step_index = state.get("current_step", 0)
    evaluation = evaluate_step_result(
        plan,
        step_index,
        state.get("tool_result", {}),
        state.get("replan_count", 0),
    )
    _trace("evaluate", f"Evaluator: {evaluation.status}", evaluation.reason)
    record_event(
        context,
        state,
        "evaluation.recorded",
        "evaluate",
        {
            "step_index": step_index,
            **evaluation.model_dump(),
        },
    )
    update = {"evaluation": evaluation.model_dump()}
    if evaluation.status == "continue":
        update["current_step"] = step_index + 1
    return update


def recover(context: _GraphContext, state: AgentState) -> dict:
    plan = WorkflowPlan.model_validate(state["plan"])
    evaluation = EvaluationResult.model_validate(state["evaluation"])
    recovered, next_step = recover_workflow_plan(
        plan,
        state.get("current_step", 0),
        evaluation,
    )
    replan_count = state.get("replan_count", 0) + 1
    tool_results = supersede_triggering_failure(
        state.get("tool_results", []),
        next_attempt=replan_count,
    )
    _trace(
        "recover",
        (f"Planner recovery plan (attempt {replan_count}/{MAX_RECOVERY_ATTEMPTS})"),
        render_plan(recovered),
    )
    record_event(
        context,
        state,
        "recovery.selected",
        "recover",
        {
            "attempt_id": replan_count,
            "next_step": next_step,
            "plan": recovered.model_dump(),
        },
    )
    return {
        "plan": recovered.model_dump(),
        "decision": recovered.decision,
        "current_step": next_step,
        "replan_count": replan_count,
        "tool_results": [item.model_dump() for item in tool_results],
    }
