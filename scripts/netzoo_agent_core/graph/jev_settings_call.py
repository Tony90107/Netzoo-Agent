"""The closed settings read's call (docs/research-log/jev-settings-2026-10-31/ROUND.md;
`interpretation.closed_settings`). Off by default: NETZOO_JEV_SETTINGS=shadow records what it would change, =on
applies it.

Jev answers one set/not_stated question per registry control and, for each it says is set, picks the request sentence
that says so; the capability check's own model then gives only the values (one strict call). The research shapes are
kept as measured (candidate-table-2026-10-30/settings_read.py): option keys o1.., question keys with `:` as `_`,
batches of 12. NETZOO_JEV_SETTINGS_CACHE (a JSON file) memoises reads for offline replay. Any failure leaves the check
as it was.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from pathlib import Path

from pydantic import BaseModel, ConfigDict, create_model

from ..contracts import HumanMessage, SystemMessage
from ..interpretation.closed_settings import (
    QUOTE_INSTRUCTIONS, SET_CRITERIA, VALUE_SYSTEM, VALUE_TASK, controls, questions, strong_reads, with_closed_settings,
)
from ..interpretation.closed_settings_retype import retyped
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..jev_client import decide
from ..llm import append_llm_usage
from .capability_check_call import with_reading_allowance
from .context import preflight_budget, record_event
from .goal_read_call import _goal_model
from .jev_guard_call import request_sentences
from .structured_calls import _serialized_structured_input

__all__ = ["apply_jev_settings", "jev_settings_mode"]

TIMEOUT = 30
BATCH = 12
_LOCK = threading.Lock()
_MEMO: dict[str, dict] = {}


def jev_settings_mode() -> str:
    mode = os.environ.get("NETZOO_JEV_SETTINGS", "off").strip().lower()
    return mode if mode in ("shadow", "on") else "off"


def _cache_path() -> Path | None:
    path = os.environ.get("NETZOO_JEV_SETTINGS_CACHE", "").strip()
    return Path(path) if path else None


def _numbered(texts: dict[str, str]) -> tuple[dict[str, str], dict[str, str]]:
    keys = {f"o{i}": key for i, key in enumerate(texts, 1)}
    return {short: texts[key] for short, key in keys.items()}, keys


def _ask(task: str, asked: dict[str, tuple[str, dict[str, str]]]) -> dict[str, dict]:
    """Jev's answers to {name: (instructions, criteria)}, in batches; raises on any failure."""
    names, answers = list(asked), {}
    for start in range(0, len(names), BATCH):
        payload, shorts = {}, {}
        for name in names[start:start + BATCH]:
            instructions, texts = asked[name]
            criteria, shorts[name] = _numbered(texts)
            payload[re.sub(r"\W", "_", name)] = {"type": "choice", "instructions": instructions, "criteria": criteria}
        out = decide(f"User request:\n{task}", payload, timeout=TIMEOUT)
        for name in names[start:start + BATCH]:
            answer = out["answers"][re.sub(r"\W", "_", name)]
            answers[name] = {"choice": shorts[name].get(answer["choice"], answer["choice"]),
                             "confidence": answer["confidence"]}
    return answers


def _value_model(names: list[str]) -> type[BaseModel]:
    item = create_model("SettingValue", __config__=ConfigDict(extra="forbid"), value=(str, ...), words=(str, ...))
    values = create_model("SettingValues", __config__=ConfigDict(extra="forbid"), **{n: (item, ...) for n in names})
    return create_model("ClosedSettingValues", __config__=ConfigDict(extra="forbid"), values=(values, ...))


def _jev_read(task: str) -> dict:
    """{answers, picks, sentences}: memoised per process and in NETZOO_JEV_SETTINGS_CACHE. Raises on failure."""
    key = hashlib.sha256(json.dumps([task, questions()], sort_keys=True).encode()).hexdigest()[:20]
    with _LOCK:
        if key in _MEMO:
            return _MEMO[key]
        cache = _cache_path()
        stored = json.loads(cache.read_text()) if cache is not None and cache.exists() else {}
        if key in stored:
            _MEMO[key] = stored[key]
            return stored[key]
    asked = {f"setting:{name}": (instructions, SET_CRITERIA) for name, instructions in questions().items()}
    answers = _ask(task, asked)
    sentences = {f"s{i}": text for i, text in enumerate(request_sentences(task), 1)}
    picked = {f"quote:{name}": (QUOTE_INSTRUCTIONS.format(question=asked[name][0], answer=SET_CRITERIA["set"]),
                                sentences | {"none": "no sentence states it"})
              for name, answer in answers.items() if answer["choice"] == "set"} if sentences else {}
    picks = _ask(task, picked) if picked else {}
    read = {"answers": {n[8:]: a for n, a in answers.items()},
            "picks": {n[14:]: a for n, a in picks.items()}, "sentences": sentences}
    with _LOCK:
        _MEMO[key] = read
        if cache is not None:
            stored = json.loads(cache.read_text()) if cache.exists() else {}
            cache.write_text(json.dumps({**stored, key: read}, indent=1))
    return read


def _values(context, state, task: str, names: list[str], usage, budget_warnings):
    """(values, usage, warnings): the model's value and words per control; {} when there is no model or budget."""
    model, llm = _goal_model(context)
    if not names or llm is None:
        return {}, usage, budget_warnings
    listed = "\n".join(f"- {name}: {controls()[name]['description']}" for name in names)
    messages = [SystemMessage(content=VALUE_SYSTEM), HumanMessage(content=VALUE_TASK.format(prompt=task, names=listed))]
    schema = _value_model(names)
    input_text = _serialized_structured_input(messages, schema)
    reading = with_reading_allowance(context, usage)
    call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
    budget, budget_warnings = preflight_budget(reading, call_state, role="jev_settings_values", model=model,
                                               input_text=input_text, reserved_output_tokens=800, allow_reserve=False)
    if usage.budget_exhausted or budget.status == "blocked":
        return {}, usage, budget_warnings
    started_ns, raw, values, output_text, error = time.monotonic_ns(), None, {}, "", None
    try:
        adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
        payload, raw = semantic_payload(adapter.invoke(messages))
        found = schema.model_validate(payload.model_dump() if hasattr(payload, "model_dump") else payload)
        values = {name: getattr(found.values, name).model_dump() for name in names}
        output_text = found.model_dump_json()
    except BaseException as caught:  # the read keeps no value; the check stands as it was
        if _is_fatal_exception(caught):
            raise
        error = caught
    usage = append_llm_usage(
        usage, role="jev_settings_values", model=model, response=raw, input_text=input_text, output_text=output_text,
        budget_tokens=reading.task_token_budget, duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
        status="success" if error is None else "failed", price_catalog=context.price_catalog)
    return values, usage, budget_warnings


def apply_jev_settings(context, state, user_task: str, check, usage, budget_warnings):
    """(check, usage, warnings): the closed settings read applied when on, recorded when shadow, skipped when off."""
    mode = jev_settings_mode()
    retype = os.environ.get("NETZOO_SETTING_RETYPE", "off").strip().lower() == "on"  # class 4, ROUND-C4
    if (mode == "off" and not retype) or check is None or check.unconfirmed():
        return check, usage, budget_warnings
    try:
        read = _jev_read(user_task)
        if retype and (found := retyped(check, user_task, read))[1]:
            record_event(context, state, "core.setting_retype", "classify", {"changes": found[1]})
            check = found[0]
        if mode == "off":
            return check, usage, budget_warnings
        names = [name for name, answer in read["answers"].items() if name != "other" and answer["choice"] == "set"]
        values, usage, budget_warnings = _values(context, state, user_task, names, usage, budget_warnings)
        reads = strong_reads(user_task, read["answers"], read["picks"], read["sentences"], values)
        after = with_closed_settings(check, user_task, reads)
    except Exception as error:  # noqa: BLE001 -- Jev down or slow: the check stands as it was
        record_event(context, state, "core.jev_settings", "classify",
                     {"mode": mode, "error": f"{type(error).__name__}: {error}"[:200]})
        return check, usage, budget_warnings
    changed = after is not check
    record_event(context, state, "core.jev_settings", "classify", {
        "mode": mode, "reads": reads, "changed": changed, "applied": changed and mode == "on",
        "before": [[row.quote, row.status, row.limits] for row in check.requirements] if changed else [],
        "after": [[row.quote, row.status, row.limits] for row in after.requirements] if changed else []})
    return (after if mode == "on" else check), usage, budget_warnings
