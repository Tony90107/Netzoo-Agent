"""The focused re-read (closed-menu phase 1, step 4; recommended by phase 0's missed-field check).

Phase 0 found that a reading missing one field turns into a wrong call only for limit fields (settings, counts, only
some data) and doubt fields (unsure or conflicting): a missed limit commits to what cannot run, a missed doubt runs
without asking. Once the first reading leaves its candidate workflows (`menu_decision.candidate_workflows`), this second
read lists each candidate's limits -- every control with its allowed values, the counts its contract limits, the data
it needs, the data conditions that rule it out -- one schema field each, and the model says for each what the words
say: stated (its value), unsure (the user does not know, or gives several: the values), or not mentioned.

Code merges it into the first reading (`merge_focused`): a limit the first reading did not state is added; a doubt
the focused read finds replaces a stated value, since a value the user is unsure of is asked, never assumed. Every
quote is checked against the request, as in the first read.

Phase 1: offline only; nothing in the live path calls it.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, create_model

from ..contracts.capability_check import CONDITIONS
from ..contracts.menu_reading import Count, MenuReading, Said, SettingAsked
from ..judgment_defaults import judgment_defaults
from ..method_names import UNREGISTERED
from ..workflow_conditions import all_conditions
from .menu_decision import workflow_conditions
from .menu_reader import _CONDITION_MEANS, _DATA_MEANS, _IDENTIFIER, ReadReport, _strict, quote_in, request_layout

__all__ = ["focus_limits", "focus_model", "focus_text", "merge_focused"]

_FORBID = ConfigDict(extra="forbid")
Mention = Literal["stated", "unsure", "not_mentioned"]
Have = Literal["has", "lacks", "unsure", "not_mentioned"]
_QUOTE = Field(description="The user's exact words that state it or show the doubt; empty when not mentioned.")


def _key(workflow: str, control: str) -> str:
    return f"{re.sub(r'[^a-z0-9]+', '_', workflow.casefold())}__{control}"


@lru_cache(maxsize=64)
def focus_limits(candidates: tuple[str, ...]) -> dict:
    """What the candidates' contracts limit: controls by schema key, counts, data needs and conditions."""
    table, conditions = judgment_defaults(), all_conditions()
    controls, counts, data, named = {}, {}, [], []
    for workflow in candidates:
        limits = conditions.get(workflow)
        if limits is None:
            continue
        for name, limit in limits.settings.items():
            controls[_key(workflow, name)] = (workflow, name, limit)
        if limits.min_samples is not None or workflow == "SAMBAR":
            counts.setdefault("sample_count", []).append(
                f"{workflow}: at least {limits.min_samples} samples" if limits.min_samples is not None
                else f"{workflow}: kmax at most the number of samples")
        if limits.max_values is not None:
            counts.setdefault("feature_count", []).append(
                f"{workflow}: features of all layers together, at most {limits.max_values:,} values "
                f"({limits.size_formula})")
            counts.setdefault("sample_count", [])
        if limits.relation is not None:
            counts.setdefault("feature_count", []).append(f"{workflow}: genes ({limits.relation_name})")
        for need in table.workflow_data.get(workflow, ((), ()))[1]:
            data += [option for option in need.split("|") if option != "two_layers" and option not in data]
        named += [name for name in workflow_conditions(workflow, table) if name not in named]
    return {"controls": controls, "counts": counts, "data": data, "conditions": named}


def focus_text(candidates: tuple[str, ...]) -> str:
    from workflow_registry import ACTION_DEFINITIONS
    from ..method_names import registered_workflows

    limits = focus_limits(tuple(candidates))
    lines = [f"CANDIDATE WORKFLOWS: {', '.join(candidates)}", "", "CONTROLS (settings.<key>):"]
    for key, (workflow, name, limit) in limits["controls"].items():
        action = registered_workflows()[workflow]
        description = next((c.description for c in ACTION_DEFINITIONS[action].controls if c.name == name), "")
        if limit.control_type == "enum":
            kind = "one of " + ", ".join(map(str, limit.allowed_values))
        elif limit.control_type in ("number", "integer"):
            kind = limit.control_type + "".join(
                f" {word} {value:g}" for word, value in (("min", limit.minimum), ("max", limit.maximum))
                if value is not None)
        else:
            kind = "true or false" if limit.control_type == "boolean" else limit.control_type.replace("_", " ")
        lines.append(f"- {key} = {workflow} {name} ({kind}): {description}")
    if not limits["controls"]:
        lines.append("- none: the candidates take no settings.")
    lines.append("UNSUPPORTED SETTINGS (unsupported_settings): a setting the user asks to run with that none of the "
                 "controls above is, for example a learning rate, a penalty or a solver no candidate takes.")
    lines += ["", "COUNTS (counts.<name>):"]
    lines += [f"- {name}: {'; '.join(parts) or 'the total number of samples'}" for name, parts in limits["counts"].items()]
    lines += ["", "DATA (data.<kind>: has, lacks, unsure, not_mentioned):"]
    lines += [f"- {kind}: {_DATA_MEANS[kind]}" for kind in limits["data"]]
    lines += ["", "DATA CONDITIONS (conditions.<name>):"]
    for name in limits["conditions"]:
        values = [v for v in CONDITIONS[name][0] if v != "not_stated"] if name in CONDITIONS \
            else list(judgment_defaults().dimensions[name].values)
        lines.append(f"- {name} ({', '.join(values)}): {_CONDITION_MEANS[name]}")
    return "\n".join(lines)


@lru_cache(maxsize=64)
def focus_model(candidates: tuple[str, ...]) -> type[BaseModel]:
    """One field per limit of the candidates (strict mode)."""
    limits = focus_limits(candidates)
    setting = create_model(
        "FocusedSetting", __config__=_FORBID,
        status=(Mention, Field(description="stated: the words give a value; unsure: the user does not know which "
                                           "value, or gives several; not_mentioned.")),
        value=(str, Field(description="stated: the value as the control's allowed values spell it.")),
        values=(list[str], Field(description="unsure: the values the words leave open.")),
        quote=(str, _QUOTE),
    )
    count = create_model(
        "FocusedCount", __config__=_FORBID,
        status=(Mention, Field(description="stated: the words give the number; unsure: the user does not know it, "
                                           "or gives several; not_mentioned.")),
        value=(int | None, Field(description="stated: the number.")),
        values=(list[int], Field(description="unsure: the numbers the words leave open.")),
        quote=(str, _QUOTE),
    )
    have = create_model(
        "FocusedData", __config__=_FORBID,
        status=(Have, Field(description="has, lacks, unsure (the user does not know whether they have it or what a "
                                        "file holds), not_mentioned.")),
        quote=(str, _QUOTE),
    )

    def condition(name: str):
        values = tuple(v for v in CONDITIONS[name][0] if v != "not_stated") if name in CONDITIONS \
            else tuple(judgment_defaults().dimensions[name].values)
        Value = Literal[values]  # type: ignore[valid-type]
        return create_model(
            f"Focused{''.join(part.capitalize() for part in name.split('_'))}", __config__=_FORBID,
            status=(Mention, Field(description="stated, unsure (the user does not know, or says two things), "
                                               "not_mentioned.")),
            value=(Value | None, Field(description="stated: the value.")),
            values=(list[Value], Field(description="unsure: the values the words leave open.")),
            quote=(str, _QUOTE),
        )

    def group(name: str, fields: dict):
        return create_model(name, __config__=_FORBID, **fields)

    unsupported = create_model(
        "UnsupportedSetting", __config__=_FORBID,
        quote=(str, Field(description="The user's exact words asking for the setting.")),
        workflow=(str, Field(description="The candidate workflow it is asked for; empty when the words do not say.")),
        value=(str, Field(description="The value the words give; empty when none.")),
        asks_to_set=(bool, Field(description="true when the user asks to run with it; false when the words only "
                                             "describe their data.")),
    )

    fields = {
        "settings": (group("FocusedSettings", {key: (setting, Field(description=f"{workflow} {control}"))
                                               for key, (workflow, control, _limit) in limits["controls"].items()}), ...),
        "counts": (group("FocusedCounts", {name: (count, Field(description=name)) for name in limits["counts"]}), ...),
        "data": (group("FocusedDataKinds", {kind: (have, Field(description=_DATA_MEANS[kind]))
                                            for kind in limits["data"]}), ...),
        "conditions": (group("FocusedConditions", {name: (condition(name), Field(description=_CONDITION_MEANS[name]))
                                                   for name in limits["conditions"]}), ...),
        # Phase 1b step 4 (bench C08: GIRAFFE takes no settings, so a learning rate had no field to land in).
        "unsupported_settings": (list[unsupported], Field(description=(
            "Each setting the user asks to run with that no listed control is."))),
    }
    return _strict(create_model("FocusedReading", __config__=_FORBID, **fields))


def _numbers_of(values) -> list[int]:
    return sorted({int(n.value) for value in values for n in request_layout(str(value)).numbers})


def merge_focused(first: MenuReading, payload, task: str, candidates: tuple[str, ...]) -> tuple[MenuReading, ReadReport]:
    """The first reading with the focused read's limits added and its doubts in place of stated values."""
    raw = payload.model_dump(mode="json") if isinstance(payload, BaseModel) else dict(payload)
    report, limits = ReadReport(), focus_limits(tuple(candidates))

    def words(entry: dict, where: str) -> str:
        quote = entry.get("quote") or ""
        if quote_in(quote, task):
            return quote
        report.dropped.append(f"focus.{where}: {entry.get('status')} without verified words {quote!r}")
        return ""

    settings = list(first.settings)
    for key, entry in (raw.get("settings") or {}).items():
        if key not in limits["controls"] or entry.get("status") == "not_mentioned":
            continue
        workflow, control, _limit = limits["controls"][key]
        quote = words(entry, f"settings.{key}")
        if not quote:
            continue
        same = [s for s in settings if s.control == control and s.workflow in (workflow, "")]
        values = list(dict.fromkeys(str(v) for v in entry.get("values") or [] if str(v).strip()))
        if entry["status"] == "unsure" and len(values) >= 2:
            settings = [s for s in settings if s not in same] + [SettingAsked(
                quote=quote, workflow=workflow, control=control, unsure=True, values=values)]
            report.filled.append(f"focus: {workflow}.{control} unsure between {values}")
        elif entry["status"] == "stated" and str(entry.get("value") or "").strip() and not any(
                s.value or s.unsure for s in same):
            settings = [s for s in settings if s not in same] + [SettingAsked(
                quote=quote, workflow=workflow, control=control, value=str(entry["value"]))]
            report.filled.append(f"focus: {workflow}.{control} = {entry['value']}")
    for index, entry in enumerate(raw.get("unsupported_settings") or []):
        if not entry.get("asks_to_set"):
            continue
        quote = words({**entry, "status": "unsupported"}, f"unsupported_settings[{index}]")
        if not quote or any(quote_in(quote, s.quote) or quote_in(s.quote, quote) for s in settings if s.quote):
            continue  # words not in the request, or a setting the reading already has
        if _IDENTIFIER.search(quote):
            # A file name or an input field names an input, not a setting (d8 m3:U18: "covariance_bundle.tsv as
            # coexpression_file" refused PANDA as a setting it lacks).
            report.dropped.append(f"focus.unsupported_settings[{index}]: names a file or field, not a setting")
            continue
        workflow = entry.get("workflow") if entry.get("workflow") in candidates else ""
        settings.append(SettingAsked(quote=quote, workflow=workflow, control=UNREGISTERED,
                                     value=str(entry.get("value") or "")))
        report.filled.append(f"focus: unsupported setting {quote[:50]!r} for {workflow or 'every candidate'}")
    counts = {"sample_count": first.sample_count, "feature_count": first.feature_count}
    for name, entry in (raw.get("counts") or {}).items():
        if name not in counts or entry.get("status") == "not_mentioned":
            continue
        quote = words(entry, f"counts.{name}")
        if not quote:
            continue
        values = sorted({int(v) for v in entry.get("values") or []}) or _numbers_of([quote])
        if entry["status"] == "unsure" and len(values) >= 2 and counts[name].status != "conflicting":
            counts[name] = Count(status="conflicting", values=values, quotes=[quote])
            report.filled.append(f"focus: {name} unsure between {values}")
        elif entry["status"] == "stated" and entry.get("value") is not None and counts[name].status == "not_stated":
            counts[name] = Count(status="stated", value=int(entry["value"]), quotes=[quote])
            report.filled.append(f"focus: {name} = {entry['value']}")
    data, absent, files = list(first.data), list(first.data_absent), list(first.unsure_files)
    for kind, entry in (raw.get("data") or {}).items():
        if kind not in limits["data"] or entry.get("status") == "not_mentioned":
            continue
        quote = words(entry, f"data.{kind}")
        if not quote:
            continue
        status = entry["status"]
        if status == "has" and kind not in data and kind not in absent:
            data.append(kind)
        elif status == "lacks" and kind not in absent and kind not in data:
            absent.append(kind)
            report.filled.append(f"focus: lacks {kind}")
        elif status == "unsure" and quote not in files:
            files.append(quote)  # what a file or dataset holds: settled by the input check, or asked
            report.filled.append(f"focus: unsure whether it has {kind}")
    conditions = dict(first.conditions)
    for name, entry in (raw.get("conditions") or {}).items():
        if name not in limits["conditions"] or entry.get("status") == "not_mentioned":
            continue
        quote = words(entry, f"conditions.{name}")
        if not quote:
            continue
        values = list(dict.fromkeys(v for v in entry.get("values") or [] if v))
        before = conditions.get(name, Said())
        if entry["status"] == "unsure" and before.status not in ("unsure", "conflicting"):
            menu = [v for v in CONDITIONS[name][0] if v != "not_stated"] if name in CONDITIONS \
                else list(judgment_defaults().dimensions[name].values)
            conditions[name] = Said(status="unsure", values=values if len(values) >= 2 else menu, quotes=[quote])
            report.filled.append(f"focus: {name} unsure")
        elif entry["status"] == "stated" and entry.get("value") and before.status == "not_stated":
            conditions[name] = Said(status="stated", value=entry["value"], basis="explicit", quotes=[quote])
            report.filled.append(f"focus: {name} = {entry['value']}")
    merged = first.model_copy(update={"settings": settings, "sample_count": counts["sample_count"],
                                      "feature_count": counts["feature_count"], "data": data, "data_absent": absent,
                                      "unsure_files": files, "conditions": conditions})
    return merged, report
