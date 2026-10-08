"""The code-owned capability sheet: what each registered workflow produces (Logs 385-387).

Log 385 measured that a request no registered workflow can answer was given
one 25 times in 45: routing projects every request onto the nearest artifact
in its vocabulary, which has no "none of these". The sheet is the closed list
the capability check reads instead (`scripts/capability_sheet.yaml`):

- a `produces` entry is a result a workflow's executor writes (`direct`), or a
  result its output gives after a named step outside NetZoo (`with_step`);
- a `near_miss` entry is a result someone may expect from that workflow and
  does not get; a `registry_wide` entry is one no workflow gives. Neither ever
  decides support -- they only let a reply say why.

Loading fails closed: an unknown action, a duplicate id, a dangling `see`, a
produces entry without a result or source, or a run action with no produces
entry raises at import time.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml

from workflow_registry import ACTION_DEFINITIONS, RUN_ACTIONS

__all__ = ["SheetEntry", "SHEET_PATH", "load_sheet", "sheet_entries", "entry", "produces_ids", "not_produced_ids"]

SHEET_PATH = Path(__file__).resolve().parents[1] / "capability_sheet.yaml"


@dataclass(frozen=True, slots=True)
class SheetEntry:
    id: str
    kind: Literal["produces", "near_miss", "registry_wide"]
    action: str | None
    workflow: str | None
    text: str
    """`result` for a produces entry, `result_asked` for the others."""
    level: Literal["direct", "with_step"] | None = None
    step: str = ""
    why_not: str = ""
    reading: str = ""
    instead_registered: str | None = None
    source: str = ""
    claim: str | None = None
    """A registry-wide entry's study-purpose claim (causal, prediction); see `capability_check`."""


def _resolve(raw: dict, by_id: dict[str, dict]) -> dict:
    target = raw.get("see")
    if target is None:
        return raw
    if target not in by_id:
        raise ValueError(f"capability sheet: {raw.get('id')!r} refers to unknown entry {target!r}")
    base = _resolve(by_id[target], by_id)
    return {**base, **{key: value for key, value in raw.items() if key != "see"}}


def load_sheet(path: Path = SHEET_PATH) -> dict[str, SheetEntry]:
    """Every entry by id, validated; raises ValueError on any malformed entry."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw_items: list[tuple[str, str | None, str | None, dict]] = []
    for item in data.get("registry_wide_not_produced") or []:
        raw_items.append(("registry_wide", None, None, item))
    for workflow, spec in (data.get("workflows") or {}).items():
        action = spec.get("action")
        if action not in ACTION_DEFINITIONS:
            raise ValueError(f"capability sheet: {workflow} names unknown action {action!r}")
        for item in spec.get("produces") or []:
            raw_items.append(("produces", action, workflow, item))
        for item in spec.get("near_misses") or []:
            raw_items.append(("near_miss", action, workflow, item))
    by_id: dict[str, dict] = {}
    for _, _, _, item in raw_items:
        key = item.get("id")
        if not key or key in by_id:
            raise ValueError(f"capability sheet: missing or duplicate id {key!r}")
        by_id[key] = item
    entries: dict[str, SheetEntry] = {}
    for kind, action, workflow, item in raw_items:
        resolved = _resolve(item, by_id)
        text = resolved.get("result") if kind == "produces" else resolved.get("result_asked")
        level = resolved.get("level", "direct") if kind == "produces" else None
        if not text or not resolved.get("source"):
            raise ValueError(f"capability sheet: {item['id']} needs its text and a source")
        if kind == "produces" and level not in ("direct", "with_step"):
            raise ValueError(f"capability sheet: {item['id']} has unknown level {level!r}")
        if level == "with_step" and not resolved.get("step"):
            raise ValueError(f"capability sheet: with_step entry {item['id']} must name its step")
        if kind != "produces" and not resolved.get("why_not"):
            raise ValueError(f"capability sheet: {item['id']} must say why it is not produced")
        instead = resolved.get("instead_registered")
        if instead is not None and instead not in ACTION_DEFINITIONS:
            raise ValueError(f"capability sheet: {item['id']} names unknown action {instead!r}")
        entries[item["id"]] = SheetEntry(
            id=item["id"], kind=kind, action=action, workflow=workflow, text=" ".join(str(text).split()),
            level=level, step=" ".join(str(resolved.get("step", "")).split()),
            why_not=" ".join(str(resolved.get("why_not", "")).split()),
            reading=" ".join(str(resolved.get("reading", "")).split()),
            instead_registered=instead, source=str(resolved.get("source")), claim=resolved.get("claim"),
        )
        if kind == "registry_wide" and not entries[item["id"]].claim:
            raise ValueError(f"capability sheet: registry-wide entry {item['id']} must name its claim")
    covered = {item.action for item in entries.values() if item.kind == "produces"}
    missing = sorted(set(RUN_ACTIONS) - covered)
    if missing:
        raise ValueError(f"capability sheet: run actions without a produces entry: {missing}")
    return entries


@lru_cache(maxsize=1)
def sheet_entries() -> dict[str, SheetEntry]:
    return load_sheet()


def entry(key: str) -> SheetEntry:
    return sheet_entries()[key]


def produces_ids() -> tuple[str, ...]:
    return tuple(key for key, item in sheet_entries().items() if item.kind == "produces")


def not_produced_ids() -> tuple[str, ...]:
    return tuple(key for key, item in sheet_entries().items() if item.kind != "produces")
