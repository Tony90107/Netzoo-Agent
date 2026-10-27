"""The overlap read's call (jev-overlap-2026-10-27; moved out of the capability check by the merge plan 2026-10-27).

Off by default: NETZOO_JEV_OVERLAP=shadow records the read, =on applies it. `overlap_reader()` is what the router passes
to `build_capability_check`: None when off (the builder then reads nothing), else a function (task, quote) -> bool that
reads Jev once per state (memo per process; NETZOO_JEV_OVERLAP_CACHE for offline replay), records the read for the
turn's `core.jev_overlap` event, and answers True only when on and Jev found no overlap asked for. Any failure leaves
the check as it was.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from pathlib import Path

from ..interpretation.jev_overlap import CRITERIA, INSTRUCTIONS, doubted, state_text
from ..jev_client import decide

__all__ = ["overlap_doubted", "overlap_mode", "overlap_reader", "take_reads"]

TIMEOUT = 20

_LOCK = threading.Lock()
_MEMO: dict[str, dict] = {}
_READS: dict[str, list[dict]] = {}


def overlap_mode() -> str:
    mode = os.environ.get("NETZOO_JEV_OVERLAP", "off").strip().lower()
    return mode if mode in ("shadow", "on") else "off"


def _cache_path() -> Path | None:
    path = os.environ.get("NETZOO_JEV_OVERLAP_CACHE", "").strip()
    return Path(path) if path else None


def _read(task: str, quote: str) -> dict:
    """Jev's read, memoised per process and (for offline replay) in NETZOO_JEV_OVERLAP_CACHE. Raises on failure."""
    state = state_text(task, quote)
    key = hashlib.sha256(state.encode()).hexdigest()[:20]
    with _LOCK:
        if key in _MEMO:
            return _MEMO[key]
        cache = _cache_path()
        stored = json.loads(cache.read_text()) if cache is not None and cache.exists() else {}
        if key in stored:
            _MEMO[key] = stored[key]
            return stored[key]
    out = decide(state, {"overlap": {"type": "choice", "instructions": INSTRUCTIONS, "criteria": CRITERIA}},
                 timeout=TIMEOUT)
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
    """Whether the result in `quote`, typed several_groups, is doubted and the flag is on (shadow records only)."""
    mode = overlap_mode()
    if mode == "off":
        return False
    try:
        read = _read(task, quote)
    except Exception as error:  # noqa: BLE001 -- Jev down or slow: the check stands as it was
        read = {"error": f"{type(error).__name__}: {error}"[:200]}
    found = doubted(read)
    with _LOCK:
        _READS.setdefault(task, []).append({"quote": quote, "mode": mode, "read": read, "doubted": found,
                                            "applied": found and mode == "on"})
    return found and mode == "on"


def overlap_reader():
    """What the router passes to `build_capability_check`: None when the flag is off."""
    return None if overlap_mode() == "off" else overlap_doubted


def take_reads(task: str) -> list[dict]:
    """The reads made while checking `task`, once (for the turn's `core.jev_overlap` event)."""
    with _LOCK:
        return _READS.pop(task, [])
