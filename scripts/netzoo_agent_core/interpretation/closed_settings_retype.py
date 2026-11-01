"""Class 4 (docs/research-log/excluded-entries-2026-11-01/ROUND-C4.md): a setting the capability check typed onto a
control the user does not set, set apart as the contract's "has no setting for" line. Pure code; the read is
`graph.jev_settings_call` (flag NETZOO_SETTING_RETYPE).

j11 C34 "the update step alpha set to 0.25 instead of the default" was typed `PANDA.with_header = 0.25`; a boolean
cannot take 0.25, so the turn asked what with_header should be. The closed settings read already asks Jev about every
control: when it reads with_header as not set and some other parameter as set in that sentence, and the value cannot
bind to the typed control anyway, the words are no setting PANDA has. They leave the run (which goes ahead with its own
settings) for a row of their own, the shape `method_conditions.settings_apart` gives (DO + partial). Never: when a
control Jev reads as set in that sentence is one the workflow takes (the words may be that control), when the value
binds (a correct setting is never removed), or when a refused row already holds the words.
"""

from __future__ import annotations

from ..capability_sheet import entry
from ..contracts.capability_check import CapabilityCheck, CheckedRequirement, full_gap
from ..workflow_conditions import UNREGISTERED, StatedSetting, conditions_for, setting_issue
from .closed_settings import OTHER, THRESHOLD
from .method_conditions import run_setting_value
from .request_spans import _span

__all__ = ["retyped"]


def _has_reason(row, check) -> bool:
    from .closed_settings import _has_reason as said

    return bool(row.limits or row.violations) or said(row, check)


def _strong(answers: dict, name: str, choice: str) -> bool:
    answer = answers.get(name) or {}
    return answer.get("choice") == choice and answer.get("confidence", 0) >= THRESHOLD


def _sentence_of(read: dict, name: str, task: str):
    """The span of the sentence Jev picked for a control it reads as set (both at >= 0.7), else None."""
    pick = read.get("picks", {}).get(name) or {}
    sentence = read.get("sentences", {}).get(pick.get("choice", "none"))
    if not _strong(read.get("answers", {}), name, "set") or sentence is None or pick.get("confidence", 0) < THRESHOLD:
        return None
    return _span(task, sentence)


def _inside(outer, inner) -> bool:
    return outer is not None and inner is not None and outer[0] <= inner[0] and inner[1] <= outer[1]


def retyped(check: CapabilityCheck | None, task: str, read: dict) -> tuple[CapabilityCheck | None, list[dict]]:
    """(check, changes): each typed setting ROUND-C4's six conditions hold for, set apart; the check unchanged else."""
    if check is None or check.unconfirmed() or not read:
        return check, []
    answers = read.get("answers", {})
    other = _sentence_of(read, OTHER, task)
    if other is None:
        return check, []
    set_spans = {name: span for name in answers if name != OTHER and (span := _sentence_of(read, name, task))}
    rows, changes, added = list(check.requirements), [], []
    for index, row in enumerate(rows):
        if row.kind != "result" or row.status not in ("available", "with_step", "partial"):
            continue
        kept, apart = [], []
        for setting in row.method.get("settings", []):
            name = setting.get("name", "")
            workflow, _, control = name.partition(".")
            conditions = conditions_for(workflow) if control else None
            limit = conditions.settings.get(control) if conditions is not None else None
            words = _span(task, setting.get("quote", ""))
            covering = [i for i, other_row in enumerate(rows) if other_row.kind == "result"
                        and other_row.status == "not_available" and _inside(_span(task, other_row.quote), words)]
            covered = any(_has_reason(rows[i], check) for i in covering)  # Z03: a row already saying a line
            wired_set = any(_inside(span, words) and conditions.settings.get(found) is not None
                            and conditions.settings[found].wired for found, span in set_spans.items()) \
                if conditions is not None else True
            issue = setting_issue(conditions, StatedSetting(UNREGISTERED, setting.get("quote", ""),
                                                            setting.get("value", ""))) if conditions else None
            if (limit is None or words is None or not _strong(answers, control, "not_stated")
                    or not _inside(other, words) or wired_set
                    or run_setting_value(limit, conditions, setting) is not None or covered or not issue):
                kept.append(setting)
                continue
            apart.append((setting, issue, workflow, covering[0] if covering else None))
        if not apart:
            continue
        quotes = [task[s:e] for setting, _issue, _w, _c in apart if (where := _span(task, setting["quote"]))
                  for s, e in [where]]
        stale = {f"setting:{setting['name']}@" for setting, _issue, _w, _c in apart}
        method = {**row.method, "settings": kept} if kept else {k: v for k, v in row.method.items() if k != "settings"}
        method["settings_apart"] = [*row.method.get("settings_apart", []), *quotes]
        rows[index] = row.model_copy(update={"method": method, "fact_ids": [
            fid for fid in row.fact_ids if not any(fid.startswith(prefix) for prefix in stale)]})
        for (setting, issue, workflow, cover), quote in zip(apart, quotes):
            line = {"method": {"settings": [{**setting, "name": UNREGISTERED}]}, "limits": [issue], "blocks": [workflow],
                    "defaults": [key for key in row.delivered_by if entry(key).workflow == workflow]}
            if cover is not None:  # Amendment 1: the reasonless row holding the words takes the line itself
                rows[cover] = rows[cover].model_copy(update={**line, "blank": False})
            else:
                added.append(CheckedRequirement(quote=quote, kind="result", status="not_available", **line))
            changes.append({"row": row.quote, "setting": setting["name"], "words": quote, "line": issue})
    if not changes:
        return check, []
    rows += added
    results = [item for item in rows if item.kind == "result"]
    return check.model_copy(update={"requirements": rows, "full_gap": full_gap(results, check.unchecked)}), changes
