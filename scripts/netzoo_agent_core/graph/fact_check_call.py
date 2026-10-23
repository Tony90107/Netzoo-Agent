"""Core decision spec, phase 2: the fact agent's call (section 6) -- once per turn whose goal is clear.

It reads the request beside the candidate workflows' contracts and proposes the facts the user is unsure of that
decide the call; `interpretation.fact_check.kept_facts` holds them to R1-R6. When there is no candidate, no model,
no budget or the call fails, the turn keeps its existing (legacy) asks: `FactCheck.status` says which.
"""

from __future__ import annotations

import os
import time
from dataclasses import replace

from pydantic import BaseModel

from ..contracts.fact_check import FactCheck, FactProposals
from ..interpretation.fact_check import fact_candidates, kept_facts
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..llm import append_llm_usage
from .capability_check_call import _check_model, with_reading_allowance
from .context import preflight_budget, record_event
from .required_check_budget import check_output_reserve, fact_check_input, retryable_check_error

__all__ = ["apply_fact_check", "fact_model", "invoke_fact_agent", "request_fact_check"]


def fact_model(context):
    """NETZOO_FACT_MODEL: `check` (the capability check's own model) or `router` (the routing model, default)."""
    if os.environ.get("NETZOO_FACT_MODEL", "router") == "check":
        return _check_model(context)
    return getattr(context, "semantic_model_name", None), getattr(context, "study_purpose_llm", None)


def invoke_fact_agent(llm, task: str, actions: list[str], policy):
    """One structured call; (proposals or None, raw, input text, output text, error)."""
    messages, input_text = fact_check_input(task, actions, policy)
    raw = payload = None
    try:
        adapter = llm.with_structured_output(FactProposals, method="function_calling", include_raw=True, strict=True)
        response = adapter.invoke(messages)
        raw = response.get("raw") if isinstance(response, dict) else None
        payload, raw = semantic_payload(response)
        if isinstance(payload, BaseModel):
            payload = payload.model_dump()
        parsed = FactProposals.model_validate(payload)
        return parsed, raw, input_text, parsed.model_dump_json(), None
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        return None, raw, input_text, "", error


def request_fact_check(context, state, user_task: str, decision, usage, budget_warnings):
    policy = getattr(context, "project_policy", None)
    model, llm = fact_model(context)
    actions = fact_candidates(decision, policy) if policy is not None else []
    if llm is None or not actions:
        return FactCheck(status="not_run"), usage, budget_warnings
    names = [policy.workflows[action].workflow for action in actions]
    _, input_text = fact_check_input(user_task, actions, policy)
    reading = with_reading_allowance(context, usage)
    for attempt in (1, 2):
        if usage.budget_exhausted:
            return FactCheck(status="blocked", model=model or "", candidates=names), usage, budget_warnings
        call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
        budget, budget_warnings = preflight_budget(
            reading, call_state, role="fact_check", model=model, input_text=input_text,
            reserved_output_tokens=check_output_reserve(context, llm), allow_reserve=False,
        )
        if budget.status == "blocked":
            return FactCheck(status="blocked", model=model or "", candidates=names), usage, budget_warnings
        started_ns = time.monotonic_ns()
        proposals, raw, input_text, output_text, error = invoke_fact_agent(llm, user_task, actions, policy)
        if error is not None:
            record_event(context, state, "core.fact_check_failed", "classify", {
                "attempt": attempt, "error_type": type(error).__name__, "error_message": str(error)[:2000]})
        usage = append_llm_usage(
            usage, role="fact_check", model=model, response=raw, input_text=input_text, output_text=output_text,
            budget_tokens=reading.task_token_budget,
            duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
            status="success" if error is None else "failed", price_catalog=context.price_catalog,
        )
        if proposals is not None:
            return kept_facts(user_task, proposals, decision, policy, model=model or ""), usage, budget_warnings
        if not retryable_check_error(error):
            break
    return FactCheck(status="failed", model=model or "", candidates=names), usage, budget_warnings


def apply_fact_check(context, state, user_task: str, result, decision, check):
    """Phase 2: the fact agent at the point the legacy dimensions would wait on a fact (`_with_capability_check`).

    The legacy questions are recorded beside the agent's and the check's waits stand: `decide_core` asks the agent's
    questions with each wait on other words, or queues it (harness repair P1, `interpretation.obligations`). Until P1
    an agent that asked anything lifted every wait -- the row credited as if the favourable answer were given, or made
    not available when nothing was delivered (P0 fixtures F03, F04). Returns (result, decision, check).
    """
    from ..interpretation.core_decision import _facts, goal_unclear

    if goal_unclear(check, decision, user_task):  # CLARIFY comes first (spec section 3)
        return result, decision, check
    facts, usage, warnings = request_fact_check(context, state, user_task,
                                                decision.model_copy(update={"capability_check": check}),
                                                result.usage, result.budget_warnings)
    if facts.status == "not_run":  # no model (tests, the routing harness) or no candidate: nothing changes
        return result, decision, check
    result = replace(result, usage=usage, budget_warnings=warnings)
    if facts.status == "checked":
        facts = facts.model_copy(update={"legacy": _facts(check, by_code=False, task=user_task)})
    record_event(context, state, "core.fact_check", "classify", facts.model_dump(mode="json"))
    decision = decision.model_copy(update={"fact_check": facts})
    return replace(result, decision=decision), decision, check  # the run path reads result.decision
