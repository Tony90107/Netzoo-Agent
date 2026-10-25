"""ROUND-26 2a: the settings links read (`interpretation.settings_links`), once per request with candidate workflows,
before the capability check is built. Behind NETZOO_SETTINGS_LINKS=1 (off by default); no model, no budget or a failed
call leaves the reading as it was.
"""

from __future__ import annotations

import os
import time

from ..contracts import HumanMessage, SystemMessage
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..interpretation.settings_links import (
    LINKS_INSTRUCTIONS, guarded_links, link_workflows, links_model, links_text, merged_reading, reading_doubts,
    verified_links, without_emptier,
)
from ..llm import append_llm_usage
from .capability_check_call import with_reading_allowance
from .context import preflight_budget, record_event
from .goal_read_call import _goal_model
from .required_check_budget import retryable_check_error
from .structured_calls import _serialized_structured_input

__all__ = ["apply_settings_links", "invoke_settings_links", "settings_links_input", "settings_links_on"]


def settings_links_on() -> bool:
    return os.environ.get("NETZOO_SETTINGS_LINKS", "0") == "1"


def settings_links_input(task: str, workflows: list[str]) -> tuple[list, str]:
    messages = [SystemMessage(content=LINKS_INSTRUCTIONS),
                HumanMessage(content=f"Workflows and their settings:\n{links_text(workflows)}\n\nRequest:\n{task}")]
    return messages, _serialized_structured_input(messages, links_model(tuple(workflows)))


def invoke_settings_links(llm, task: str, workflows: list[str]):
    """One structured call; (read or None, raw, input text, output text, error)."""
    schema = links_model(tuple(workflows))
    messages, input_text = settings_links_input(task, workflows)
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


def apply_settings_links(context, state, user_task: str, proposal, usage, budget_warnings, build):
    """(proposal, links, empty, held, usage, warnings): the reading with its credited workflows' settings linked.

    `links` and `empty` are what `merged_reading` takes (the re-read is merged with them too, without adding); `held`
    are the links not merged (ROUND-27 B1: unsure, or adding a limit), asked to confirm on a DO. `build(reading_dict)`
    makes the capability check, code only (B1 change 5)."""
    unchanged = (proposal, [], set(), [], usage, budget_warnings)
    if not settings_links_on() or proposal is None:
        return unchanged
    reading = proposal.model_dump()
    workflows = link_workflows(user_task, reading)
    model, llm = _goal_model(context)
    if not workflows or llm is None:
        return unchanged
    allowance = with_reading_allowance(context, usage)
    _, input_text = settings_links_input(user_task, workflows)
    status, read = "failed", None
    for attempt in (1, 2):
        call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
        budget, budget_warnings = preflight_budget(
            allowance, call_state, role="settings_links", model=model, input_text=input_text,
            reserved_output_tokens=800, allow_reserve=False)
        if usage.budget_exhausted or budget.status == "blocked":
            status = "blocked"
            break
        started_ns = time.monotonic_ns()
        read, raw, input_text, output_text, error = invoke_settings_links(llm, user_task, workflows)
        usage = append_llm_usage(
            usage, role="settings_links", model=model, response=raw, input_text=input_text, output_text=output_text,
            budget_tokens=allowance.task_token_budget,
            duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
            status="success" if error is None else "failed", price_catalog=context.price_catalog)
        if read is not None:
            status = "read"
            break
        if not retryable_check_error(error):
            break
    links, empty = (verified_links(user_task, workflows, read, reading_doubts(user_task, reading)) if read is not None
                    else ([], set()))
    links = without_emptier(user_task, reading, links)
    kept, held = guarded_links(user_task, reading, links, empty, build) if links else ([], [])
    record_event(context, state, "core.settings_links", "classify", {
        "status": status, "model": model or "", "workflows": workflows,
        "read": read.model_dump() if read is not None else None,
        "links": [{key: (list(value) if key == "span" else value) for key, value in link.items()} for link in kept],
        "held": [{key: (list(value) if key == "span" else value) for key, value in link.items()} for link in held]})
    clean = [{key: value for key, value in link.items() if key != "span"} for link in held]
    if not kept:
        return proposal, [], set(), clean, usage, budget_warnings
    merged = type(proposal).model_validate(merged_reading(user_task, reading, kept, empty))
    return merged, kept, empty, clean, usage, budget_warnings
