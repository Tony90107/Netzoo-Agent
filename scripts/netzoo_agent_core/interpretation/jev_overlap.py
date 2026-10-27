"""Jev's second read of overlapping group membership (docs/research-log/jev-overlap-2026-10-27/ROUND.md).

Off by default: NETZOO_JEV_OVERLAP=shadow records the read, =on applies it.

The capability check rules a grouping result out when its reading types `group_membership=several_groups` (each item
in several groups at once; no registered workflow gives that). gpt-4o-mini types plain subtyping and community requests
that way ("2 to 5 subtypes", "groups of factors and the genes they share"), and the refusal then says no workflow
returns overlapping memberships -- a reason the user never gave. Jev reads the user's words once, on a closed menu;
when it confidently finds no overlap asked for, the result waits on a `group_membership` question with the two
options instead of being refused. Jev never makes a DO or a DECLINE, never picks a workflow and writes no reason; a
call that fails leaves the check as it was.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import urllib.request
from pathlib import Path

__all__ = ["CRITERIA", "INSTRUCTIONS", "THRESHOLD", "overlap_doubted", "overlap_mode", "take_reads"]

# Frozen with the stability check (jev-overlap-2026-10-27/overlap_q.py); never reworded after a run.
INSTRUCTIONS = ("The user asks for groups (communities, modules, subtypes or clusters). Does the request say that one "
                "item (a gene, regulator or sample) may belong to more than one group at the same time?")
CRITERIA = {
    "overlapping": "Yes: the request says an item may belong to several groups at once, or asks for a membership "
                   "strength or degree in each group.",
    "one_each": "No: the request says each item belongs to exactly one group.",
    "not_stated": "The request does not say whether an item can belong to more than one group.",
}
URL = "https://openrouter.ai/api/alpha/decisions"
MODEL = "typesafe/jev-1.13"
TIMEOUT = 20
THRESHOLD = 0.3
"""Doubted when P(overlapping) is at most this (stability: controls 1.0; misreads 0 to 0.05)."""

_LOCK = threading.Lock()
_MEMO: dict[str, dict] = {}
_READS: dict[str, list[dict]] = {}


def overlap_mode() -> str:
    mode = os.environ.get("NETZOO_JEV_OVERLAP", "off").strip().lower()
    return mode if mode in ("shadow", "on") else "off"


def _state(task: str, quote: str) -> str:
    return f"User request:\n{task}\n\nThe part that asks for groups:\n{quote}"


def _cache_path() -> Path | None:
    path = os.environ.get("NETZOO_JEV_OVERLAP_CACHE", "").strip()
    return Path(path) if path else None


def _decide(state: str, questions: dict) -> dict:
    """One Jev decisions call, as `graph.jev_guard_call._decide` makes it (kept here: interpretation never imports graph)."""
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("no_key")
    body = json.dumps({"model": MODEL, "state": state, "questions": questions}).encode()
    url = os.environ.get("NETZOO_JEV_URL", "").strip() or URL
    request = urllib.request.Request(url, data=body, headers={"Authorization": f"Bearer {key}",
                                                              "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.loads(response.read())


def _read(task: str, quote: str) -> dict:
    """Jev's read, memoised per process and (for offline replay) in NETZOO_JEV_OVERLAP_CACHE. Raises on failure."""
    state = _state(task, quote)
    key = hashlib.sha256(state.encode()).hexdigest()[:20]
    with _LOCK:
        if key in _MEMO:
            return _MEMO[key]
        cache = _cache_path()
        stored = json.loads(cache.read_text()) if cache is not None and cache.exists() else {}
        if key in stored:
            _MEMO[key] = stored[key]
            return stored[key]
    out = _decide(state, {"overlap": {"type": "choice", "instructions": INSTRUCTIONS, "criteria": CRITERIA}})
    answer = out["answers"]["overlap"]
    read = {"model": out.get("model"), "choice": answer["choice"], "confidence": answer["confidence"],
            "probabilities": answer.get("probabilities") or {}, "cost": (out.get("usage") or {}).get("cost", 0)}
    with _LOCK:
        _MEMO[key] = read
        if cache is not None:
            stored = json.loads(cache.read_text()) if cache.exists() else {}
            cache.write_text(json.dumps({**stored, key: read}, indent=1))
    return read


def overlap_doubted(task: str, quote: str) -> bool:
    """Whether the result in `quote`, typed several_groups and refused by that form alone, waits on the question."""
    mode = overlap_mode()
    if mode == "off":
        return False
    try:
        read = _read(task, quote)
    except Exception as error:  # noqa: BLE001 -- Jev down or slow: the check stands as it was
        read = {"error": f"{type(error).__name__}: {error}"[:200]}
    p_overlap = (read.get("probabilities") or {}).get("overlapping")
    if p_overlap is None and "choice" in read:
        p_overlap = read["confidence"] if read["choice"] == "overlapping" else 1 - read["confidence"]
    doubted = "error" not in read and p_overlap is not None and p_overlap <= THRESHOLD
    with _LOCK:
        _READS.setdefault(task, []).append({"quote": quote, "mode": mode, "read": read, "doubted": doubted,
                                            "applied": doubted and mode == "on"})
    return doubted and mode == "on"


def take_reads(task: str) -> list[dict]:
    """The reads made while checking `task`, once (for the turn's `core.jev_overlap` event)."""
    with _LOCK:
        return _READS.pop(task, [])
