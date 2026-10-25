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
from ..interpretation.core_decision import decide_core, with_core
from ..interpretation.request_requirements import read_request_requirements, with_routing
from ..interpretation.semantic_goal import publish_routing_progress
from ..llm import latest_user_message, latest_user_task
from ..planning import build_workflow_plan, render_plan
from .context import _GraphContext, record_event
from .contract_veto_call import apply_contract_veto
from .data_items_call import apply_data_items
from .hybrid_gate_call import apply_hybrid_gates
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
    if decision.run_verdict is not None:
        # Items 1-2: the verdict holds for this request only; a plan evaluated against another one fails.
        decision = decision.model_copy(update={"run_verdict": decision.run_verdict.model_copy(
            update={"request_sha256": requirements.source_sha256})})
    # Core decision spec: the turn's four-way call; phase 1 acts on CLARIFY (nothing selected or run), the rest shadow.
    core = decide_core(decision, user_task, reason_code=invocation.reason_code)
    # Options-first decision step 7 (2026-10-18): the hard gates judge a DO's workflows before any is runnable.
    core, usage, budget_warnings = apply_hybrid_gates(
        context, state, decision, core, user_task, invocation.usage, invocation.budget_warnings)
    # Hybrid spec 2026-10-19: the contract veto replaces the hard gates at the same hook (both off by default).
    core, usage, budget_warnings = apply_contract_veto(context, state, decision, core, user_task, usage,
                                                       budget_warnings)
    # ROUND-27 C1 (NETZOO_DATA_ITEMS): a DO whose workflows the user's stated data cannot feed asks to confirm.
    core, usage, budget_warnings = apply_data_items(context, state, core, user_task, usage, budget_warnings)
    # Harness repair P3: a third round of clarification is not asked (spec 7.2).
    from ..interpretation.task_answers import clarification_rounds

    core = clarification_rounds(core, state.get("task_state"))
    decision = with_core(decision, core)
    record_event(context, state, "core.decision", "classify", core.model_dump(mode="json"))
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
        "budget_warnings": budget_warnings,
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
