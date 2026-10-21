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
from ..contracts.capability_check import (
    MAX_SENTENCES, condition_check_model, proposal_model, reread_model, schema_version, second_opinion_model,
)
from ..interpretation.capability_check import request_sentences
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..llm import append_llm_usage
from ..settings import ROUTER_CONTEXT_MAX_CHARS
from .context import _GraphContext, preflight_budget, record_event
from ..contracts.strict_schema import expanded_enum_values
from .structured_calls import _serialized_structured_input, _validation_issue_types
from .required_check_budget import check_output_reserve, retryable_check_error

__all__ = ["capability_check_system", "build_capability_check_messages", "build_reread_messages",
           "request_capability_reread", "request_capability_check", "request_condition_check",
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
    "PRODUCED entries that describe what the quote asks for.\n\n"
    "Then give the request's conditions: what any sentence says about the user's data, or about what every "
    "asked-for result must satisfy, each with the exact words that say it; not_stated, with an empty quote, "
    "when nothing says it. List every other requirement on the results under other_requirements, and under "
    "unknown_facts each property of the data or of the wanted result that the user says they do not know or have "
    "not decided, with the words that say so; under open_choices each choice among options the user names but has "
    "not made, every option as an ask of its own."
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
    "for more than one result and the workflow's results give some of them; named if the words only ask to run or "
    "use this very workflow and name no result; none otherwise. The user's own data "
    "and situation are listed first; read the request words in that light."
)


_CONDITION_CHECK = (
    "Return only the ConditionCheck structure. Each numbered pair gives a result the user asked for, a requirement "
    "the user stated about the results, and what one registered workflow produces and how. Answer violates only if "
    "that workflow's result, as described, cannot meet the requirement; satisfies if it meets it; unrelated if the "
    "requirement is not about this result; not_about_results if it only sets the result files' names, format or "
    "folder, or how the user runs the analysis."
)


_CONDITION_REDIRECT = (
    "Return only the ConditionCheck structure. Each numbered pair gives a result the user asked for, a requirement "
    "the user stated about the results, and what one registered workflow produces and how. Answer satisfies only if "
    "that workflow's results give the asked result and meet the requirement; violates if they cannot meet the "
    "requirement; unrelated if they do not give the asked result; not_about_results if the requirement only sets the "
    "result files' names, format or folder, or how the user runs the analysis."
)


def _check_model(context):
    """The check's model and LLM: its own (OPENROUTER_CAPABILITY_MODEL, Log 389) or the study-purpose call's."""
    llm = getattr(context, "study_purpose_llm", None)
    model = getattr(context, "semantic_model_name", None)
    own = os.environ.get("OPENROUTER_CAPABILITY_MODEL")
    if llm is not None and own and own != model:
        # Reasoning models spend output tokens before the answer (nemotron ~1.7k a call on the
        # seen sets), so the check's own model gets its own cap rather than the router's 1,200.
        # Log 414: on the 7 requests whose check came back undecodable, nemotron had spent the whole 6,000-token
        # cap on reasoning (finish "length"); with 9,000 all 7 decoded (largest 6,749), the live schema too.
        # Core decision follow-up (2026-10-16): the phase 1-2 fields grew the reply (median 5,580, p90 7,788, max 8,977
        # of 9,000 on the bench rounds) and 27 of 249 calls were undecodable (156-285 s each). Re-read with 16,000,
        # all 27 decoded (8 needed more than 9,000 tokens, largest 12,906); research log offline_cap_check.py.
        model, llm = own, _own_llm(own, int(os.environ.get("OPENROUTER_CAPABILITY_MAX_TOKENS", "16000")))
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


def request_condition_check(context, state, pairs: list[tuple[str, str, str, str]], usage, budget_warnings,
                            redirect: bool = False):
    """Log 414: satisfies / violates / unrelated per (asked result, stated requirement, workflow, its results).

    None when nothing answered (no model, budget, failure); the caller then changes nothing, so a failed call
    never makes a supported result unconfirmed.
    """
    from ..interpretation.expects import code_answer

    # ROUND-14: words stating the opposite of what a workflow's contract expects are judged by code, never asked.
    by_code = [code_answer(workflow, stated) for _asked, stated, workflow, _produced in pairs]
    if pairs and all(by_code):
        return by_code, usage, budget_warnings
    model, llm = _check_model(context)
    if llm is None or not pairs:
        return None, usage, budget_warnings
    asked = [pair for pair, answer in zip(pairs, by_code) if answer is None]
    answers, usage, budget_warnings = _condition_call(context, state, model, llm, asked, usage, budget_warnings,
                                                      redirect)
    if answers is None:
        return None, usage, budget_warnings
    model_answers = iter(answers)
    return [answer or next(model_answers) for answer in by_code], usage, budget_warnings


def _condition_call(context, state, model, llm, pairs, usage, budget_warnings, redirect: bool):
    schema = condition_check_model(len(pairs))
    listed = "\n".join(f'{index}. Asked result: "{asked}" | Stated requirement: "{stated}" | {workflow} produces: '
                        f"{produced}" for index, (asked, stated, workflow, produced) in enumerate(pairs, 1))
    system = _CONDITION_REDIRECT if redirect else _CONDITION_CHECK
    messages = [SystemMessage(content=system), HumanMessage(content=listed)]
    input_text = _serialized_structured_input(messages, schema)
    call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
    budget, budget_warnings = preflight_budget(
        (reading := with_reading_allowance(context, usage)), call_state, role="capability_condition_check", model=model,
        input_text=input_text, reserved_output_tokens=check_output_reserve(context, llm), allow_reserve=False,
    )
    if budget.status == "blocked":
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
        record_event(context, state, "routing.capability_condition_check_failed", "classify", {
            "error_type": type(error).__name__, "error_message": str(error)[:2000], "provider_payload": payload,
        })
    usage = append_llm_usage(
        usage, role="capability_condition_check", model=model,
        response=raw, input_text=input_text, output_text=output_text,
        budget_tokens=reading.task_token_budget,
        duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
        status=call_status, price_catalog=context.price_catalog,
    )
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
        (reading := with_reading_allowance(context, usage)), call_state, role="capability_second_opinion", model=model,
        input_text=input_text, reserved_output_tokens=check_output_reserve(context, llm), allow_reserve=False,
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
        budget_tokens=reading.task_token_budget,
        duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
        status=call_status, price_catalog=context.price_catalog,
    )
    return answers, usage, budget_warnings


_ENUM_LIMIT = 1_000
"""OpenAI strict mode: enum values per schema, references expanded (the backup model is gpt-4o-mini)."""


# Log 394: the safety check gets its own allowance on top of the turn's token budget, because
# routing-heavy turns (retries, sibling repairs, a review) spent 26.6k of 30k tokens before it and
# the budget skipped exactly the check (heldout3 KU9 x2: both answered with a workflow menu).
# M1 (2026-10-14): the method, settings and counts on every ask, and what each registered setting does, add about 2.0k
# estimated tokens to the check's input and 1.8k to its re-read (5.4k -> 7.4k for a two-sentence request); the
# allowance grows by as much, so the calls after it keep the margin they had (a24b: study purpose blocked in 20 of 157
# turns, data facts in 17).
# M2 live m2a (user decision 2026-10-14): the check now reads ~12.5k tokens and nemotron writes ~5-6k with its
# reasoning, the re-read ~9k, so the condition check was blocked in 5 of 26 turns and the study purpose in 5. The
# reading calls are mostly the free check model's; the allowance grows to 30k, the turn budget stays 30k.
CHECK_EXTRA_TOKENS = 30_000


def with_reading_allowance(context, usage=None):
    """The context with the check's allowance added to the turn budget (Logs 394, 403).

    The allowance tops up a turn whose routing left too little; it never reopens a
    turn already marked spent (`usage.budget_exhausted`), which keeps its own budget.

    Log 403: the calls that read the request after routing -- the check, its second
    opinion, the study purpose and the data facts -- share it. Traces of h8-h9, o10 and
    f10: with the turn budget alone the data-facts call was blocked in 2-17% of turns and
    the reply then asked for a motif prior and PPI the request had named, and 11 second
    opinions were blocked, leaving their gaps unasked.

    M1 (2026-10-14): each of these calls records its usage against the budget it was given, the allowance included.
    Recorded against the turn budget alone, the check's own use of its allowance marked the turn spent, and the study
    purpose and data facts after it lost the allowance they share (the larger M1 check made that more frequent).
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
    a temporary transport/provider failure is also eligible for this single retry. When the check has its
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
    version = schema_version()  # ROUND-04: reading shape 1 or 2 (NETZOO_CHECK_SCHEMA)
    schema = proposal_model(count, version=version)
    input_text = _serialized_structured_input(messages, schema)
    budget_context = reading = with_reading_allowance(context)
    for attempt in (1, 2):
        if llm is fallback_llm and expanded_enum_values(schema.model_json_schema()) > _ENUM_LIMIT:
            schema = proposal_model(count, compact=True, version=version)
        input_text = _serialized_structured_input(messages, schema)
        if usage.budget_exhausted:
            return None, usage, budget_warnings, "blocked"
        call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
        budget, budget_warnings = preflight_budget(
            budget_context, call_state, role="capability_check",
            model=model, input_text=input_text,
            reserved_output_tokens=check_output_reserve(context, llm), allow_reserve=False,
        )
        if budget.status == "blocked":
            return None, usage, budget_warnings, "blocked"
        started_ns = time.monotonic_ns()
        raw = payload = proposal = None
        output_text, call_status, retry = "", "failed", False
        try:
            adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
            response = adapter.invoke(messages)
            raw = response.get("raw") if isinstance(response, dict) else None
            payload, raw = semantic_payload(response)
            if isinstance(payload, BaseModel):
                payload = payload.model_dump()
            proposal = schema.model_validate(payload)
            output_text = proposal.model_dump_json()
            call_status = "success"
        except BaseException as error:
            if _is_fatal_exception(error):
                raise
            retry = retryable_check_error(error)
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
            budget_tokens=reading.task_token_budget,
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


def build_reread_messages(user_task: str, passages: list[str]) -> list:
    """The whole request for context, then only the passages to read, numbered as the schema's fields."""
    task = user_task[-ROUTER_CONTEXT_MAX_CHARS:]
    numbered = "\n".join(f"{index}. {text}" for index, text in enumerate(passages[:MAX_SENTENCES], 1))
    return [SystemMessage(content=capability_check_system()),
            HumanMessage(content=f"Request:\n{task}\n\nPassages to read:\n{numbered}")]


def request_capability_reread(context, state, user_task: str, passages: list[str], usage, budget_warnings):
    """Log 406: the check's own model reads the passages it left unread once more, asks only.

    Returns (re-read or None, usage, warnings). Only the check's own model is asked: the
    backup reading is never acted on (Log 401), and a failure leaves the first reading as it was.
    """
    model, llm = _check_model(context)
    if llm is None or not passages or usage.budget_exhausted:
        return None, usage, budget_warnings
    messages = build_reread_messages(user_task, passages)
    schema = reread_model(min(len(passages), MAX_SENTENCES), version=schema_version())
    input_text = _serialized_structured_input(messages, schema)
    call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
    budget, budget_warnings = preflight_budget(
        (reading := with_reading_allowance(context, usage)), call_state, role="capability_reread", model=model,
        input_text=input_text, reserved_output_tokens=check_output_reserve(context, llm), allow_reserve=False,
    )
    if budget.status == "blocked":
        return None, usage, budget_warnings
    started_ns = time.monotonic_ns()
    raw = payload = reread = None
    output_text, call_status = "", "failed"
    try:
        adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
        payload, raw = semantic_payload(adapter.invoke(messages))
        if isinstance(payload, BaseModel):
            payload = payload.model_dump()
        reread = schema.model_validate(payload)
        output_text = reread.model_dump_json()
        call_status = "success"
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        record_event(context, state, "routing.capability_reread_failed", "classify", {
            "error_type": type(error).__name__, "error_message": str(error)[:2000], "provider_payload": payload,
        })
    usage = append_llm_usage(
        usage, role="capability_reread", model=model,
        response=raw, input_text=input_text, output_text=output_text,
        budget_tokens=reading.task_token_budget,
        duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
        status=call_status, price_catalog=context.price_catalog,
    )
    return reread, usage, budget_warnings
