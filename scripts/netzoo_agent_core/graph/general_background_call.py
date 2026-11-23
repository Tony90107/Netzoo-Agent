"""couldn't-match-2026-11-18: the general-background call beside a refusal with no verified reason.

One structured call on the routing model, only when `general_background.wanted` holds and NETZOO_GENERAL_BACKGROUND
is on. It never changes the call: the paragraph is kept in `core.evidence["general_background"]` and the DECLINE
view prints it under its label. No model, no budget or a failed call leaves the reply as it was, and says so.
"""

from __future__ import annotations

import time

from pydantic import BaseModel

from ..contracts import HumanMessage, SystemMessage
from ..interpretation.general_background import GeneralBackground, background_mode, kept_sentences, \
    unmatched_quotes, wanted
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..llm import append_llm_usage
from .capability_check_call import spent, with_reading_allowance
from .context import preflight_budget, record_event
from .fact_check_call import fact_model
from .required_check_budget import check_output_reserve

__all__ = ["apply_general_background", "background_messages"]

INSTRUCTIONS = (
    "A user asked a network-analysis tool for something its fixed set of workflows was not matched to; that decision "
    "is already made and is not yours. Give the user short general background on what they asked, from general "
    "scientific knowledge, in English. Fill the schema: `answerable` and `background`."
)


def background_messages(task: str, quotes: list[str]) -> tuple[list, str]:
    asked = "\n".join(f"- {quote}" for quote in quotes) or "(the whole request)"
    user = f"The user's request:\n{task.strip()}\n\nThe part no workflow was matched to:\n{asked}"
    return [SystemMessage(content=INSTRUCTIONS), HumanMessage(content=user)], f"{INSTRUCTIONS}\n\n{user}"


def _invoke(llm, messages):
    raw = None
    try:
        adapter = llm.with_structured_output(GeneralBackground, method="function_calling", include_raw=True,
                                             strict=True)
        response = adapter.invoke(messages)
        raw = response.get("raw") if isinstance(response, dict) else None
        payload, raw = semantic_payload(response)
        if isinstance(payload, BaseModel):
            payload = payload.model_dump()
        parsed = GeneralBackground.model_validate(payload)
        return parsed, raw, parsed.model_dump_json(), None
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        return None, raw, "", error


def apply_general_background(context, state, decision, core, user_task: str, usage, budget_warnings):
    """(core, usage, budget_warnings): the core with its background paragraph recorded, when one is wanted."""
    if background_mode() != "on" or not wanted(core):
        return core, usage, budget_warnings
    model, llm = fact_model(context)
    if llm is None:
        return core, usage, budget_warnings
    quotes = unmatched_quotes(core, getattr(decision, "capability_check", None))
    messages, input_text = background_messages(user_task, quotes)
    record = {"model": model or "", "quotes": quotes}
    reading = with_reading_allowance(context, usage)
    call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
    budget, budget_warnings = preflight_budget(
        reading, call_state, role="general_background", model=model, input_text=input_text,
        reserved_output_tokens=check_output_reserve(context, llm), allow_reserve=False)
    if spent(usage) or budget.status == "blocked":
        record_event(context, state, "core.general_background", "classify", {**record, "status": "blocked"})
        return core, usage, budget_warnings
    started_ns = time.monotonic_ns()
    parsed, raw, output_text, error = _invoke(llm, messages)
    usage = append_llm_usage(
        usage, role="general_background", model=model, response=raw, input_text=input_text, output_text=output_text,
        budget_tokens=reading.task_token_budget, duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
        status="success" if error is None else "failed", price_catalog=context.price_catalog)
    if parsed is None:
        record_event(context, state, "core.general_background", "classify",
                     {**record, "status": f"failed:{type(error).__name__}"})
        return core, usage, budget_warnings
    text, dropped = kept_sentences(parsed.background) if parsed.answerable else ("", [])
    record = {**record, "status": "kept" if text else "none", "answerable": parsed.answerable,
              "background": text, "dropped": dropped, "raw": parsed.background}
    record_event(context, state, "core.general_background", "classify", record)
    if not text:
        return core, usage, budget_warnings
    evidence = {**core.evidence, "general_background": {"text": text, "model": model or ""}}
    return core.model_copy(update={"evidence": evidence}), usage, budget_warnings
