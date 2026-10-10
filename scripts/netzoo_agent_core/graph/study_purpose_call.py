"""The study-purpose call: a model proposes, deterministic rules verify (Log 355).

One strict call per new request, after routing. Its proposal is never used
as is: `verify_proposal` keeps only what the request's own words support.
When the call is not configured, blocked by the budget or fails, the word
witnesses read the request as before (Log 342), so a reply never loses the
reading it had. The result is state for the reply layer; the decision is
never touched.
"""

from __future__ import annotations

import time

from pydantic import BaseModel

from ..contracts import AgentState, LLMUsage
from ..contracts.study_purpose import StudyPurposeProposal
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..llm import append_llm_usage, build_study_purpose_messages
from ..routing.study_purpose import StudyPurpose, study_purpose
from ..routing.study_purpose_verify import verify_proposal
from .capability_check_call import with_reading_allowance
from .context import _GraphContext, preflight_budget, record_event
from .structured_calls import _serialized_structured_input, _validation_issue_types

__all__ = ["invoke_study_purpose", "purpose_state"]


def purpose_state(purpose: StudyPurpose, source: str) -> dict:
    """The state entry the reply layer reads (`interpretation.study_purpose_notes.purpose_from_state`)."""
    return {
        "source": source,
        "design": purpose.design,
        "design_quote": purpose.design_quote,
        "claims": [[claim, quote] for claim, quote in purpose.claims],
    }


def _witness_state(context, state, user_task: str, reason: str) -> dict:
    purpose = study_purpose(user_task)
    if purpose.design is not None or purpose.claims:
        record_event(context, state, "routing.study_purpose_detected", "classify", {
            "source": "witness", "reason": reason, **purpose_state(purpose, "witness"),
        })
    return purpose_state(purpose, "witness")


def invoke_study_purpose(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
    usage: LLMUsage,
    budget_warnings: list[str],
) -> tuple[dict, LLMUsage, list[str]]:
    """The verified study purpose of the request, with the call's usage recorded."""
    llm = getattr(context, "study_purpose_llm", None)
    if llm is None:
        return _witness_state(context, state, user_task, "not_configured"), usage, budget_warnings
    messages = build_study_purpose_messages(user_task)
    input_text = _serialized_structured_input(messages, StudyPurposeProposal)
    call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
    # Log 403: the reading allowance the check has (`with_reading_allowance`).
    budget, budget_warnings = preflight_budget(
        with_reading_allowance(context, usage), call_state, role="study_purpose",
        model=context.semantic_model_name, input_text=input_text,
        reserved_output_tokens=context.router_max_tokens, allow_reserve=False,
    )
    if budget.status == "blocked":
        usage.budget_exhausted = True
        return _witness_state(context, state, user_task, "budget"), usage, budget_warnings
    started_ns = time.monotonic_ns()
    raw = None
    payload = None
    output_text = ""
    call_status = "failed"
    try:
        adapter = llm.with_structured_output(
            StudyPurposeProposal, method="function_calling", include_raw=True, strict=True,
        )
        payload, raw = semantic_payload(adapter.invoke(messages))
        if isinstance(payload, BaseModel):
            payload = payload.model_dump()
        proposal = StudyPurposeProposal.model_validate(payload)
        output_text = proposal.model_dump_json()
        call_status = "success"
        purpose, rejected = verify_proposal(user_task, proposal)
        record_event(context, state, "routing.study_purpose_detected", "classify", {
            "source": "model", "proposal": proposal.model_dump(), "rejected": rejected,
            **purpose_state(purpose, "model"),
        })
        result = purpose_state(purpose, "model")
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        record_event(context, state, "routing.study_purpose_failed", "classify", {
            "error_type": type(error).__name__,
            "error_message": str(error)[:2000],
            "validation_issues": _validation_issue_types(error),
            "provider_payload": payload,
        })
        result = _witness_state(context, state, user_task, "call_failed")
    usage = append_llm_usage(
        usage, role="study_purpose", model=context.semantic_model_name,
        response=raw, input_text=input_text, output_text=output_text,
        budget_tokens=context.task_token_budget,
        duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
        status=call_status, price_catalog=context.price_catalog,
    )
    return result, usage, budget_warnings
