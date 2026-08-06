"""Task-classification and workflow-planning graph nodes."""

from __future__ import annotations

import json
import time

from ..contracts import (
    AgentState,
    LLMUsage,
    RouterDecision,
    TaskDecision,
    UserProfile,
    _trace,
    _ui_text,
)
from ..interpretation import (
    _is_fatal_exception,
    deterministic_router_fallback,
    hydrate_router_decision,
    repair_router_decision,
)
from ..llm import (
    append_llm_usage,
    build_router_messages,
    latest_user_task,
    structured_result_payload,
)
from ..planning import build_workflow_plan, render_plan
from .context import _GraphContext, preflight_budget, record_event

__all__: list[str] = []


def classify_task(context: _GraphContext, state: AgentState) -> dict:
    _trace("intent", "Interpreting the request and capability boundaries")
    messages = build_router_messages(context.routing_prompt, state["messages"])
    user_task = latest_user_task(state["messages"])
    router_input_text = "\n".join(str(message.content) for message in messages)
    router_input_text += json.dumps(
        RouterDecision.model_json_schema(),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    current_usage = state.get("token_usage")
    budget_decision, budget_warnings = preflight_budget(
        context,
        state,
        role="router",
        model=context.router_model_name,
        input_text=router_input_text,
        reserved_output_tokens=context.router_max_tokens,
        allow_reserve=False,
    )
    if budget_decision.status == "blocked":
        usage = (
            LLMUsage.model_validate(current_usage)
            if current_usage
            else LLMUsage(budget_tokens=context.task_token_budget)
        )
        usage.budget_exhausted = True
        decision = deterministic_router_fallback(user_task)
        _trace(
            "intent",
            "Router call skipped because the task token budget would be exceeded",
        )
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
                "reason_code": "budget_fallback",
                "recommended_actions": decision.recommended_actions,
            },
        )
        return {
            "decision": decision.model_dump(),
            "token_usage": usage.model_dump(),
            "budget_warnings": budget_warnings,
        }
    call_started_ns = time.monotonic_ns()
    call_status = "success"
    reason_code = "provider"
    try:
        structured = context.router.invoke(messages)
        parsed_decision, raw_message = structured_result_payload(structured)
        hydrated = hydrate_router_decision(parsed_decision, user_task)
        decision = repair_router_decision(hydrated, user_task)
        usage = append_llm_usage(
            current_usage,
            role="router",
            model=context.router_model_name,
            response=raw_message,
            input_text=router_input_text,
            output_text=decision.model_dump_json(),
            budget_tokens=context.task_token_budget,
            duration_ms=max(0, (time.monotonic_ns() - call_started_ns) // 1_000_000),
            price_catalog=context.price_catalog,
        )
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        decision = deterministic_router_fallback(user_task, error)
        call_status = "failed"
        reason_code = "deterministic_fallback"
        usage = append_llm_usage(
            current_usage,
            role="router",
            model=context.router_model_name,
            input_text=router_input_text,
            output_text="",
            budget_tokens=context.task_token_budget,
            duration_ms=max(0, (time.monotonic_ns() - call_started_ns) // 1_000_000),
            status=call_status,
            price_catalog=context.price_catalog,
        )
        _trace(
            "intent",
            "Router provider failed; deterministic fallback selected",
            type(error).__name__,
        )
    record_event(
        context,
        state,
        "llm.completed",
        "classify",
        usage.calls[-1].model_dump(mode="json"),
    )
    _trace(
        "intent",
        f"Classified as {decision.action}",
        f"Confidence {decision.confidence:.2f} | {decision.reason}",
    )
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
            "reason_code": reason_code,
            "recommended_actions": decision.recommended_actions,
        },
    )
    return {
        "decision": decision.model_dump(),
        "token_usage": usage.model_dump(),
        "budget_warnings": budget_warnings,
    }


def plan_task(context: _GraphContext, state: AgentState) -> dict:
    user_task = str(state["messages"][-1].content)
    decision = TaskDecision.model_validate(state["decision"])
    plan = build_workflow_plan(
        decision,
        user_task,
        profile=state.get("profile"),
        retrieved_episodes=state.get("retrieved_episodes", []),
        project_policy=state.get("project_policy"),
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
        "current_step": 0,
        "tool_results": [],
        "replan_count": 0,
    }
