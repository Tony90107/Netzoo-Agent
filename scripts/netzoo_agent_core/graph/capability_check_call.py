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
from dataclasses import is_dataclass, replace
from types import SimpleNamespace
from functools import lru_cache

from pydantic import BaseModel

from ..capability_sheet import sheet_entries
from ..contracts import AgentState, HumanMessage, LLMUsage, SystemMessage
from ..contracts.capability_check import MAX_SENTENCES, proposal_model, second_opinion_model
from ..interpretation.capability_check import request_sentences
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..llm import append_llm_usage
from ..settings import ROUTER_CONTEXT_MAX_CHARS
from .context import _GraphContext, preflight_budget, record_event
from .structured_calls import _serialized_structured_input, _validation_issue_types

__all__ = ["capability_check_system", "build_capability_check_messages", "request_capability_check",
           "with_reading_allowance", "has_check_model", "request_second_opinion"]

_INSTRUCTIONS = (
    "Return only the CapabilityCheckProposal for the user's request.\n\n"
    "The request's sentences are numbered after it. For each sentence, first give its role, then quote its "
    "exact words into:\n"
    "- has: what the user has, did, or must respect (data, samples, constraints);\n"
    "- about_methods: questions about how a method works or what it needs, naming no result;\n"
    "- asks: each result the user wants produced, or asks whether or which method produces, about their data "
    "or biology, one item per result.\n"
    "If one sentence asks for two results, make two asks. For each ask, also give how it was asked (a request "
    "or a question), its scale, how many omics data types it must model together, what each unit is computed "
    "from, the regulator kinds it must contain, whether it must say activation versus repression, and its form "
    "(group membership, time model, use of space).\n\n"
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


_SECOND_OPINION = (
    "Return only the SecondOpinion structure. Each numbered pair gives words from a user's request and the "
    "results one registered workflow produces. Answer all only if those results, together, give what the words "
    "ask for, as they ask it -- not a related result, and not only an ingredient of it; part if the words ask "
    "for more than one result and the workflow's results give some of them; none otherwise. The user's own data "
    "and situation are listed first; read the request words in that light."
)


def _check_model(context):
    """The check's model and LLM: its own (OPENROUTER_CAPABILITY_MODEL, Log 389) or the study-purpose call's."""
    llm = getattr(context, "study_purpose_llm", None)
    model = getattr(context, "semantic_model_name", None)
    own = os.environ.get("OPENROUTER_CAPABILITY_MODEL")
    if llm is not None and own and own != model:
        # Reasoning models spend output tokens before the answer (nemotron ~1.7k a call on the
        # seen sets), so the check's own model gets its own cap rather than the router's 1,200.
        model, llm = own, _own_llm(own, int(os.environ.get("OPENROUTER_CAPABILITY_MAX_TOKENS", "6000")))
    return model, llm


def has_check_model(context) -> bool:
    """Whether any model is configured to read the check (none in tests and the routing harness)."""
    return _check_model(context)[1] is not None


def request_second_opinion(context, state, pairs: list[tuple[str, str, str]], usage, budget_warnings,
                           situation: tuple[str, ...] = ()):
    """Log 390: yes/no per (request words, workflow, its results), or None when nothing answered.

    Asked only when a full gap would clear an exact routing match: on heldouts 1-3 every false
    gap (HC7, JC6, KC8) had routing exact and an empty `delivered_by`.
    """
    model, llm = _check_model(context)
    if llm is None or not pairs:
        return None, usage, budget_warnings
    answers, usage, budget_warnings = _second_opinion_call(context, state, model, llm, pairs, usage, budget_warnings,
                                                           situation)
    fallback = getattr(context, "study_purpose_llm", None)
    if answers is None and fallback is not None and llm is not fallback and not usage.budget_exhausted:
        # Log 401: a failed own model is followed by the semantic model, as for the check itself.
        answers, usage, budget_warnings = _second_opinion_call(
            context, state, getattr(context, "semantic_model_name", None), fallback, pairs, usage, budget_warnings,
            situation)
    return answers, usage, budget_warnings


def _second_opinion_call(context, state, model, llm, pairs, usage, budget_warnings, situation):
    schema = second_opinion_model(len(pairs))
    listed = "\n".join(f'{index}. Request words: "{quote}" | {workflow} produces: {result}'
                        for index, (quote, workflow, result) in enumerate(pairs, 1))
    # Log 396: without the user's own data beside them, "for a rare tissue" read as a demand on the
    # method and "infer a network" was refused 2/2; with it, 2/2 accepted and two near misses kept.
    shown = f"The user has: {'; '.join(situation)}.\n{listed}" if situation else listed
    messages = [SystemMessage(content=_SECOND_OPINION), HumanMessage(content=shown)]
    input_text = _serialized_structured_input(messages, schema)
    call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
    budget, budget_warnings = preflight_budget(
        with_reading_allowance(context, usage), call_state, role="capability_second_opinion", model=model,
        input_text=input_text, reserved_output_tokens=context.router_max_tokens, allow_reserve=False,
    )
    if budget.status == "blocked":
        usage.budget_exhausted = True
        return None, usage, budget_warnings
    started_ns = time.monotonic_ns()
    raw = payload = answers = None
    output_text, call_status = "", "failed"
    try:
        adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
        payload, raw = semantic_payload(adapter.invoke(messages))
        if isinstance(payload, BaseModel):
            payload = payload.model_dump()
        parsed = schema.model_validate(payload)
        output_text = parsed.model_dump_json()
        answers = [getattr(parsed, f"a{index}") for index in range(1, len(pairs) + 1)]
        call_status = "success"
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        record_event(context, state, "routing.capability_second_opinion_failed", "classify", {
            "error_type": type(error).__name__, "error_message": str(error)[:2000], "provider_payload": payload,
        })
    usage = append_llm_usage(
        usage, role="capability_second_opinion", model=model,
        response=raw, input_text=input_text, output_text=output_text,
        budget_tokens=context.task_token_budget,
        duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
        status=call_status, price_catalog=context.price_catalog,
    )
    return answers, usage, budget_warnings


# Log 394: the safety check gets its own allowance on top of the turn's token budget, because
# routing-heavy turns (retries, sibling repairs, a review) spent 26.6k of 30k tokens before it and
# the budget skipped exactly the check (heldout3 KU9 x2: both answered with a workflow menu).
CHECK_EXTRA_TOKENS = 8_000


def with_reading_allowance(context, usage=None):
    """The context with the check's allowance added to the turn budget (Logs 394, 403).

    The allowance tops up a turn whose routing left too little; it never reopens a
    turn already marked spent (`usage.budget_exhausted`), which keeps its own budget.

    Log 403: the calls that read the request after routing -- the check, its second
    opinion, the study purpose and the data facts -- share it. Traces of h8-h9, o10 and
    f10: with the turn budget alone the data-facts call was blocked in 2-17% of turns and
    the reply then asked for a motif prior and PPI the request had named, and 11 second
    opinions were blocked, leaving their gaps unasked.
    """
    if usage is not None and usage.budget_exhausted:
        return context
    extra = int(os.environ.get("OPENROUTER_CAPABILITY_EXTRA_TOKENS", CHECK_EXTRA_TOKENS))
    budget = context.task_token_budget + extra
    return (replace(context, task_token_budget=budget) if is_dataclass(context)
            else SimpleNamespace(**{**vars(context), "task_token_budget": budget}))


def request_capability_check(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
    usage: LLMUsage,
    budget_warnings: list[str],
) -> tuple[BaseModel | None, LLMUsage, list[str], str]:
    """The model's proposal for the request, its usage, and why it is missing.

    The status is "ok", "fallback" (the semantic model answered after the own model failed,
    Log 401), "no_model" (nothing is configured to read it: tests, the harness),
    "blocked" (even the extra allowance is spent) or "failed". Called right after routing,
    before the advisory reads; verification waits for the study-purpose claims
    (`interpretation.capability_check.build_capability_check`). A reply the model sent
    that could not be decoded or validated is asked once more (TEST_PROMPTS r9 test9);
    a timeout is not, since the free model already took a minute. When the check has its
    own model, the second attempt is the study-purpose model's, after any failure (Log 401,
    TEST_PROMPTS r15 test9: nemotron answered nothing twice, about a minute each).
    """
    model, llm = _check_model(context)
    if llm is None:
        return None, usage, budget_warnings, "no_model"
    fallback_llm = getattr(context, "study_purpose_llm", None)
    own = llm is not fallback_llm
    if usage.budget_exhausted:
        # The allowance tops up a turn whose routing left too little; it never reopens a spent turn.
        return None, usage, budget_warnings, "blocked"
    messages, count = build_capability_check_messages(user_task)
    schema = proposal_model(count)
    input_text = _serialized_structured_input(messages, schema)
    budget_context = with_reading_allowance(context)
    for attempt in (1, 2):
        call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
        budget, budget_warnings = preflight_budget(
            budget_context, call_state, role="capability_check",
            model=model, input_text=input_text,
            reserved_output_tokens=context.router_max_tokens, allow_reserve=False,
        )
        if budget.status == "blocked":
            return None, usage, budget_warnings, "blocked"
        started_ns = time.monotonic_ns()
        raw = payload = proposal = None
        output_text, call_status, retry = "", "failed", False
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
            retry = isinstance(error, ValueError)  # undecodable or invalid; pydantic errors are ValueErrors
            record_event(context, state, "routing.capability_check_failed", "classify", {
                "attempt": attempt,
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
        if proposal is not None:
            return proposal, usage, budget_warnings, ("fallback" if own and llm is fallback_llm else "ok")
        fallback = getattr(context, "study_purpose_llm", None)
        if llm is not fallback and fallback is not None:
            model, llm = getattr(context, "semantic_model_name", None), fallback
        elif not retry:
            break
    return None, usage, budget_warnings, "failed"
