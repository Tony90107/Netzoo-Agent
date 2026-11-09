"""Choose the normalization method from what the request says it needs corrected (2026-11-04).

Two places in routing call `normalization_route`:
- before workflow matching, for a request that asks to normalize: a named method is used as named; with none
  named, the need reader is asked which correction the request states, and that decides the method;
- after workflow matching found nothing, for a command about an expression matrix that may describe a
  normalization without the word ("make /data/counts.tsv comparable across sequencing depths"): the need reader
  decides whether it asks to normalize at all.
The reader is one strict model call that proposes needs with quotes; only quotes found in the request are kept
(`normalization_request.verified_needs`). One method fitting the needs is used; several are asked; none stated
leaves SNAIL as the default, said as the default. A failed or unconfigured call never invents a method.
"""

from __future__ import annotations

import time

from pydantic import BaseModel

from ..prior_request import prior_decision
from ..contracts import AgentState, HumanMessage, LLMUsage, SystemMessage
from ..contracts.normalization import NeedReading, NormalizationNeedProposal
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..interpretation.semantic_goal import outcome_routing_state
from ..llm import append_llm_usage
from ..normalization_request import (
    decision_from_needs,
    needs_normalization_reading,
    normalization_decision,
    verified_needs,
)
from ..settings import ROUTER_CONTEXT_MAX_CHARS
from .capability_check_call import with_reading_allowance
from .context import _GraphContext, preflight_budget, record_event
from .invocation_types import RouterInvocation
from .structured_calls import _serialized_structured_input, _validation_issue_types

__all__ = ["invoke_need_reader", "normalization_route"]

NEED_READER_SYSTEM = """You read one request to a gene-regulatory-network toolkit.
Say whether it asks, now, to normalize (rescale, make comparable) the values of an expression or count matrix,
and which corrections it states. Report only what the request itself says; do not recommend a method.
For every need, copy the exact contiguous words of the request that state it into text_span.
- sequencing_depth: the samples differ in sequencing depth, read depth or library size.
- gene_length: the values must account for or be scaled by gene length.
- group_differences: the samples come from different tissues, conditions or groups whose real differences
  must be kept.
- same_distribution: every sample should end with the same distribution of values.
Leave needs empty when the request states none of these."""


def invoke_need_reader(
    context: _GraphContext, state: AgentState, user_task: str, usage: LLMUsage, budget_warnings: list[str],
) -> tuple[tuple[bool, list[NeedReading]] | None, LLMUsage, list[str]]:
    """(asks to normalize, verified needs), or None when the call is not configured, blocked or failed."""
    llm = getattr(context, "study_purpose_llm", None)
    if llm is None:
        return None, usage, budget_warnings
    messages = [SystemMessage(content=NEED_READER_SYSTEM), HumanMessage(content=user_task[-ROUTER_CONTEXT_MAX_CHARS:])]
    input_text = _serialized_structured_input(messages, NormalizationNeedProposal)
    call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
    budget, budget_warnings = preflight_budget(
        (reading := with_reading_allowance(context, usage)), call_state, role="normalization_need",
        model=context.semantic_model_name, input_text=input_text,
        reserved_output_tokens=context.router_max_tokens, allow_reserve=False,
    )
    if budget.status == "blocked":
        return None, usage, budget_warnings
    started_ns = time.monotonic_ns()
    raw, payload, output_text, call_status, result = None, None, "", "failed", None
    try:
        adapter = llm.with_structured_output(
            NormalizationNeedProposal, method="function_calling", include_raw=True, strict=True,
        )
        payload, raw = semantic_payload(adapter.invoke(messages))
        if isinstance(payload, BaseModel):
            payload = payload.model_dump()
        proposal = NormalizationNeedProposal.model_validate(payload)
        output_text = proposal.model_dump_json()
        call_status = "success"
        needs = verified_needs(user_task, proposal.needs)
        record_event(context, state, "routing.normalization_needs_read", "classify", {
            "proposal": proposal.model_dump(), "kept": [need.model_dump() for need in needs],
        })
        result = (proposal.asks_to_normalize, needs)
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        record_event(context, state, "routing.normalization_needs_failed", "classify", {
            "error_type": type(error).__name__, "error_message": str(error)[:2000],
            "validation_issues": _validation_issue_types(error), "provider_payload": payload,
        })
    usage = append_llm_usage(
        usage, role="normalization_need", model=context.semantic_model_name,
        response=raw, input_text=input_text, output_text=output_text,
        budget_tokens=reading.task_token_budget,
        duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
        status=call_status, price_catalog=context.price_catalog,
    )
    return result, usage, budget_warnings


def normalization_route(
    context: _GraphContext, state: AgentState, user_task: str, interpretation, usage: LLMUsage,
    budget_warnings: list[str], *, after_match: bool = False,
) -> RouterInvocation | None:
    """A preparation step for this request -- SPONGE priors or a normalization -- or None to leave it to routing."""
    if not after_match and (priors := prior_decision(user_task, interpretation)) is not None:
        record_event(context, state, "routing.sponge_priors_selected", "classify", {
            "tf_names": priors.sponge_tf_names, "then_action": priors.then_action})
        return RouterInvocation(
            decision=priors, usage=usage, budget_warnings=budget_warnings, reason_code="sponge_priors",
            routing_state=outcome_routing_state(priors, interpretation.semantic_goal, interpretation.request_mode))
    if not after_match:
        decision = normalization_decision(user_task, interpretation)
        if decision is None:
            return None
        if decision.normalization_choice.source == "default":  # "normalize" with no method: read its needs
            read, usage, budget_warnings = invoke_need_reader(context, state, user_task, usage, budget_warnings)
            if read is not None:
                decision = decision_from_needs(user_task, read[1])
        reason_code = "snail_normalization"
    else:
        if not needs_normalization_reading(user_task, interpretation):
            return None
        read, usage, budget_warnings = invoke_need_reader(context, state, user_task, usage, budget_warnings)
        if read is None or not read[0] or not read[1]:  # only a stated need makes an unnamed request a normalization
            return None
        decision = decision_from_needs(user_task, read[1])
        reason_code = "normalization_from_needs"
    record_event(context, state, "routing.normalization_selected", "classify", {
        "method": decision.normalization_method,
        "choice": decision.normalization_choice.model_dump() if decision.normalization_choice else None,
        "reason_code": reason_code,
    })
    return RouterInvocation(
        decision=decision,
        routing_state=outcome_routing_state(decision, interpretation.semantic_goal, interpretation.request_mode),
        usage=usage, budget_warnings=budget_warnings, reason_code=reason_code,
    )
