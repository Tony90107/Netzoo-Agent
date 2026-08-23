"""Router invocation, semantic interpretation recovery, and budget handling."""

from __future__ import annotations

from dataclasses import dataclass
import json
import time

from ..contracts import AgentState, LLMUsage, RouterDecision, TaskDecision, _trace
from ..contracts.outcomes import SemanticInterpretation
from ..interpretation.hydration import hydrate_router_decision
from ..interpretation.outcome_validation import (
    OutcomeValidation,
    validate_outcome_hypotheses,
)
from ..interpretation.provider_fallback import (
    _is_fatal_exception,
    deterministic_router_fallback,
)
from ..interpretation.repair import repair_router_decision
from ..interpretation.semantic_goal import outcome_routing_state
from ..llm import (
    append_llm_usage,
    build_router_messages,
    build_semantic_interpreter_messages,
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


def _fail_closed_semantic_decision(decision: RouterDecision) -> RouterDecision:
    """Prevent unvalidated scientific meaning from authorizing a workflow."""
    return decision.model_copy(
        update={
            "action": "no_tool",
            "selected_action": "no_tool",
            "candidate_actions": ["no_tool"],
            "semantic_goal": None,
            "outcome_hypotheses": [],
            "clarification_question": (
                decision.clarification_question
                or "What scientific result do you want NetZoo to produce?"
            ),
        }
    )


def _invoke_semantic_interpreter_once(
    context: _GraphContext,
    state: AgentState,
    *,
    user_task: str,
    first_decision: RouterDecision,
    validation: OutcomeValidation,
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
            "validation_issues": list(validation.issues),
        },
    )
    messages = build_semantic_interpreter_messages(
        context.semantic_prompt,
        user_task,
        validation.issues,
    )
    input_text = _serialized_structured_input(messages, SemanticInterpretation)
    repair_state = dict(state)
    repair_state["token_usage"] = usage.model_dump()
    repair_state["budget_warnings"] = budget_warnings
    budget, budget_warnings = preflight_budget(
        context,
        repair_state,
        role="semantic_interpreter",
        model=context.router_model_name,
        input_text=input_text,
        reserved_output_tokens=context.router_max_tokens,
        allow_reserve=False,
    )
    if budget.status == "blocked":
        return _fail_closed_semantic_decision(first_decision), usage, budget_warnings

    started_ns = time.monotonic_ns()
    try:
        _trace(
            "router",
            "Router classification started",
            {"kind": "router_activity", "operation": "semantic_interpreter", "status": "started"},
        )
        structured = context.semantic_interpreter.invoke(messages)
        payload, raw = structured_result_payload(structured)
        interpretation = SemanticInterpretation.model_validate(payload)
        repaired_validation = validate_outcome_hypotheses(
            user_task,
            interpretation.outcome_hypotheses,
        )
        if not repaired_validation.valid:
            record_event(
                context,
                state,
                "routing.semantic_interpretation_rejected",
                "classify",
                {"issues": list(repaired_validation.issues)},
            )
            raise ValueError("semantic interpretation failed evidence validation")
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
        decision = first_decision.model_copy(
            update={
                "outcome_hypotheses": interpretation.outcome_hypotheses,
                "semantic_goal": interpretation.semantic_goal,
                "clarification_question": None,
            }
        )
        _trace(
            "router",
            "Router classification completed",
            {"kind": "router_activity", "operation": "semantic_interpreter", "status": "completed", "duration_ms": max(0, (time.monotonic_ns() - started_ns) // 1_000_000)},
        )
        usage = append_llm_usage(
            usage,
            role="semantic_interpreter",
            model=context.router_model_name,
            response=raw,
            input_text=input_text,
            output_text=interpretation.model_dump_json(),
            budget_tokens=context.task_token_budget,
            duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
            price_catalog=context.price_catalog,
        )
        return decision, usage, budget_warnings
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
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
            input_text=input_text,
            output_text="",
            budget_tokens=context.task_token_budget,
            duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
            status="failed",
            price_catalog=context.price_catalog,
        )
        _trace("router", "Router classification failed", {"kind": "router_activity", "operation": "semantic_interpreter", "status": "failed", "error_type": type(error).__name__})
        _trace(
            "intent",
            "Outcome repair failed; retaining the first safe classification",
            type(error).__name__,
        )
        return _fail_closed_semantic_decision(first_decision), usage, budget_warnings


def invoke_router(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
) -> _RouterInvocation:
    """Classify one task, allowing at most one semantic interpretation call."""
    messages = build_router_messages(context.routing_prompt, state["messages"])
    input_text = _serialized_structured_input(messages, RouterDecision)
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
        _trace(
            "router",
            "Router classification started",
            {"kind": "router_activity", "operation": "router", "status": "started"},
        )
        structured = context.router.invoke(messages)
        payload, raw = structured_result_payload(structured)
        router_decision = RouterDecision.model_validate(payload)
        _trace(
            "router",
            "Router classification completed",
            {"kind": "router_activity", "operation": "router", "status": "completed", "duration_ms": max(0, (time.monotonic_ns() - started_ns) // 1_000_000)},
        )
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
        validation = validate_outcome_hypotheses(
            user_task,
            router_decision.outcome_hypotheses,
        )
        if not validation.valid and router_decision.action not in {
            "query_context7",
            "web_search",
        }:
            router_decision, usage, budget_warnings = _invoke_semantic_interpreter_once(
                context,
                state,
                user_task=user_task,
                first_decision=router_decision,
                validation=validation,
                usage=usage,
                budget_warnings=budget_warnings,
            )
        hydrated = hydrate_router_decision(router_decision, user_task)
        _trace(
            "reasoning",
            "Checking registered workflow capabilities",
            {"kind": "registry_activity", "status": "started"},
        )
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
        _trace("router", "Router classification failed", {"kind": "router_activity", "operation": "router", "status": "failed", "error_type": type(error).__name__})
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
