"""ROUND-22 (R22-B): the narrow settings read of a result whose words hold numbers nothing read
(`interpretation.settings_read`). One small strict call per such result, on the capability check's own model; no
model, no budget or a failed call leaves the check as it was.
"""

from __future__ import annotations

import time

from ..contracts import HumanMessage, SystemMessage
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..interpretation.settings_read import (
    SETTINGS_READ_INSTRUCTIONS, numeric_controls, settings_read_model, settings_read_triggers, with_settings_read,
)
from ..llm import append_llm_usage
from .capability_check_call import with_reading_allowance
from .context import preflight_budget, record_event
from .goal_read_call import _goal_model
from .required_check_budget import retryable_check_error
from .structured_calls import _serialized_structured_input

__all__ = ["MAX_SETTINGS_READS", "apply_settings_reads", "invoke_settings_read", "settings_read_input"]

MAX_SETTINGS_READS = 2


def settings_read_input(task: str, workflow: str) -> tuple[list, str]:
    settings = "\n".join(f"- {name}: {description}" for name, description in numeric_controls(workflow))
    messages = [SystemMessage(content=SETTINGS_READ_INSTRUCTIONS),
                HumanMessage(content=f"Workflow: {workflow}\nNumeric settings:\n{settings}\n\nRequest:\n{task}")]
    return messages, _serialized_structured_input(messages, settings_read_model(workflow))


def invoke_settings_read(llm, task: str, workflow: str):
    """One structured call; (read or None, raw, input text, output text, error)."""
    schema = settings_read_model(workflow)
    messages, input_text = settings_read_input(task, workflow)
    raw = None
    try:
        adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
        payload, raw = semantic_payload(adapter.invoke(messages))
        read = schema.model_validate(payload.model_dump() if hasattr(payload, "model_dump") else payload)
        return read, raw, input_text, read.model_dump_json(), None
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        return None, raw, input_text, "", error


def apply_settings_reads(context, state, user_task: str, check, usage, budget_warnings):
    """(check, usage, warnings): each triggered result read once, its found settings judged by the workflow's rules."""
    triggers = settings_read_triggers(check, user_task)[:MAX_SETTINGS_READS]
    if not triggers:
        return check, usage, budget_warnings
    model, llm = _goal_model(context)
    if llm is None:
        return check, usage, budget_warnings
    reading = with_reading_allowance(context, usage)
    for index, workflow in triggers:
        _, input_text = settings_read_input(user_task, workflow)
        status, read = "failed", None
        for attempt in (1, 2):
            call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
            budget, budget_warnings = preflight_budget(
                reading, call_state, role="settings_read", model=model, input_text=input_text,
                reserved_output_tokens=400, allow_reserve=False)
            if usage.budget_exhausted or budget.status == "blocked":
                status = "blocked"
                break
            started_ns = time.monotonic_ns()
            read, raw, input_text, output_text, error = invoke_settings_read(llm, user_task, workflow)
            usage = append_llm_usage(
                usage, role="settings_read", model=model, response=raw, input_text=input_text,
                output_text=output_text, budget_tokens=reading.task_token_budget,
                duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
                status="success" if error is None else "failed", price_catalog=context.price_catalog)
            if read is not None:
                status = "read"
                break
            if not retryable_check_error(error):
                break
        quote = check.requirements[index].quote
        check = with_settings_read(check, user_task, index, workflow, read)
        record_event(context, state, "core.settings_read", "classify", {
            "status": status, "model": model or "", "workflow": workflow, "quote": quote,
            "read": read.model_dump() if read is not None else None,
            "settings": check.requirements[index].method.get("settings", [])})
    return check, usage, budget_warnings
