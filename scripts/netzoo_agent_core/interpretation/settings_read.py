"""ROUND-22 (R22-B, collab/ROUND-22-PLAN.md): the numbers a result's words state that the reading read as nothing.

The executors' rules already judge a SAMBAR run whose kmax exceeds its samples (`combination_issues`), but M25 "Set
SAMBAR going on mut_pilot.csv (6 tumours ...), trying anywhere from 2 to 8 subtypes" was run: the reading typed no
setting from "2 to 8", so no rule saw it. Replayed over every reading, such unread numbers sat only in SAMBAR subtype
ranges (M25, C30 x2 run although gold DECLINE; C35, L30 gold DO).

So the trigger is code's (GraphRAG gleaning, Gero 2023): a result whose named workflow has numeric settings, and whose
words hold a number no read count or setting covers, by position in the request. One narrow read lists only that
workflow's numeric settings (IEPile: few fields at a time) as flat required pairs -- the words that set each, and the
value (VAREX, Round 4: a small model leaves object lists empty). Code keeps a pair only when its words are in the
request, cover one of the unread numbers and contain its value's number; the workflow's own rules then judge it
(`method_fitting`), never the model.
"""

from __future__ import annotations

import re
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field, create_model

from workflow_registry import ACTION_DEFINITIONS

from ..contracts.capability_check import CapabilityCheck, full_gap
from ..workflow_conditions import conditions_for, stated_numbers
from .method_conditions import method_fitting
from .request_spans import _span

__all__ = ["SETTINGS_READ_INSTRUCTIONS", "numeric_controls", "settings_read_model", "settings_read_triggers",
           "unread_numbers", "with_settings_read"]

SETTINGS_READ_INSTRUCTIONS = (
    "Return only the SettingsRead structure. You are given a user's request to run a bioinformatics workflow and that "
    "workflow's numeric settings. For each setting, copy the exact words of the request that set it and give the "
    "value they state; leave both empty when the request does not set it."
)
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


def numeric_controls(workflow: str) -> list[tuple[str, str]]:
    """(name, contract description) of each numeric setting the workflow passes to its executor."""
    conditions = conditions_for(workflow)
    if conditions is None:
        return []
    described = {control.name: control.description for control in ACTION_DEFINITIONS[conditions.action].controls}
    return [(name, described.get(name, "")) for name, limit in conditions.settings.items()
            if limit.control_type in ("number", "integer") and limit.wired]


@lru_cache(maxsize=16)
def settings_read_model(workflow: str) -> type[BaseModel]:
    fields = {}
    for name, description in numeric_controls(workflow):
        fields[f"{name}_words"] = (str, Field(description=(
            f"The request's exact words that set {name} ({description.rstrip('.')}); empty when it does not set it.")))
        fields[f"{name}_value"] = (str, Field(description=f"The value of {name} those words state; empty when none."))
    return create_model("SettingsRead", __config__=ConfigDict(extra="forbid"), **fields)


def unread_numbers(check: CapabilityCheck, row, task: str) -> list[tuple[int, int]]:
    """(start, end) of each number in the result's words that no read count or setting covers, by position. A number
    inside a word or a file name (h.all.v2023.gmt, expr_2023.tsv) is no stated number."""
    span = _span(task, row.quote)
    if span is None:
        return []
    read = [tuple(found) for fact in check.facts for found in (fact.span, fact.value_span) if len(found) == 2]
    found = []
    for token in re.finditer(r"\S+", task[span[0]:span[1]]):
        words = token.group().strip("()[]{},;:!?\"'")
        start = span[0] + token.start() + token.group().index(words) if words else 0
        if not words or not _NUMBER.fullmatch(words):
            continue
        end = start + len(words)
        if not any(s < end and start < e for s, e in read):
            found.append((start, end))
    return found


def settings_read_triggers(check: CapabilityCheck | None, task: str) -> list[tuple[int, str]]:
    """(row index, named workflow) of each credited result with numeric settings and an unread number in its words."""
    if check is None or check.unconfirmed():
        return []
    return [(index, row.method["named"]) for index, row in enumerate(check.requirements)
            if row.kind == "result" and row.status in ("available", "with_step", "partial")
            and row.method.get("named") and numeric_controls(row.method["named"]) and unread_numbers(check, row, task)]


def with_settings_read(check: CapabilityCheck, task: str, index: int, workflow: str, read) -> CapabilityCheck:
    """The check with each setting the read found for an unread number added to the result, and judged."""
    if read is None:
        return check
    row = check.requirements[index]
    unread = unread_numbers(check, row, task)
    named = {item["name"] for item in row.method.get("settings", [])}
    added = []
    for name, _description in numeric_controls(workflow):
        words, value = (getattr(read, f"{name}_words", "") or "").strip(), (getattr(read, f"{name}_value", "") or "")
        span = _span(task, words) if words else None
        if (span is None or f"{workflow}.{name}" in named or not stated_numbers(value)
                or not any(span[0] <= s and e <= span[1] for s, e in unread)
                or not all(number in stated_numbers(task[span[0]:span[1]]) for number in stated_numbers(value))):
            continue
        added.append({"name": f"{workflow}.{name}", "quote": task[span[0]:span[1]], "value": value.strip(),
                      "span": list(span)})
    if not added:
        return check
    method = {**row.method, "settings": [*row.method.get("settings", []), *added]}
    kept, limits, instead, defaults = method_fitting(method, row.delivered_by)
    update = {"method": method}
    if limits:
        update.update({"delivered_by": kept, "status": row.status if kept else "not_available",
                       "limits": list(dict.fromkeys([*row.limits, *limits])),
                       "defaults": list(dict.fromkeys([*row.defaults, *defaults])),
                       "instead": list(dict.fromkeys([*row.instead, *instead]))})
    rows = [*check.requirements[:index], row.model_copy(update=update), *check.requirements[index + 1:]]
    results = [item for item in rows if item.kind == "result"]
    return check.model_copy(update={"requirements": rows, "full_gap": full_gap(results, check.unchecked)})
