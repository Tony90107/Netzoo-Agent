"""State-only conditional transitions for the graph topology."""

from __future__ import annotations

from ..contracts import AgentState, PlanEvaluationResult, WorkflowPlan

__all__: list[str] = []


def route_plan_evaluation(state: AgentState) -> str:
    plan = WorkflowPlan.model_validate(state["plan"])
    evaluation = PlanEvaluationResult.model_validate(state["plan_evaluation"])
    return (
        "execute_tool"
        if evaluation.status == "approved" and plan.status == "ready" and plan.steps
        else "consolidate_memory"
    )


def route_evaluation(state: AgentState) -> str:
    status = state["evaluation"]["status"]
    if status == "continue":
        return "execute_tool"
    if status == "replan":
        return "recover"
    return "consolidate_memory"
