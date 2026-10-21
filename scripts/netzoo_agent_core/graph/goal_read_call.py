"""ROUND-21 (R21-A): the narrow goal read of a full gap no reason can be given for (`interpretation.goal_read`).

One small strict call on the capability check's own model, made only when `needs_goal_read` says so. No model, no
budget or a failed call leaves the check as it was: the turn stays the DECLINE it would have been.
"""

from __future__ import annotations

import os
import time

from ..contracts import HumanMessage, SystemMessage
from ..contracts.capability_check import GoalRead
from ..interpretation.goal_read import GOAL_READ_INSTRUCTIONS, needs_goal_read, with_goal_read
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..llm import append_llm_usage
from .capability_check_call import _own_llm, with_reading_allowance
from .context import preflight_budget, record_event
from .required_check_budget import retryable_check_error
from .structured_calls import _serialized_structured_input

__all__ = ["GOAL_READ_MAX_TOKENS", "apply_goal_read", "goal_read_input", "invoke_goal_read"]

GOAL_READ_MAX_TOKENS = 400
"""The answer is one quote and one choice; a small cap keeps the call inside a turn the check nearly spent."""


def goal_read_input(task: str) -> tuple[list, str]:
    messages = [SystemMessage(content=GOAL_READ_INSTRUCTIONS), HumanMessage(content=f"Request:\n{task}")]
    return messages, _serialized_structured_input(messages, GoalRead)


def _goal_model(context):
    """The capability check's own model (OPENROUTER_CAPABILITY_MODEL), else the study-purpose call's."""
    own = os.environ.get("OPENROUTER_CAPABILITY_MODEL")
    if own:
        return own, _own_llm(own, GOAL_READ_MAX_TOKENS)
    return getattr(context, "semantic_model_name", None), getattr(context, "study_purpose_llm", None)


def invoke_goal_read(llm, task: str):
    """One structured call; (read or None, raw, input text, output text, error)."""
    messages, input_text = goal_read_input(task)
    raw = None
    try:
        adapter = llm.with_structured_output(GoalRead, method="function_calling", include_raw=True, strict=True)
        payload, raw = semantic_payload(adapter.invoke(messages))
        read = GoalRead.model_validate(payload.model_dump() if hasattr(payload, "model_dump") else payload)
        return read, raw, input_text, read.model_dump_json(), None
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        return None, raw, input_text, "", error


def apply_goal_read(context, state, user_task: str, decision, check, usage, budget_warnings):
    """(check, usage, warnings): the check with the open goal's words when the read finds no result named."""
    if not needs_goal_read(check, decision, user_task):
        return check, usage, budget_warnings
    model, llm = _goal_model(context)
    if llm is None:
        return check, usage, budget_warnings
    _, input_text = goal_read_input(user_task)
    reading = with_reading_allowance(context, usage)
    status, read = "failed", None
    for attempt in (1, 2):
        call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
        budget, budget_warnings = preflight_budget(
            reading, call_state, role="goal_read", model=model, input_text=input_text,
            reserved_output_tokens=GOAL_READ_MAX_TOKENS, allow_reserve=False)
        if usage.budget_exhausted or budget.status == "blocked":
            status = "blocked"
            break
        started_ns = time.monotonic_ns()
        read, raw, input_text, output_text, error = invoke_goal_read(llm, user_task)
        usage = append_llm_usage(
            usage, role="goal_read", model=model, response=raw, input_text=input_text, output_text=output_text,
            budget_tokens=reading.task_token_budget, duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
            status="success" if error is None else "failed", price_catalog=context.price_catalog)
        if read is not None:
            status = "read"
            break
        if not retryable_check_error(error):
            break
    after = with_goal_read(check, user_task, read)
    record_event(context, state, "core.goal_read", "classify", {
        "status": status, "model": model or "", "read": read.model_dump() if read is not None else None,
        "open_goal_quote": after.open_goal_quote})
    return after, usage, budget_warnings
