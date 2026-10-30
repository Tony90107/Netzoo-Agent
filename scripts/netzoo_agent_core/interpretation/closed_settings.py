"""The closed settings read (docs/research-log/jev-settings-2026-10-31/ROUND.md): which registered controls the user
asks to set, one closed question per control, and what that means for the capability check. Pure code.

A setting lives only inside a credited result's `method["settings"]`; a sentence that only states one ("Try anywhere
between 2 and 5 subtypes.") is its own uncredited result with no reason, so it renders as unmatched and makes the turn
partial (j8 Z01, j3 R41, j4 S12). The read asks Jev, per control, whether the user sets it (the contract's own name,
type and description; never a phrase list) and which request sentence says so; a small model gives only the value,
kept when its words lie inside that sentence. Code then (1) adds each strong setting to the credited result whose
workflow passes that control to its executor and re-judges it with the workflow's rules (`method_fitting`: ranges,
kmax <= samples, save_pvals with sparsify, the lambda pair), and (2) drops an uncredited, reasonless row inside such a
sentence -- or, when no credited workflow has the control, gives it the contract's "has no setting for" line instead of
the unmatched one. Nothing is credited and nothing is ruled out except through those contract lines.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from ..contracts.capability_check import CapabilityCheck, full_gap
from ..capability_sheet import entry
from ..workflow_conditions import StatedSetting, conditions_for, setting_issue
from .method_conditions import method_fitting
from .request_spans import _span

__all__ = ["OTHER", "QUOTE_INSTRUCTIONS", "SET_CRITERIA", "THRESHOLD", "VALUE_SYSTEM", "VALUE_TASK", "controls",
           "questions", "strong_reads", "with_closed_settings"]

THRESHOLD = 0.7
OTHER = "other"
WORKFLOWS = Path(__file__).resolve().parents[3] / "workflows"
# The research questions (candidate-table-2026-10-30/settings_read.py), unchanged.
SET_CRITERIA = {"set": "Yes: the user asks to set it to a value or choice.",
                "not_stated": "The request does not ask to set it."}
QUOTE_INSTRUCTIONS = "Pick the sentence of the user's request that states this. Question: {question} Answer: {answer}"
VALUE_SYSTEM = ("You copy evidence from a user's request to a network-analysis assistant. Copy text exactly, character "
                "for character, from the request; never paraphrase. Return JSON only.")
VALUE_TASK = ("Request:\n<<<{prompt}>>>\n\nFor each setting named below, give the value the user asks for and the "
              "words of the request that state it, copied exactly.\n{names}")


@lru_cache(maxsize=1)
def controls() -> dict[str, dict]:
    """name -> {type, description}: every registry control, the first contract (by file name) giving its words."""
    out: dict[str, dict] = {}
    for path in sorted(WORKFLOWS.glob("*.yaml")):
        for control in yaml.safe_load(path.read_text()).get("controls") or []:
            out.setdefault(control["name"], {"type": control.get("type"),
                                             "description": " ".join(str(control.get("description", "")).split())})
    return out


@lru_cache(maxsize=1)
def questions() -> dict[str, str]:
    """Question key -> instructions; every question has SET_CRITERIA."""
    out = {name: f"Does the user ask to set {name} ({spec['type']}): {spec['description']}"
           for name, spec in controls().items()}
    out[OTHER] = f"Does the user ask to set a method parameter or option that is none of these: {', '.join(controls())}?"
    return out


def strong_reads(task: str, answers: dict, picks: dict, sentences: dict[str, str], values: dict) -> list[dict]:
    """The reads code keeps: `set` at >= 0.7, its sentence picked at >= 0.7, and for a control a value whose words are
    in the request, inside that sentence, and contain it. {control, sentence, value, value_span}."""
    kept = []
    for name, answer in answers.items():
        pick = picks.get(name) or {}
        sentence = sentences.get(pick.get("choice", "none"))
        if answer.get("choice") != "set" or answer.get("confidence", 0) < THRESHOLD or sentence is None \
                or pick.get("confidence", 0) < THRESHOLD or (where := _span(task, sentence)) is None:
            continue
        if name == OTHER:
            kept.append({"control": OTHER, "sentence": task[where[0]:where[1]], "value": "", "value_span": None})
            continue
        said = values.get(name) or {}
        value, words = (said.get("value") or "").strip(), (said.get("words") or "").strip()
        inside = _inside(task, where, words) or _inside(task, where, value)
        if not value or inside is None or value.casefold() not in task[inside[0]:inside[1]].casefold():
            continue
        kept.append({"control": name, "sentence": task[where[0]:where[1]], "value": value, "value_span": inside})
    return kept


def _inside(task: str, where: tuple[int, int], words: str) -> tuple[int, int] | None:
    """The words' place inside the sentence -- never request-wide (Z01: a request-wide "5" was the one in "85")."""
    if not words:
        return None
    at = task[where[0]:where[1]].casefold().find(words.casefold())
    return (where[0] + at, where[0] + at + len(words)) if at >= 0 else None


def _wired(workflow: str | None, control: str) -> bool:
    conditions = conditions_for(workflow) if workflow else None
    limit = conditions.settings.get(control) if conditions is not None else None
    return limit is not None and limit.wired


def with_closed_settings(check: CapabilityCheck | None, task: str, reads: list[dict]) -> CapabilityCheck | None:
    """The check with each strong read applied (module docstring); unchanged when nothing applies."""
    if check is None or not reads or check.unconfirmed():
        return check
    rows = list(check.requirements)
    credited = [i for i, row in enumerate(rows)
                if row.kind == "result" and row.status in ("available", "with_step", "partial")]
    changed = set()
    for read in reads:
        if read["control"] == OTHER:
            continue
        for index in credited:
            row = rows[index]
            workflow = next((entry(key).workflow for key in row.delivered_by if _wired(entry(key).workflow,
                                                                                      read["control"])), None)
            name = f"{workflow}.{read['control']}" if workflow else None
            if name is None or any(item.get("name") == name for item in row.method.get("settings", [])):
                continue
            start, end = read["value_span"]
            added = {"name": name, "quote": task[start:end], "value": read["value"], "span": [start, end], "at": start}
            rows[index] = row.model_copy(update={"method": {**row.method,
                                                            "settings": [*row.method.get("settings", []), added]}})
            changed.add(index)
            break
    for index in changed:
        row = rows[index]
        kept, limits, instead, defaults = method_fitting(row.method, row.delivered_by)
        if limits:
            rows[index] = row.model_copy(update={
                "delivered_by": kept, "status": row.status if kept else "not_available",
                "limits": list(dict.fromkeys([*row.limits, *limits])),
                "defaults": list(dict.fromkeys([*row.defaults, *defaults])),
                "instead": list(dict.fromkeys([*row.instead, *instead]))})
    workflows = [entry(key).workflow for i in credited for key in rows[i].delivered_by]
    dropped = set()
    for index, row in enumerate(rows):
        if row.kind != "result" or row.status != "not_available" or row.delivered_by or row.not_by \
                or row.limits or row.violations or _has_reason(row, check):
            continue
        place = _span(task, row.quote)
        read = next((r for r in reads if place is not None and (s := _span(task, r["sentence"])) is not None
                     and s[0] <= place[0] and place[1] <= s[1]), None)
        if read is None or not workflows:
            continue
        if read["control"] != OTHER and any(_wired(w, read["control"]) for w in workflows):
            dropped.add(index)  # the sentence states a setting a credited workflow takes
            continue
        conditions = conditions_for(workflows[0])
        name = UNSET if read["control"] == OTHER else f"{workflows[0]}.{read['control']}"
        if conditions is not None and (issue := setting_issue(conditions, StatedSetting(name, row.quote,
                                                                                         read["value"]))):
            rows[index] = row.model_copy(update={"limits": [issue], "blank": False})
    if not changed and not dropped and rows == check.requirements:
        return check
    rows = [row for i, row in enumerate(rows) if i not in dropped]
    results = [row for row in rows if row.kind == "result"]
    return check.model_copy(update={"requirements": rows, "full_gap": full_gap(results, check.unchecked)})


UNSET = "unregistered"
"""`setting_issue`'s name for a setting no control is: it answers with the workflow's own list of settings."""


def _has_reason(row, check: CapabilityCheck) -> bool:
    """Whether the row already renders a reason (a form, a fact): only an unmatched row is replaced."""
    from .capability_check import _why_not

    return bool(_why_not(row, check))
