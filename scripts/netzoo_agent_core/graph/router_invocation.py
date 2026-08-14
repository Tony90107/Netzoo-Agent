"""Bounded Router invocation, under-classification repair, and budget handling."""

from __future__ import annotations

from dataclasses import dataclass
import json
import time

from ..contracts import AgentState, LLMUsage, RouterDecision, TaskDecision, _trace
from ..interpretation.hydration import hydrate_router_decision
from ..interpretation.outcome_consistency import needs_outcome_repair
from ..interpretation.provider_fallback import (
    _is_fatal_exception,
    deterministic_router_fallback,
)
from ..interpretation.repair import repair_router_decision
from ..interpretation.semantic_goal import outcome_routing_state
from ..llm import (
    append_llm_usage,
    build_router_messages,
    build_router_repair_messages,
    structured_result_payload,
)
from .context import _GraphContext, preflight_budget, record_event

__all__: list[str] = []


@dataclass(frozen=True, slots=True)
class _RouterInvocation:
    decision: TaskDecision
    routing_state: dict
    usage: LLMUsage
    budget_warnings: list[str]
    reason_code: str


def _serialized_router_input(messages) -> str:
    text = "\n".join(str(message.content) for message in messages)
    return text + json.dumps(
        RouterDecision.model_json_schema(),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _validation_issue_types(error: BaseException) -> list[dict[str, object]]:
    """Return non-sensitive Pydantic issue locations and codes for telemetry."""
    errors = getattr(error, "errors", None)
    if not callable(errors):
        return []
    return [
        {
            "location": [str(item) for item in issue.get("loc", ())],
            "type": str(issue.get("type", "unknown")),
        }
        for issue in errors()
    ][:8]


def _invoke_repair_once(
    context: _GraphContext,
    state: AgentState,
    *,
    user_task: str,
    first_decision: RouterDecision,
    usage: LLMUsage,
    budget_warnings: list[str],
) -> tuple[RouterDecision, LLMUsage, list[str]]:
    record_event(
        context,
        state,
        "routing.underclassified",
        "classify",
        {
            "hypothesis_count": len(first_decision.outcome_hypotheses),
            "usable_evidence": False,
        },
    )
    messages = build_router_repair_messages(
        context.routing_prompt,
        user_task,
        first_decision,
    )
    input_text = _serialized_router_input(messages)
    repair_state = dict(state)
    repair_state["token_usage"] = usage.model_dump()
    repair_state["budget_warnings"] = budget_warnings
    budget, budget_warnings = preflight_budget(
        context,
        repair_state,
        role="router_repair",
        model=context.router_model_name,
        input_text=input_text,
        reserved_output_tokens=context.router_max_tokens,
        allow_reserve=False,
    )
    if budget.status == "blocked":
        return first_decision, usage, budget_warnings

    started_ns = time.monotonic_ns()
    try:
        structured = context.router.invoke(messages)
        payload, raw = structured_result_payload(structured)
        decision = RouterDecision.model_validate(payload)
        usage = append_llm_usage(
            usage,
            role="router_repair",
            model=context.router_model_name,
            response=raw,
            input_text=input_text,
            output_text=decision.model_dump_json(),
            budget_tokens=context.task_token_budget,
            duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
            price_catalog=context.price_catalog,
        )
        return decision, usage, budget_warnings
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        usage = append_llm_usage(
            usage,
            role="router_repair",
            model=context.router_model_name,
            input_text=input_text,
            output_text="",
            budget_tokens=context.task_token_budget,
            duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
            status="failed",
            price_catalog=context.price_catalog,
        )
        _trace(
            "intent",
            "Outcome repair failed; retaining the first safe classification",
            type(error).__name__,
        )
        return first_decision, usage, budget_warnings


def invoke_router(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
) -> _RouterInvocation:
    """Classify one task, allowing at most one evidence-focused repair call."""
    messages = build_router_messages(context.routing_prompt, state["messages"])
    input_text = _serialized_router_input(messages)
    current_usage = state.get("token_usage")
    budget, budget_warnings = preflight_budget(
        context,
        state,
        role="router",
        model=context.router_model_name,
        input_text=input_text,
        reserved_output_tokens=context.router_max_tokens,
        allow_reserve=False,
    )
    if budget.status == "blocked":
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
        return _RouterInvocation(
            decision=decision,
            routing_state=outcome_routing_state(decision),
            usage=usage,
            budget_warnings=budget_warnings,
            reason_code="budget_fallback",
        )

    started_ns = time.monotonic_ns()
    try:
        structured = context.router.invoke(messages)
        payload, raw = structured_result_payload(structured)
        router_decision = RouterDecision.model_validate(payload)
        usage = append_llm_usage(
            current_usage,
            role="router",
            model=context.router_model_name,
            response=raw,
            input_text=input_text,
            output_text=router_decision.model_dump_json(),
            budget_tokens=context.task_token_budget,
            duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
            price_catalog=context.price_catalog,
        )
        if needs_outcome_repair(user_task, router_decision.outcome_hypotheses):
            router_decision, usage, budget_warnings = _invoke_repair_once(
                context,
                state,
                user_task=user_task,
                first_decision=router_decision,
                usage=usage,
                budget_warnings=budget_warnings,
            )
        hydrated = hydrate_router_decision(router_decision, user_task)
        decision = repair_router_decision(hydrated, user_task)
        return _RouterInvocation(
            decision=decision,
            routing_state=outcome_routing_state(
                decision,
                router_decision.semantic_goal or "",
            ),
            usage=usage,
            budget_warnings=budget_warnings,
            reason_code="provider",
        )
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        record_event(
            context,
            state,
            "routing.provider_failed",
            "classify",
            {
                "error_type": type(error).__name__,
                "validation_issues": _validation_issue_types(error),
            },
        )
        decision = deterministic_router_fallback(user_task, error)
        usage = append_llm_usage(
            current_usage,
            role="router",
            model=context.router_model_name,
            input_text=input_text,
            output_text="",
            budget_tokens=context.task_token_budget,
            duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
            status="failed",
            price_catalog=context.price_catalog,
        )
        _trace(
            "intent",
            "Router provider failed; deterministic fallback selected",
            type(error).__name__,
        )
        return _RouterInvocation(
            decision=decision,
            routing_state=outcome_routing_state(decision),
            usage=usage,
            budget_warnings=budget_warnings,
            reason_code="deterministic_fallback",
        )
