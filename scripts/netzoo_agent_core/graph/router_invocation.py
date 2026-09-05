"""Semantic → evidence → registry → intent routing pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import re
import time

from pydantic import ValidationError
from workflow_registry import OUTPUT_CAPABILITIES

from ..contracts import AgentState, IntentDecision, LLMUsage, TaskDecision, _trace
from ..contracts.interaction import WorkflowContinuation
from ..contracts.outcomes import (
    CapabilityMatch,
    RequestedOutcome,
    SemanticInterpretation,
    SemanticReview,
)
from ..interpretation.assembly import assemble_task_decision
from ..interpretation.hydration import hydrate_router_decision
from ..interpretation.outcome_validation import validate_outcome_hypotheses
from ..interpretation.provider_fallback import (
    _is_fatal_exception,
    deterministic_router_fallback,
    recover_registry_guidance,
)
from ..interpretation.semantic_goal import outcome_routing_state
from ..interpretation.semantic_repair import semantic_payload
from ..llm import (
    append_llm_usage,
    build_intent_router_messages,
    build_semantic_interpreter_messages,
    build_semantic_reviewer_messages,
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


# A rejected ontology literal is model vocabulary worth recording; free text may
# quote the request, so only identifier-shaped values are retained.
_IDENTIFIER_VALUE = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,63}")


def _validation_issue_types(error: BaseException) -> list[dict[str, object]]:
    """Return non-sensitive Pydantic issue locations, codes and shapes.

    The rejected value's type name records what shape a provider actually sent,
    which the September traces could not answer. Its content is kept only when it
    is a bare canonical-looking identifier, never as arbitrary request text.
    """
    errors = getattr(error, "errors", None)
    if not callable(errors):
        return []
    issues = []
    for issue in errors():
        value = issue.get("input")
        recorded = {
            "location": [str(item) for item in issue.get("loc", ())],
            "type": str(issue.get("type", "unknown")),
            "input_type": type(value).__name__,
        }
        if isinstance(value, str) and _IDENTIFIER_VALUE.fullmatch(value):
            recorded["input_value"] = value
        if isinstance(value, Mapping):
            # Field names an object was built from are model-chosen schema terms,
            # so they name the wrong shape without retaining any request content.
            recorded["input_keys"] = sorted(
                key for key in value
                if isinstance(key, str) and _IDENTIFIER_VALUE.fullmatch(key)
            )[:8]
        issues.append(recorded)
    return issues[:8]


# A third, progress-gated attempt was tried and reverted. It fired twice in nine
# live trials and made the outcome worse both times: the extra review dropped an
# input it had already recovered and added ungrounded evidence, while the error
# it was meant to fix survived. Overall passes were unchanged, so it bought an
# extra call and nothing else. See tests/test_semantic_attempt_bound.py.
MAX_SEMANTIC_ATTEMPTS = 2


def _current_usage(context: _GraphContext, state: AgentState) -> LLMUsage:
    current = state.get("token_usage")
    return (
        LLMUsage.model_validate(current)
        if current
        else LLMUsage(budget_tokens=context.task_token_budget)
    )


def _semantic_failure(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
    usage: LLMUsage,
    budget_warnings: list[str],
    *,
    error: BaseException | None = None,
    reason_code: str,
) -> _RouterInvocation:
    decision = deterministic_router_fallback(user_task, error)
    recovered = recover_registry_guidance(
        user_task,
        context.project_policy.workflows,
        error,
    )
    if recovered is not None:
        decision = recovered
        record_event(
            context,
            state,
            "routing.semantic_guidance_recovered",
            "classify",
            {
                "matched_actions": decision.matched_actions,
                "reason_code": decision.match_basis,
                "match_status": decision.capability_match_status,
            },
        )
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
    validation_issues: tuple[str, ...] = ()
    budget_warnings = list(state.get("budget_warnings", []))
    last_error: BaseException | None = None
    proposal = None
    # The reviewer is a second opinion, not a precondition. An interpretation
    # that already satisfied every check is kept if the review that follows does
    # not, because discarding both leaves a registry guess naming no workflow.
    validated: SemanticInterpretation | None = None
    for attempt in range(MAX_SEMANTIC_ATTEMPTS):
        role = "semantic_interpreter" if attempt == 0 else "semantic_reviewer"
        adapter = (
            context.semantic_interpreter if attempt == 0 else context.semantic_reviewer
        )
        messages = (
            build_semantic_reviewer_messages(
                context.semantic_prompt,
                user_task,
                proposal,
                validation_issues,
            )
            if attempt == 1
            else build_semantic_interpreter_messages(
                context.semantic_prompt,
                user_task,
                validation_issues,
            )
        )
        schema_model = SemanticInterpretation if attempt == 0 else SemanticReview
        input_text = _serialized_structured_input(messages, schema_model)
        semantic_state = dict(state)
        semantic_state["token_usage"] = usage.model_dump()
        semantic_state["budget_warnings"] = budget_warnings
        budget, budget_warnings = preflight_budget(
            context,
            semantic_state,
            role=role,
            model=context.semantic_model_name,
            input_text=input_text,
            reserved_output_tokens=context.router_max_tokens,
            allow_reserve=False,
        )
        if budget.status == "blocked":
            usage.budget_exhausted = True
            return None, usage, budget_warnings, last_error

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
                    "attempt": attempt + 1,
                },
            )
            structured = adapter.invoke(messages)
            payload, raw = semantic_payload(structured)
            if attempt == 0:
                proposal = payload
            if attempt == 0:
                interpretation = SemanticInterpretation.model_validate(payload)
                output_text = interpretation.model_dump_json()
            else:
                review = SemanticReview.model_validate(payload)
                output_text = review.model_dump_json()
                interpretation = SemanticInterpretation(
                    request_mode=review.request_mode,
                    semantic_goal=review.semantic_goal,
                    outcome_hypotheses=[review.outcome_hypothesis],
                )
            if attempt == 0:
                proposal = interpretation
        except BaseException as error:
            if _is_fatal_exception(error):
                raise
            duration_ms = max(0, (time.monotonic_ns() - started_ns) // 1_000_000)
            schema_issues = _validation_issue_types(error)
            usage = append_llm_usage(
                usage,
                role=role,
                model=context.semantic_model_name,
                response=raw,
                input_text=input_text,
                output_text=output_text,
                budget_tokens=context.task_token_budget,
                duration_ms=duration_ms,
                status="failed",
                price_catalog=context.price_catalog,
            )
            if attempt == 0 and schema_issues:
                validation_issues = tuple(
                    "schema_validation:"
                    + ".".join(issue["location"])
                    + ":"
                    + str(issue["type"])
                    for issue in schema_issues
                )
                last_error = error
                record_event(
                    context,
                    state,
                    "routing.semantic_interpretation_rejected",
                    "classify",
                    # Keep the located shapes beside the flattened issue strings:
                    # the first attempt is where a rejected value is otherwise lost.
                    {"attempt": 1, "issues": list(validation_issues), "shapes": schema_issues},
                )
                record_event(
                    context,
                    state,
                    "routing.semantic_interpretation_retried",
                    "classify",
                    {"issues": list(validation_issues)},
                )
                continue
            record_event(
                context,
                state,
                "routing.semantic_interpreter_failed",
                "classify",
                {
                    "attempt": attempt + 1,
                    "error_type": type(error).__name__,
                    "validation_issues": schema_issues,
                },
            )
            if recover_registry_guidance(
                user_task,
                context.project_policy.workflows,
                error,
            ) is None:
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

        validation = validate_outcome_hypotheses(
            user_task,
            interpretation.outcome_hypotheses,
        )
        duration_ms = max(0, (time.monotonic_ns() - started_ns) // 1_000_000)
        if not validation.valid:
            usage = append_llm_usage(
                usage,
                role=role,
                model=context.semantic_model_name,
                response=raw,
                input_text=input_text,
                output_text=output_text,
                budget_tokens=context.task_token_budget,
                duration_ms=duration_ms,
                status="failed",
                price_catalog=context.price_catalog,
            )
            record_event(
                context,
                state,
                "routing.semantic_interpretation_rejected",
                "classify",
                {"attempt": attempt + 1, "issues": list(validation.issues)},
            )
            last_error = ValueError(
                "semantic interpretation failed evidence validation"
            )
            if attempt + 1 < MAX_SEMANTIC_ATTEMPTS:
                validation_issues = validation.issues
                record_event(
                    context,
                    state,
                    "routing.semantic_interpretation_retried",
                    "classify",
                    {"issues": list(validation_issues)},
                )
                continue
            record_event(
                context,
                state,
                "routing.semantic_interpreter_failed",
                "classify",
                {
                    "attempt": attempt + 1,
                    "error_type": type(last_error).__name__,
                    "validation_issues": list(validation.issues),
                },
            )
            if validated is not None:
                record_event(
                    context,
                    state,
                    "routing.semantic_review_discarded",
                    "classify",
                    {"attempt": attempt + 1, "issues": list(validation.issues)},
                )
                return validated, usage, budget_warnings, None
            return None, usage, budget_warnings, last_error

        usage = append_llm_usage(
            usage,
            role=role,
            model=context.semantic_model_name,
            response=raw,
            input_text=input_text,
            output_text=output_text,
            budget_tokens=context.task_token_budget,
            duration_ms=duration_ms,
            price_catalog=context.price_catalog,
        )
        validated = interpretation
        if attempt == 0:
            preliminary_match = match_semantic_request(
                user_task,
                interpretation.outcome_hypotheses,
                request_mode=interpretation.request_mode,
            )
            if preliminary_match.status == "ambiguous":
                validation_issues = (
                    "registry_ambiguity:the structured outcome does not uniquely "
                    "identify a capability; re-check the original request for explicit "
                    "biological entity, regulator, target, and granularity roles",
                )
            record_event(
                context,
                state,
                "routing.semantic_interpretation_proposed",
                "classify",
                {
                    "hypothesis_count": len(interpretation.outcome_hypotheses),
                    "evidence_dimensions": [
                        sorted({item.dimension for item in hypothesis.evidence})
                        for hypothesis in interpretation.outcome_hypotheses
                    ],
                    "registry_match_status": preliminary_match.status,
                },
            )
            continue

        record_event(
            context,
            state,
            "routing.semantic_interpretation_accepted",
            "classify",
            {
                "attempt": attempt + 1,
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
                "attempt": attempt + 1,
            },
        )
        return interpretation, usage, budget_warnings, None

    return None, usage, budget_warnings, last_error


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
    if state.get("workflow_continuation") is not None:
        return _continue_workflow(context, state, user_task, usage)
    interpretation, usage, budget_warnings, semantic_error = (
        _invoke_semantic_interpreter(context, state, user_task, usage)
    )
    if interpretation is None:
        return _semantic_failure(
            context,
            state,
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
        request_mode=interpretation.request_mode,
    )
    record_event(
        context,
        state,
        "routing.registry_match_completed",
        "classify",
        {
            "status": capability_match.status,
            "match_basis": capability_match.match_basis,
            "rejected_methods": [item.model_dump() for item in capability_match.rejected_methods],
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
        routing_state=outcome_routing_state(
            decision,
            interpretation.semantic_goal,
            interpretation.request_mode,
        ),
        usage=usage,
        budget_warnings=budget_warnings,
        reason_code=("intent_fallback" if intent_fallback else
                     "registry_guidance_fallback" if capability_match.status == "fallback" else
                     "semantic_registry_intent"),
    )


def _continue_workflow(
    context: _GraphContext,
    state: AgentState,
    task: str,
    usage: LLMUsage,
) -> _RouterInvocation:
    """Plan a CLI-validated selection without asking models to select it again."""
    try:
        continuation = WorkflowContinuation.model_validate(state["workflow_continuation"])
        if (
            continuation.task != task
            or continuation.action not in context.project_policy.workflows
        ):
            raise ValueError("The continuation does not match the current task and policy.")
    except (ValidationError, ValueError):
        decision = TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            confidence=0.0,
            intent_type="answer_question",
            reason="The workflow continuation is invalid or stale; select the workflow again.",
        )
        reason_code = "invalid_workflow_continuation"
    else:
        action = continuation.action
        capability = OUTPUT_CAPABILITIES[action]
        granularity = (
            next(iter(capability.granularities))
            if len(capability.granularities) == 1
            else "unknown"
        )
        decision = hydrate_router_decision(
            TaskDecision(
                action=action,
                in_scope=True,
                should_execute=True,
                confidence=1.0,
                intent_type="run_analysis",
                reason="Preparing the workflow selected in the current CLI continuation.",
                candidate_actions=[action, "no_tool"],
                matched_actions=[action],
                recommended_actions=[action],
                capability_match_status="exact",
                requested_outcome=RequestedOutcome(
                    operation=capability.operation,
                    artifact_type=capability.artifact_type,
                    entity_types=sorted(capability.entity_types),
                    regulator_types=sorted(capability.regulator_types),
                    target_types=sorted(capability.target_types),
                    granularity=granularity,
                    unresolved_dimensions=(
                        ["granularity"] if granularity == "unknown" else []
                    ),
                ),
            ),
            task,
        )
        reason_code = "workflow_continuation"
    record_event(
        context, state, "routing.workflow_continuation", "classify",
        {
            "action": decision.action,
            "reason_code": reason_code,
            "purpose": "planning",
            "execution_authorized": False,
        },
    )
    return _RouterInvocation(
        decision=decision,
        routing_state=outcome_routing_state(
            decision,
            decision.reason,
            "execute" if decision.action != "no_tool" else "unknown",
        ),
        usage=usage,
        budget_warnings=list(state.get("budget_warnings", [])),
        reason_code=reason_code,
    )
