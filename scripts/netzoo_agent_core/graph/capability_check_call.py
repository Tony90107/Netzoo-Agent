"""The capability-check call: what the request asks for, against the capability sheet (Log 387).

Its own small call after routing, like the data-facts call (Log 376): routing
keeps its prompt, and this one sees only the request and the sheet. The model
reads meaning; code checks every quote, decides support from the sheet's
produces entries alone, and covers every sentence
(`interpretation.capability_check`). When the call is not configured, blocked by
the budget or fails, nothing is checked and the turn is answered as before.
"""

from __future__ import annotations

import os
import time
from functools import lru_cache

from pydantic import BaseModel

from ..capability_sheet import sheet_entries
from ..contracts import AgentState, HumanMessage, LLMUsage, SystemMessage
from ..contracts.capability_check import MAX_SENTENCES, proposal_model
from ..interpretation.capability_check import request_sentences
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..llm import append_llm_usage
from ..settings import ROUTER_CONTEXT_MAX_CHARS
from .context import _GraphContext, preflight_budget, record_event
from .structured_calls import _serialized_structured_input, _validation_issue_types

__all__ = ["capability_check_system", "build_capability_check_messages", "request_capability_check"]

_INSTRUCTIONS = (
    "Return only the CapabilityCheckProposal for the user's request.\n\n"
    "The request's sentences are numbered after it. For each sentence, first give its role, then quote its "
    "exact words into:\n"
    "- has: what the user has, did, or must respect (data, samples, constraints);\n"
    "- about_methods: questions about the methods themselves -- which to use, how one works, what it needs;\n"
    "- asks: each thing the user wants produced or answered about their data or biology, one item per thing.\n"
    "If one sentence asks for two things, make two asks. For each ask, also give its scale, how many omics data "
    "types it must model together, what each unit is computed from, the regulator kinds it must contain, and "
    "whether it must say activation versus repression.\n\n"
    "For each ask, delivered_by lists the PRODUCES entries below whose result gives what the quote asks for, "
    "as it is asked. An entry that gives a related result, or only an ingredient of it, does not deliver it. "
    "When no entry gives it, delivered_by is empty -- a normal answer, not a failure. not_by lists the NOT "
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


@lru_cache(maxsize=2)
def _own_llm(model: str, max_tokens: int):
    """Log 389: on the seen trap sets gpt-4o-mini declared 4/60 controls unsupported, gpt-4o 0/60.

    The model must pass the router allowlist, like every routing model.
    """
    from ..llm import build_llm, validate_router_model

    return build_llm(validate_router_model(model), 0.0, max_output_tokens=max_tokens)


def request_capability_check(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
    usage: LLMUsage,
    budget_warnings: list[str],
) -> tuple[BaseModel | None, LLMUsage, list[str]]:
    """The model's proposal for the request, or None when nothing read it.

    Called right after routing, before the advisory reads (Log 387 dev round 3: a
    routing-heavy turn spent 25k of its 30k tokens and the check was the call the
    budget blocked). Verification waits for the study-purpose claims
    (`interpretation.capability_check.build_capability_check`).
    """
    # The study-purpose call's model, or the check's own (OPENROUTER_CAPABILITY_MODEL, Log 389).
    llm = getattr(context, "study_purpose_llm", None)
    model = getattr(context, "semantic_model_name", None)
    if llm is None:
        return None, usage, budget_warnings
    own = os.environ.get("OPENROUTER_CAPABILITY_MODEL")
    if own and own != model:
        # Reasoning models spend output tokens before the answer (nemotron ~1.7k a call on the
        # seen sets), so the check's own model gets its own cap rather than the router's 1,200.
        model, llm = own, _own_llm(own, int(os.environ.get("OPENROUTER_CAPABILITY_MAX_TOKENS", "6000")))
    messages, count = build_capability_check_messages(user_task)
    schema = proposal_model(count)
    input_text = _serialized_structured_input(messages, schema)
    call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
    budget, budget_warnings = preflight_budget(
        context, call_state, role="capability_check",
        model=model, input_text=input_text,
        reserved_output_tokens=context.router_max_tokens, allow_reserve=False,
    )
    if budget.status == "blocked":
        usage.budget_exhausted = True
        return None, usage, budget_warnings
    started_ns = time.monotonic_ns()
    raw = payload = proposal = None
    output_text, call_status = "", "failed"
    try:
        adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
        payload, raw = semantic_payload(adapter.invoke(messages))
        if isinstance(payload, BaseModel):
            payload = payload.model_dump()
        proposal = schema.model_validate(payload)
        output_text = proposal.model_dump_json()
        call_status = "success"
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
        usage, role="capability_check", model=model,
        response=raw, input_text=input_text, output_text=output_text,
        budget_tokens=context.task_token_budget,
        duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
        status=call_status, price_catalog=context.price_catalog,
    )
    return proposal, usage, budget_warnings
