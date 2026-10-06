"""The data-facts call: what the request says about its TF priors (Log 376).

Log 379 (plan item 3): asked only when the stated conclusion could pick a
workflow that needs a TF motif prior and a PPI network
(`routing.purpose_selection`); only a "stated" reading lets it be picked, so
"unstated" and "ruled_out" both withhold the pick (Log 377's never-ask bug was
"unstated" read as known).
The model reads what the words mean; the quote is checked only for being in
the request (Logs 373-374: word lists judging meaning failed both ways). When
the call is not configured, blocked by the budget or fails, nothing is read
and the reply falls back to its word lists.
"""

from __future__ import annotations

import time

from pydantic import BaseModel

from ..contracts import AgentState, LLMUsage
from ..contracts.data_facts import DataFactsProposal
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..llm import append_llm_usage, build_data_facts_messages
from ..routing.study_purpose_verify import _locate
from .context import _GraphContext, preflight_budget, record_event
from .structured_calls import _serialized_structured_input, _validation_issue_types

__all__ = ["invoke_data_facts", "verify_data_facts"]


def verify_data_facts(task: str, proposal: DataFactsProposal) -> tuple[dict, list[dict]]:
    """The state entry for a proposal: its reading when the quote is in the request, else unstated."""
    if proposal.priors != "unstated":
        if _locate(task, proposal.priors_span) is not None:
            return {"source": "model", "priors": proposal.priors, "priors_quote": proposal.priors_span.strip()}, []
        return ({"source": "model", "priors": "unstated", "priors_quote": ""},
                [{"field": "priors", "value": proposal.priors, "reason": "quote_not_in_request"}])
    return {"source": "model", "priors": "unstated", "priors_quote": ""}, []


def invoke_data_facts(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
    usage: LLMUsage,
    budget_warnings: list[str],
) -> tuple[dict | None, LLMUsage, list[str]]:
    """The verified data facts of the request, or None when nothing read them."""
    # The same model as the study-purpose call, which the graph binds (`study_purpose_llm`).
    llm = getattr(context, "study_purpose_llm", None)
    if llm is None:
        return None, usage, budget_warnings
    messages = build_data_facts_messages(user_task)
    input_text = _serialized_structured_input(messages, DataFactsProposal)
    call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
    budget, budget_warnings = preflight_budget(
        context, call_state, role="data_facts",
        model=context.semantic_model_name, input_text=input_text,
        reserved_output_tokens=context.router_max_tokens, allow_reserve=False,
    )
    if budget.status == "blocked":
        usage.budget_exhausted = True
        return None, usage, budget_warnings
    started_ns = time.monotonic_ns()
    raw = None
    payload = None
    output_text = ""
    call_status = "failed"
    result = None
    try:
        adapter = llm.with_structured_output(
            DataFactsProposal, method="function_calling", include_raw=True, strict=True,
        )
        payload, raw = semantic_payload(adapter.invoke(messages))
        if isinstance(payload, BaseModel):
            payload = payload.model_dump()
        proposal = DataFactsProposal.model_validate(payload)
        output_text = proposal.model_dump_json()
        call_status = "success"
        result, rejected = verify_data_facts(user_task, proposal)
        record_event(context, state, "routing.data_facts_detected", "classify", {
            "proposal": proposal.model_dump(), "rejected": rejected, **result,
        })
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        record_event(context, state, "routing.data_facts_failed", "classify", {
            "error_type": type(error).__name__,
            "error_message": str(error)[:2000],
            "validation_issues": _validation_issue_types(error),
            "provider_payload": payload,
        })
    usage = append_llm_usage(
        usage, role="data_facts", model=context.semantic_model_name,
        response=raw, input_text=input_text, output_text=output_text,
        budget_tokens=context.task_token_budget,
        duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
        status=call_status, price_catalog=context.price_catalog,
    )
    return result, usage, budget_warnings
