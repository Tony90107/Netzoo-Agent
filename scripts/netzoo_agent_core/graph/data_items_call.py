"""ROUND-27 C1: the data-item read (`interpretation.data_items`), once after a DO, and code's DO -> ASK judgment.
Behind NETZOO_DATA_ITEMS=1 (off by default); no model, no budget or a failed call leaves the call as it was.
"""

from __future__ import annotations

import os
import time

from ..contracts import HumanMessage, SystemMessage
from ..interpretation.data_items import DATA_ITEMS_INSTRUCTIONS, DataItemsRead, asked_core, data_item_findings
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..llm import append_llm_usage
from ..method_names import registered_workflows
from .capability_check_call import _own_llm, with_reading_allowance
from .context import preflight_budget, record_event
from .required_check_budget import retryable_check_error
from .structured_calls import _serialized_structured_input

__all__ = ["DATA_ITEMS_MAX_TOKENS", "apply_data_items", "data_items_input", "data_items_on", "invoke_data_items"]

DATA_ITEMS_MAX_TOKENS = 1200


def data_items_on() -> bool:
    return os.environ.get("NETZOO_DATA_ITEMS", "0") == "1"


def data_items_input(task: str) -> tuple[list, str]:
    messages = [SystemMessage(content=DATA_ITEMS_INSTRUCTIONS), HumanMessage(content=f"Request:\n{task}")]
    return messages, _serialized_structured_input(messages, DataItemsRead)


def invoke_data_items(llm, task: str):
    """One structured call; (read or None, raw, input text, output text, error)."""
    messages, input_text = data_items_input(task)
    raw = None
    try:
        adapter = llm.with_structured_output(DataItemsRead, method="function_calling", include_raw=True, strict=True)
        payload, raw = semantic_payload(adapter.invoke(messages))
        read = DataItemsRead.model_validate(payload.model_dump() if hasattr(payload, "model_dump") else payload)
        return read, raw, input_text, read.model_dump_json(), None
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        return None, raw, input_text, "", error


def apply_data_items(context, state, core, user_task: str, usage, warnings):
    """(core, usage, warnings): a DO whose credited workflows the user's stated data cannot feed becomes an ASK."""
    if core.kind != "DO" or not data_items_on():
        return core, usage, warnings
    workflows = [name for name in core.workflows if name in registered_workflows()]
    model = os.environ.get("OPENROUTER_CAPABILITY_MODEL") or getattr(context, "semantic_model_name", None)
    llm = _own_llm(model, DATA_ITEMS_MAX_TOKENS) if os.environ.get("OPENROUTER_CAPABILITY_MODEL") else getattr(
        context, "study_purpose_llm", None)
    if not workflows or llm is None or usage.budget_exhausted:
        record_event(context, state, "core.data_items", "classify", {
            "status": "not_run:" + ("no_workflows" if not workflows else "no_model" if llm is None else "budget"),
            "workflows": workflows})
        return core, usage, warnings
    allowance = with_reading_allowance(context, usage)
    _, input_text = data_items_input(user_task)
    status, read = "failed", None
    for _attempt in (1, 2):
        call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=warnings)
        budget, warnings = preflight_budget(allowance, call_state, role="data_items", model=model,
                                            input_text=input_text, reserved_output_tokens=DATA_ITEMS_MAX_TOKENS,
                                            allow_reserve=False)
        if usage.budget_exhausted or budget.status == "blocked":
            status = "blocked"
            break
        started_ns = time.monotonic_ns()
        read, raw, input_text, output_text, error = invoke_data_items(llm, user_task)
        usage = append_llm_usage(
            usage, role="data_items", model=model, response=raw, input_text=input_text, output_text=output_text,
            budget_tokens=allowance.task_token_budget,
            duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
            status="success" if error is None else "failed", price_catalog=context.price_catalog)
        if read is not None:
            status = "read"
            break
        if not retryable_check_error(error):
            break
    findings = data_item_findings(user_task, read, workflows) if read is not None else []
    asked = asked_core(core, findings)
    record_event(context, state, "core.data_items", "classify", {
        "status": status, "model": model or "", "workflows": workflows,
        "read": read.model_dump() if read is not None else None,
        "findings": [f.__dict__ for f in findings], "kind_before": core.kind, "kind_after": asked.kind})
    return asked, usage, warnings
