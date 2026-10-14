"""M1 (2026-10-14): an ask's named method, settings and data size, verified against the request and judged in code.

The model types them (`contracts.capability_check._method_fields`); code keeps each only when its words are in the
request and decides, from `workflow_conditions` alone, which credited workflow can run as asked. The capability
check, its second opinion and its redirect all hold a result to the same verdict.
"""

from __future__ import annotations

import re

from ..capability_sheet import entry
from ..method_names import LIONESS_FAMILY, registered_workflows
from ..workflow_conditions import (
    UNREGISTERED, StatedSetting, conditions_for, data_issue, named_workflows, setting_issue, stated_numbers,
)
from .request_spans import _span

__all__ = ["method_fitting", "verified_method"]


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
    found: dict = {}
    named, said = getattr(item, "named_method", "none"), _stated(task, getattr(item, "named_method_quote", ""))
    if named not in (None, "none") and said and (named == UNREGISTERED or _folded(named) in _folded(said)):
        found.update(named=_unregistered_lioness(said) or named, named_quote=said)
    settings = []
    for setting in getattr(item, "settings", None) or []:
        if (words := _stated(task, setting.quote)) is not None:
            settings.append({"name": setting.name, "quote": words, "value": _stated(task, setting.value_quote) or ""})
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
    LIONESS-PANDA could have been credited for it.
    """
    folded, known = _folded(said), registered_workflows()
    if LIONESS_FAMILY.casefold() not in folded or any(
            _folded(name) in folded for name in known if name.startswith(f"{LIONESS_FAMILY}-")):
        return None
    bases = [name for name in known if not name.startswith(f"{LIONESS_FAMILY}-") and _folded(name) in folded]
    return UNREGISTERED if any(f"{LIONESS_FAMILY}-{name}" not in known for name in bases) else None


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
            issue for setting in settings if (issue := setting_issue(conditions, setting))]
        too_much = data_issue(conditions, samples, features) if conditions is not None else None
        limits.extend([*unset, *filter(None, [too_much])])
        if unset and not too_much:
            defaults.append(key)
        elif not too_much:
            kept.append(key)
    if instead and not kept and named not in (None, UNREGISTERED):
        limits.insert(0, f"NetZoo's {named} does not give this result")
    return kept, list(dict.fromkeys(limits)), list(dict.fromkeys(instead)), list(dict.fromkeys(defaults))
