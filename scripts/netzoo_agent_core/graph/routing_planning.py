"""Task-classification and workflow-planning graph nodes."""

from __future__ import annotations

from ..contracts import (
    AgentState,
    LLMUsage,
    TaskDecision,
    UserProfile,
    _trace,
    _ui_text,
)
from ..interpretation.request_requirements import read_request_requirements, with_routing
from ..interpretation.semantic_goal import publish_routing_progress
from ..llm import latest_user_message, latest_user_task
from ..planning import build_workflow_plan, render_plan
from .context import _GraphContext, record_event
from .operation_authority import with_operation_authority
from .router_invocation import invoke_router
from .planning_mapper import PlanningMapper

__all__: list[str] = []


def classify_task(context: _GraphContext, state: AgentState) -> dict:
    _trace("intent", "Interpreting the request and capability boundaries")
    user_task = latest_user_task(state["messages"])
    current_usage = state.get("token_usage")
    # Plan item 2: the request's requirements are read once, from the full
    # message; the router and model calls read the bounded window.
    requirements = read_request_requirements(latest_user_message(state["messages"]))
    invocation = with_operation_authority(
        context, state, requirements, invoke_router(context, state, user_task),
    )
    if invocation.reason_code == "workflow_continuation":
        # Values the user stated in the request this turn continues, carried as
        # validated typed state, are the user's words too.
        requirements = read_request_requirements(
            latest_user_message(state["messages"]),
            carried=(state.get("workflow_continuation") or {}).get("parameters"),
        )
    decision = invocation.decision
    usage = invocation.usage
    routing_state = invocation.routing_state
    previous_call_count = (
        len(LLMUsage.model_validate(current_usage).calls) if current_usage else 0
    )
    for call in usage.calls[previous_call_count:]:
        record_event(
            context,
            state,
            "llm.completed",
            "classify",
            call.model_dump(mode="json"),
        )
    publish_routing_progress(decision, routing_state["semantic_goal"], context.project_policy, user_task)
    record_event(
        context,
        state,
        "decision.recorded",
        "classify",
        {
            "action": decision.action,
            "confidence": decision.confidence,
            "in_scope": decision.in_scope,
            "reason": decision.reason,
            "reason_code": invocation.reason_code,
            "recommended_actions": decision.recommended_actions,
        },
    )
    requirements = with_routing(requirements, decision, routing_state)
    return {
        "decision": decision.model_dump(),
        "request_requirements": requirements.model_dump(mode="json"),
        "workflow_continuation": None,
        "method_comparison": None,
        "token_usage": usage.model_dump(),
        "budget_warnings": invocation.budget_warnings,
        **routing_state,
    }


def plan_task(context: _GraphContext, state: AgentState) -> dict:
    user_task = latest_user_message(state["messages"])
    decision = TaskDecision.model_validate(state["decision"])
    mapper = (
        PlanningMapper(context.input_content_mapper, context, state)
        if context.input_content_mapper is not None else None
    )
    plan = build_workflow_plan(
        decision,
        user_task,
        profile=state.get("profile"),
        retrieved_episodes=state.get("retrieved_episodes", []),
        project_policy=state.get("project_policy"),
        requirements=state.get("request_requirements"),
        content_mapper=mapper,
    )
    profile = UserProfile.model_validate(state.get("profile"))
    pending_preferences = context.profile_store.pending(
        profile, decision.preference_updates
    )
    if "PREFERENCE_CONFIRMATION_REJECTED" in user_task:
        pending_preferences = []
    if pending_preferences:
        plan.status = "needs_confirmation"
        plan.preference_proposals = pending_preferences
        plan.question = _ui_text("Confirm whether these preferences should be saved.")
        plan.steps = []
    _trace("plan", f"Planner: {plan.workflow} / {plan.status}", render_plan(plan))
    if plan.status == "needs_input":
        _trace("input", "The Planner requires additional input", plan.question)
    elif plan.status == "needs_confirmation":
        _trace("input", "The Planner requires confirmation", plan.question)
    record_event(
        context,
        state,
        "plan.created",
        "plan",
        {
            "workflow": plan.workflow,
            "objective": plan.objective,
            "status": plan.status,
            "steps": [step.model_dump() for step in plan.steps],
            "missing_inputs": plan.missing_inputs,
            "evidence": [item.model_dump() for item in plan.evidence],
            "policy_hash": plan.policy_hash,
        },
    )
    return {
        "plan": plan.model_dump(),
        "decision": plan.decision,
        "token_usage": mapper.usage.model_dump() if mapper is not None else state.get("token_usage", {}),
        "budget_warnings": mapper.budget_warnings if mapper is not None else state.get("budget_warnings", []),
        "current_step": 0,
        "tool_results": [],
        "replan_count": 0,
    }
