"""Semantic → evidence → registry → intent routing pipeline."""

from __future__ import annotations

from dataclasses import dataclass
import json
import time

from ..contracts import AgentState, IntentDecision, LLMUsage, TaskDecision, _trace
from ..contracts.outcomes import CapabilityMatch, SemanticInterpretation
from ..interpretation.assembly import assemble_task_decision
from ..interpretation.hydration import hydrate_router_decision
from ..interpretation.outcome_validation import validate_outcome_hypotheses
from ..interpretation.provider_fallback import (
    _is_fatal_exception,
    deterministic_router_fallback,
)
from ..interpretation.semantic_goal import outcome_routing_state
from ..llm import (
    append_llm_usage,
    build_intent_router_messages,
    build_semantic_interpreter_messages,
    structured_result_payload,
)
from ..routing.outcome_matching import match_semantic_request
from .context import _GraphContext, preflight_budget, record_event

__all__: list[str] = []


@dataclass(frozen=True, slots=True)
class _RouterInvocation:
    decision: TaskDecision
    routing_state: dict
    usage: LLMUsage
    budget_warnings: list[str]
    reason_code: str


def _serialized_structured_input(messages, schema_model) -> str:
    text = "\n".join(str(message.content) for message in messages)
    return text + json.dumps(
        schema_model.model_json_schema(),
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


def _current_usage(context: _GraphContext, state: AgentState) -> LLMUsage:
    current = state.get("token_usage")
    return (
        LLMUsage.model_validate(current)
        if current
        else LLMUsage(budget_tokens=context.task_token_budget)
    )


def _semantic_failure(
    context: _GraphContext,
    user_task: str,
    usage: LLMUsage,
    budget_warnings: list[str],
    *,
    error: BaseException | None = None,
    reason_code: str,
) -> _RouterInvocation:
    decision = deterministic_router_fallback(user_task, error)
    return _RouterInvocation(
        decision=decision,
        routing_state=outcome_routing_state(decision),
        usage=usage,
        budget_warnings=budget_warnings,
        reason_code=reason_code,
    )


def _invoke_semantic_interpreter(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
    usage: LLMUsage,
) -> tuple[SemanticInterpretation | None, LLMUsage, list[str], BaseException | None]:
    messages = build_semantic_interpreter_messages(context.semantic_prompt, user_task)
    input_text = _serialized_structured_input(messages, SemanticInterpretation)
    budget, budget_warnings = preflight_budget(
        context,
        state,
        role="semantic_interpreter",
        model=context.router_model_name,
        input_text=input_text,
        reserved_output_tokens=context.router_max_tokens,
        allow_reserve=False,
    )
    if budget.status == "blocked":
        usage.budget_exhausted = True
        return None, usage, budget_warnings, None

    started_ns = time.monotonic_ns()
    raw = None
    output_text = ""
    try:
        _trace(
            "router",
            "Semantic interpretation started",
            {
                "kind": "router_activity",
                "operation": "semantic_interpreter",
                "status": "started",
            },
        )
        structured = context.semantic_interpreter.invoke(messages)
        payload, raw = structured_result_payload(structured)
        interpretation = SemanticInterpretation.model_validate(payload)
        output_text = interpretation.model_dump_json()
        validation = validate_outcome_hypotheses(
            user_task,
            interpretation.outcome_hypotheses,
        )
        if not validation.valid:
            record_event(
                context,
                state,
                "routing.semantic_interpretation_rejected",
                "classify",
                {"issues": list(validation.issues)},
            )
            raise ValueError("semantic interpretation failed evidence validation")
        duration_ms = max(0, (time.monotonic_ns() - started_ns) // 1_000_000)
        usage = append_llm_usage(
            usage,
            role="semantic_interpreter",
            model=context.router_model_name,
            response=raw,
            input_text=input_text,
            output_text=output_text,
            budget_tokens=context.task_token_budget,
            duration_ms=duration_ms,
            price_catalog=context.price_catalog,
        )
        record_event(
            context,
            state,
            "routing.semantic_interpretation_accepted",
            "classify",
            {
                "hypothesis_count": len(interpretation.outcome_hypotheses),
                "evidence_dimensions": [
                    sorted({item.dimension for item in hypothesis.evidence})
                    for hypothesis in interpretation.outcome_hypotheses
                ],
            },
        )
        _trace(
            "router",
            "Semantic interpretation completed",
            {
                "kind": "router_activity",
                "operation": "semantic_interpreter",
                "status": "completed",
                "duration_ms": duration_ms,
            },
        )
        return interpretation, usage, budget_warnings, None
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        duration_ms = max(0, (time.monotonic_ns() - started_ns) // 1_000_000)
        record_event(
            context,
            state,
            "routing.semantic_interpreter_failed",
            "classify",
            {
                "error_type": type(error).__name__,
                "validation_issues": _validation_issue_types(error),
            },
        )
        usage = append_llm_usage(
            usage,
            role="semantic_interpreter",
            model=context.router_model_name,
            response=raw,
            input_text=input_text,
            output_text=output_text,
            budget_tokens=context.task_token_budget,
            duration_ms=duration_ms,
            status="failed",
            price_catalog=context.price_catalog,
        )
        _trace(
            "router",
            "Semantic interpretation failed",
            {
                "kind": "router_activity",
                "operation": "semantic_interpreter",
                "status": "failed",
                "error_type": type(error).__name__,
            },
        )
        return None, usage, budget_warnings, error


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


def invoke_router(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
) -> _RouterInvocation:
    """Run the ordered semantic, validation, registry, and intent pipeline."""
    usage = _current_usage(context, state)
    interpretation, usage, budget_warnings, semantic_error = (
        _invoke_semantic_interpreter(context, state, user_task, usage)
    )
    if interpretation is None:
        return _semantic_failure(
            context,
            user_task,
            usage,
            budget_warnings,
            error=semantic_error,
            reason_code=("budget_fallback" if semantic_error is None else "semantic_fallback"),
        )

    _trace(
        "reasoning",
        "Checking registered workflow capabilities",
        {"kind": "registry_activity", "status": "started"},
    )
    capability_match = match_semantic_request(
        user_task,
        interpretation.outcome_hypotheses,
    )
    record_event(
        context,
        state,
        "routing.registry_match_completed",
        "classify",
        {
            "status": capability_match.status,
            "matched_actions": capability_match.matched_actions,
            "hypothesis_actions": capability_match.hypothesis_actions,
            "mismatch_dimensions": capability_match.mismatch_dimensions,
        },
    )

    intent, usage, budget_warnings, intent_fallback = _invoke_intent_router(
        context,
        state,
        user_task,
        interpretation,
        capability_match,
        usage,
        budget_warnings,
    )
    decision = assemble_task_decision(
        interpretation,
        capability_match,
        intent,
        task=user_task,
    )
    decision = hydrate_router_decision(decision, user_task)
    return _RouterInvocation(
        decision=decision,
        routing_state=outcome_routing_state(decision, interpretation.semantic_goal),
        usage=usage,
        budget_warnings=budget_warnings,
        reason_code="intent_fallback" if intent_fallback else "semantic_registry_intent",
    )
