"""The capability-check call: what the request asks for, against the capability sheet (Log 387).

Its own small call after routing, like the data-facts call (Log 376): routing
keeps its prompt, and this one sees only the request and the sheet. The model
reads meaning; code checks every quote, decides support from the sheet's
produces entries alone, and covers every sentence
(`interpretation.capability_check`). When the call is not configured, blocked by
the budget or fails, nothing is checked and the turn is answered as before.
"""

from __future__ import annotations

import time
from functools import lru_cache

from pydantic import BaseModel

from ..capability_sheet import sheet_entries
from ..contracts import AgentState, HumanMessage, LLMUsage, SystemMessage
from ..contracts.capability_check import MAX_SENTENCES, CapabilityCheck, proposal_model
from ..interpretation.capability_check import build_capability_check, request_sentences
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..llm import append_llm_usage
from ..settings import ROUTER_CONTEXT_MAX_CHARS
from .context import _GraphContext, preflight_budget, record_event
from .structured_calls import _serialized_structured_input, _validation_issue_types

__all__ = ["capability_check_system", "build_capability_check_messages", "invoke_capability_check"]

_INSTRUCTIONS = (
    "Return only the CapabilityCheckProposal for the user's request.\n\n"
    "The request's sentences are numbered after it. For each sentence, list the things it says. Each thing "
    "quotes the sentence's exact words and has a kind:\n"
    "- result: something the user wants produced or answered about their data or biology.\n"
    "- about_methods: a question about the methods themselves -- which to use, how one works, what it needs.\n"
    "- context: what the user has, did, or must respect.\n"
    "If one sentence asks for two results, make two items.\n\n"
    "For each result, delivered_by lists the PRODUCES entries below whose result gives what the quote asks "
    "for, as it is asked. An entry that gives a related result, or only an ingredient of it, does not deliver "
    "it. When no entry gives it, delivered_by is empty -- a normal answer, not a failure. not_by lists the NOT "
    "PRODUCED entries that describe what the quote asks for."
)


@lru_cache(maxsize=1)
def capability_check_system() -> str:
    """The instructions plus the sheet, one line per entry."""
    produces, not_produced = [], []
    for key, item in sheet_entries().items():
        if item.kind == "produces":
            produces.append(f"- {key} [{item.workflow}]: {item.text}")
        else:
            owner = f" [{item.workflow}]" if item.workflow else ""
            not_produced.append(f"- {key}{owner}: {item.text}")
    return "\n\n".join([_INSTRUCTIONS, "PRODUCES:\n" + "\n".join(produces),
                        "NOT PRODUCED:\n" + "\n".join(not_produced)])


def build_capability_check_messages(user_task: str) -> tuple[list, int]:
    """The request, then its sentences numbered as the schema's fields are (s1, s2, ...)."""
    task = user_task[-ROUTER_CONTEXT_MAX_CHARS:]
    sentences = [task[start:end].strip() for start, end in request_sentences(task)][:MAX_SENTENCES]
    numbered = "\n".join(f"{index}. {text}" for index, text in enumerate(sentences, 1))
    return [
        SystemMessage(content=capability_check_system()),
        HumanMessage(content=f"Request:\n{task}\n\nSentences:\n{numbered}"),
    ], max(1, len(sentences))


def invoke_capability_check(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
    usage: LLMUsage,
    budget_warnings: list[str],
    verified_claims: frozenset[str] = frozenset(),
) -> tuple[CapabilityCheck | None, LLMUsage, list[str]]:
    """The verified capability check of the request, or None when nothing read it."""
    # The same model as the study-purpose call, which the graph binds (`study_purpose_llm`).
    llm = getattr(context, "study_purpose_llm", None)
    if llm is None:
        return None, usage, budget_warnings
    messages, count = build_capability_check_messages(user_task)
    schema = proposal_model(count)
    input_text = _serialized_structured_input(messages, schema)
    call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
    budget, budget_warnings = preflight_budget(
        context, call_state, role="capability_check",
        model=context.semantic_model_name, input_text=input_text,
        reserved_output_tokens=context.router_max_tokens, allow_reserve=False,
    )
    if budget.status == "blocked":
        usage.budget_exhausted = True
        return None, usage, budget_warnings
    started_ns = time.monotonic_ns()
    raw = payload = None
    output_text, call_status, result = "", "failed", None
    try:
        adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
        payload, raw = semantic_payload(adapter.invoke(messages))
        if isinstance(payload, BaseModel):
            payload = payload.model_dump()
        proposal = schema.model_validate(payload)
        output_text = proposal.model_dump_json()
        call_status = "success"
        result, rejected = build_capability_check(user_task, proposal, verified_claims)
        record_event(context, state, "routing.capability_checked", "classify", {
            "proposal": proposal.model_dump(), "rejected": rejected, "check": result.model_dump(),
        })
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        record_event(context, state, "routing.capability_check_failed", "classify", {
            "error_type": type(error).__name__,
            "error_message": str(error)[:2000],
            "validation_issues": _validation_issue_types(error),
            "provider_payload": payload,
        })
    usage = append_llm_usage(
        usage, role="capability_check", model=context.semantic_model_name,
        response=raw, input_text=input_text, output_text=output_text,
        budget_tokens=context.task_token_budget,
        duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
        status=call_status, price_catalog=context.price_catalog,
    )
    return result, usage, budget_warnings
