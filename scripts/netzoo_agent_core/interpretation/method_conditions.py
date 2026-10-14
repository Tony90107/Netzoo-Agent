"""M1 (2026-10-14): an ask's named method, settings and data size, verified against the request and judged in code.

The model types them (`contracts.capability_check._method_fields`); code keeps each only when its words are in the
request and decides, from `workflow_conditions` alone, which credited workflow can run as asked. The capability
check, its second opinion and its redirect all hold a result to the same verdict.
"""

from __future__ import annotations

import re

from ..capability_sheet import entry, sheet_entries
from ..contracts.capability_check import CheckedRequirement
from ..method_names import LIONESS_FAMILY, registered_workflows
from ..workflow_conditions import (
    UNREGISTERED, StatedSetting, combination_issues, conditions_for, data_issue, named_workflows, setting_issue,
    stated_numbers,
)
from .request_spans import _span

__all__ = ["method_fitting", "request_method", "request_method_for", "request_method_limit", "verified_controls",
           "verified_method", "with_request_method"]


def _folded(text: str) -> str:
    return re.sub(r"[^0-9a-z]+", "", (text or "").casefold())


def _stated(task: str, quote: str) -> str | None:
    """The request's own words for a quote, or None when they are not in it."""
    span = _span(task, quote) if (quote or "").strip() else None
    return task[span[0]:span[1]] if span is not None else None


def verified_method(task: str, item) -> dict:
    """M1 (2026-10-14): the ask's named method, settings and data size, each kept only when its words are in the
    request -- a registered method only when the words name it, a count only when the words state that number.

    Recordings from before M1 state none of these, so nothing is kept and no rule fires on them.
    """
    from ..method_names import method_names, setting_names

    found: dict = {}
    named, said = getattr(item, "named_method", "none"), _stated(task, getattr(item, "named_method_quote", ""))
    if named not in (None, "none", UNREGISTERED, *method_names()):
        named = UNREGISTERED  # the compact schema's names are strings (M2, live m2b P30)
    if named not in (None, "none") and said and (named == UNREGISTERED or _folded(named) in _folded(said)):
        found.update(named=named, named_quote=said)
        asked = _stated(task, getattr(item, "quote", "")) or ""
        if _unregistered_lioness(said):
            found["named"] = UNREGISTERED
        elif asked and _unregistered_lioness(f"{said} {asked}"):  # m1b N12: "LIONESS-style", OTTER in the ask's words
            found.update(named=UNREGISTERED, named_quote=asked)
    settings = []
    for setting in getattr(item, "settings", None) or []:
        if (span := _span(task, setting.quote) if setting.quote.strip() else None) is not None:
            value = _span(task, setting.value_quote) if setting.value_quote.strip() else None
            name = setting.name if setting.name in setting_names() else UNREGISTERED
            settings.append({"name": name, "quote": task[span[0]:span[1]],
                             "value": task[value[0]:value[1]] if value else "", "span": list(span),
                             "at": (value or span)[0]})
    if settings:
        found["settings"] = settings
    count, words = getattr(item, "sample_count", None), _stated(task, getattr(item, "sample_count_quote", ""))
    if count is not None and words and count in stated_numbers(words):
        found.update(samples=count, samples_quote=words)
    features = {}
    for stated in getattr(item, "feature_counts", None) or []:
        if (words := _stated(task, stated.quote)) and stated.count in stated_numbers(words):
            features.setdefault(_span(task, stated.quote), stated.count)
    if features:
        found["features"] = sum(features.values())
    return found


def _unregistered_lioness(said: str) -> str | None:
    """A LIONESS version of a registered workflow that has none here ("LIONESS-OTTER") names no registered method.

    m1a MX18: "the per-sample LIONESS-OTTER networks" was typed LIONESS, which stands for every LIONESS-X, so
    LIONESS-PANDA could have been credited for it; m1b N12: "one OTTER network per sample, LIONESS-style" likewise.
    Only a workflow with no per-sample result can be the base ("LIONESS or BONOBO" names two methods), and every base
    the words name must lack a LIONESS version.
    """
    folded, known = _folded(said), registered_workflows()
    if LIONESS_FAMILY.casefold() not in folded or any(
            _folded(name) in folded for name in known if name.startswith(f"{LIONESS_FAMILY}-")):
        return None
    per_sample = {found.workflow for found in sheet_entries().values()
                  if found.kind == "produces" and "sample_specific" in found.granularity}
    bases = [name for name in known if not name.startswith(f"{LIONESS_FAMILY}-") and name not in per_sample
             and _folded(name) in folded]
    return UNREGISTERED if bases and all(f"{LIONESS_FAMILY}-{name}" not in known for name in bases) else None


def method_fitting(method: dict, keys: list[str]) -> tuple[list[str], list[str], list[str], list[str]]:
    """M1: the credited entries whose workflow can run as the request asks; why the others cannot; the entries of
    other workflows that give the result by a method the request did not name; and the entries whose workflow could
    give it with its own settings, only not with the ones stated.

    The named method allows only itself and its registered LIONESS version (an unregistered one allows none); each
    remaining workflow must have every stated setting, wired to its executor and in range, and take the stated
    number of samples and features (`workflow_conditions`). What the request does not state is never judged.
    """
    if not method:
        return list(keys), [], [], []
    named = method.get("named")
    allowed = named_workflows(named) if named else None
    samples, features = method.get("samples"), method.get("features")
    settings = [StatedSetting(item["name"], item["quote"], item.get("value", "")) for item in method.get("settings", [])]
    kept, limits, instead, defaults = [], [], [], []
    if named == UNREGISTERED:
        limits.append(f'NetZoo has no registered method or variant "{method["named_quote"]}"')
    for key in keys:
        workflow = entry(key).workflow
        if allowed is not None and workflow not in allowed:
            instead.append(key)
            continue
        conditions = conditions_for(workflow) if workflow else None
        unset = [] if conditions is None else [
            *(issue for setting in settings if (issue := setting_issue(conditions, setting))),
            *combination_issues(conditions, settings, samples)]
        too_much = data_issue(conditions, samples, features) if conditions is not None else None
        limits.extend([*unset, *filter(None, [too_much])])
        if unset and not too_much:
            defaults.append(key)
        elif not too_much:
            kept.append(key)
    if instead and not kept and named not in (None, UNREGISTERED):
        limits.insert(0, f"NetZoo's {named} does not give this result")
    return kept, list(dict.fromkeys(limits)), list(dict.fromkeys(instead)), list(dict.fromkeys(defaults))


def request_method(task: str, proposal) -> dict:
    """The method and settings the request names as a whole (live m1a F1), verified like an ask's."""
    found = verified_method(task, getattr(proposal, "conditions", None))
    return {key: value for key, value in found.items() if key in ("named", "named_quote", "settings")}


def with_request_method(method: dict, whole: dict) -> dict:
    """An ask's method with the request's named method and settings where it states none of its own.

    Applied only when the request asks for one result: with two, a setting given for one workflow would hold the other
    to it ("run PANDA ..., then CONDOR on it").
    """
    merged = dict(method)
    if "named" not in merged and "named" in whole:
        merged.update(named=whole["named"], named_quote=whole["named_quote"])
    if settings := _latest([*merged.get("settings", []), *whole.get("settings", [])]):
        merged["settings"] = settings
    return merged


def request_method_for(whole: dict, workflows: set[str]) -> dict:
    """The request's method and settings that belong to one of several results (M2): its named method when that names
    a workflow the result is credited to, and each registered setting of such a workflow. An unregistered setting
    names no workflow, so with several results it is not given to any."""
    found = {}
    if whole.get("named") not in (None, UNREGISTERED) and named_workflows(whole["named"]) & workflows:
        found.update(named=whole["named"], named_quote=whole["named_quote"])
    settings = [item for item in whole.get("settings", [])
                if item["name"] != UNREGISTERED and item["name"].split(".", 1)[0] in workflows]
    if settings:
        found["settings"] = settings
    return found


def _latest(settings: list[dict]) -> list[dict]:
    """One value per registered setting, the one the request states last; unregistered settings once per passage.

    m1b K09 (turn 2, "Never mind the GPU - CPU is fine"): the ask was typed computing=GPU and the request both GPU and
    CPU; what the user said last is what they want.
    """
    kept: dict = {}
    for setting in settings:
        if setting["name"] != UNREGISTERED:
            if setting["name"] not in kept or setting.get("at", -1) > kept[setting["name"]].get("at", -1):
                kept[setting["name"]] = setting
            continue
        span = setting.get("span") or [-1, -1]
        if not any(other["name"] == UNREGISTERED and (other.get("span") or [-1, -1])[0] < span[1]
                   and span[0] < (other.get("span") or [-1, -1])[1] for other in kept.values()):
            kept[("unregistered", tuple(span), setting["quote"])] = setting
    return list(kept.values())


def _ruled_out_by_data(keys: list[str], conditions: dict[str, str], quotes: dict[str, str]) -> tuple[list[str], str]:
    """The entries the user's data rules out -- single cells, layers not measured on the same samples (Log 412) --
    and the words that say so (M2, a24b K02 asked to run DRAGON, then said the layers came from different mice)."""
    from ..capability_sheet import data_units

    known = sheet_entries()
    if conditions.get("data_unit") and conditions["data_unit"] not in data_units():
        return list(keys), quotes.get("data_unit", "")
    if conditions.get("samples_matched") == "different_samples":
        return [key for key in keys if known[key].layers], quotes.get("samples_matched", "")
    return [], ""


def request_method_limit(whole: dict, conditions: dict[str, str] | None = None,
                         quotes: dict[str, str] | None = None) -> CheckedRequirement | None:
    """A result for a request that asks for none but names a method it cannot have as asked (live m1a F1).

    "Can you run PANDA with its alpha update rate set to 0.25 ...?" was read as a question about the methods only, so
    the run was approved with nothing asked. The named workflow's own results are held to the stated settings; an
    unregistered method gives none. Nothing is added when the request names no method or the method can run as asked.
    """
    named = whole.get("named")
    if not named:
        return None
    # No result says which scale, so the named workflow itself -- not its LIONESS version -- is what is asked to run.
    workflows = {named} if named in registered_workflows() else named_workflows(named)
    keys = [key for key, found in sheet_entries().items()
            if found.kind == "produces" and found.level == "direct" and found.workflow in workflows]
    kept, limits, instead, defaults = method_fitting(whole, keys)
    ruled, said = _ruled_out_by_data(kept, conditions or {}, quotes or {})
    if ruled and said:
        kept = [key for key in kept if key not in ruled]
        names = list(dict.fromkeys(entry(key).workflow for key in ruled))
        limits = [*limits, *(f'NetZoo\'s {name} cannot run on this data: "{said}"' for name in names)]
        defaults = [key for key in defaults if key not in ruled]
    if not limits or kept:
        return None
    quote = (whole["settings"][0]["quote"] if whole.get("settings") and named != UNREGISTERED and not ruled
             else said if ruled and said else whole["named_quote"])
    return CheckedRequirement(quote=quote, kind="result", status="not_available", method=whole, limits=limits,
                              instead=instead, defaults=defaults)


def _control_value(limit, words: str):
    """A stated value as the control takes it: a number in range, or the one allowed choice the words name."""
    if limit.control_type in ("number", "integer"):
        numbers = stated_numbers(words)
        if not numbers:
            return None
        number = numbers[0]
        if limit.control_type == "integer":
            return int(number) if number == int(number) else None
        return number
    if limit.control_type == "enum":
        folded = _folded(words)
        chosen = [item for item in limit.allowed_values if (key := _folded(str(item))) and key in folded]
        return chosen[0] if len(chosen) == 1 else None
    return None  # booleans, names and lists are not read from prose


def verified_controls(check, action: str) -> dict[str, object]:
    """The settings the check verified for a run's workflow, as its control values (M2).

    a24b K06 "Please give it to me as an edge list, with fixed lambdas of 0.2 and 0.6" and K09 "just use single
    precision" were checked but never reached the run: controls were bound only from name=value text, so DRAGON
    would have estimated its own lambdas. Only numbers and allowed choices are taken; every value already passed the
    control's range and the runtime's limits, or the check would not have approved the run.
    """
    conditions = conditions_for(action)
    if check is None or conditions is None:
        return {}
    found: dict[str, object] = {}
    for item in check.results():
        if action not in {entry(key).action for key in item.delivered_by}:
            continue
        for setting in item.method.get("settings", []):
            limit = conditions.settings.get(setting["name"].split(".", 1)[-1]) if setting["name"] != UNREGISTERED else None
            if limit is not None and limit.wired and (value := _control_value(limit, setting.get("value", ""))) is not None:
                found[limit.name] = value
    return found

