"""Intent classification: is the user asking, or telling the agent to act?

Split out of `router_invocation` when that module passed the reviewable-size
limit. This is the pipeline's third stage and its own responsibility -- it reads
the request's mood, never its science, and cannot select or reject a capability.
It runs after the registry match precisely so that it classifies against a
decided candidate rather than deciding one.
"""

from __future__ import annotations

import time

from ..contracts import AgentState, IntentDecision, LLMUsage, _trace
from ..contracts.outcomes import CapabilityMatch, SemanticInterpretation
from ..interpretation.provider_fallback import _is_fatal_exception
from ..llm import (
    append_llm_usage,
    build_intent_router_messages,
    structured_result_payload,
)
from .context import _GraphContext, preflight_budget, record_event
from .structured_calls import _serialized_structured_input, _validation_issue_types

__all__: list[str] = []


def _invoke_intent_router(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
    interpretation: SemanticInterpretation,
    capability_match: CapabilityMatch,
    usage: LLMUsage,
    budget_warnings: list[str],
) -> tuple[IntentDecision, LLMUsage, list[str], bool]:
    messages = build_intent_router_messages(
        context.intent_prompt,
        user_task,
        interpretation,
        capability_match,
    )
    input_text = _serialized_structured_input(messages, IntentDecision)
    intent_state = dict(state)
    intent_state["token_usage"] = usage.model_dump()
    intent_state["budget_warnings"] = budget_warnings
    budget, budget_warnings = preflight_budget(
        context,
        intent_state,
        role="intent_router",
        model=context.router_model_name,
        input_text=input_text,
        reserved_output_tokens=context.router_max_tokens,
        allow_reserve=False,
    )
    if budget.status == "blocked":
        usage.budget_exhausted = True
        return (
            IntentDecision(
                mode="answer",
                confidence=0.0,
                reason="Intent classification was skipped because the token budget was exhausted.",
            ),
            usage,
            budget_warnings,
            True,
        )

    started_ns = time.monotonic_ns()
    raw = None
    try:
        _trace(
            "intent",
            "Intent classification started",
            {"kind": "intent_activity", "status": "started"},
        )
        structured = context.intent_router.invoke(messages)
        payload, raw = structured_result_payload(structured)
        intent = IntentDecision.model_validate(payload)
        duration_ms = max(0, (time.monotonic_ns() - started_ns) // 1_000_000)
        usage = append_llm_usage(
            usage,
            role="intent_router",
            model=context.router_model_name,
            response=raw,
            input_text=input_text,
            output_text=intent.model_dump_json(),
            budget_tokens=context.task_token_budget,
            duration_ms=duration_ms,
            price_catalog=context.price_catalog,
        )
        record_event(
            context,
            state,
            "routing.intent_classified",
            "classify",
            {"mode": intent.mode, "confidence": intent.confidence},
        )
        _trace(
            "intent",
            "Intent classification completed",
            {
                "kind": "intent_activity",
                "status": "completed",
                "duration_ms": duration_ms,
            },
        )
        return intent, usage, budget_warnings, False
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        duration_ms = max(0, (time.monotonic_ns() - started_ns) // 1_000_000)
        record_event(
            context,
            state,
            "routing.intent_router_failed",
            "classify",
            {
                "error_type": type(error).__name__,
                "validation_issues": _validation_issue_types(error),
            },
        )
        usage = append_llm_usage(
            usage,
            role="intent_router",
            model=context.router_model_name,
            response=raw,
            input_text=input_text,
            output_text="",
            budget_tokens=context.task_token_budget,
            duration_ms=duration_ms,
            status="failed",
            price_catalog=context.price_catalog,
        )
        return (
            IntentDecision(
                mode="answer",
                confidence=0.0,
                reason="Intent classification failed, so execution was not authorized.",
            ),
            usage,
            budget_warnings,
            True,
        )
