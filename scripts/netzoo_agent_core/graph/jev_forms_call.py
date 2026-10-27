"""The forms read's call (jev-forms-2026-10-27): time_model, spatial and input_network, as `jev_overlap_call` reads
group_membership.

Off by default: NETZOO_JEV_FORMS=shadow records the read, =on applies it. `forms_reader()` is what the router passes to
`build_capability_check`: None when off, else a function (task, quote, attr, options) -> bool that reads Jev once per
state (memo per process; NETZOO_JEV_FORMS_CACHE for offline replay), records the read for the turn's `core.jev_forms`
event, and answers True only when on and Jev put at most the threshold on the ruling-out options. Any failure leaves
the check as it was.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from pathlib import Path

from ..interpretation.jev_forms import QUESTIONS, answer_question, answer_state, answer_value, doubted, state_text
from ..jev_client import decide

__all__ = ["answer_reader", "forms_doubted", "forms_mode", "forms_reader", "take_reads"]

TIMEOUT = 20

_LOCK = threading.Lock()
_MEMO: dict[str, dict] = {}
_READS: dict[str, list[dict]] = {}


def forms_mode() -> str:
    mode = os.environ.get("NETZOO_JEV_FORMS", "off").strip().lower()
    return mode if mode in ("shadow", "on") else "off"


def _cache_path() -> Path | None:
    path = os.environ.get("NETZOO_JEV_FORMS_CACHE", "").strip()
    return Path(path) if path else None


def _read(attr: str, task: str, quote: str) -> dict:
    """Jev's read, memoised per process and (for offline replay) in NETZOO_JEV_FORMS_CACHE. Raises on failure."""
    state = state_text(attr, task, quote)
    key = hashlib.sha256(f"{attr}\n{state}".encode()).hexdigest()[:20]
    with _LOCK:
        if key in _MEMO:
            return _MEMO[key]
        cache = _cache_path()
        stored = json.loads(cache.read_text()) if cache is not None and cache.exists() else {}
        if key in stored:
            _MEMO[key] = stored[key]
            return stored[key]
    question = QUESTIONS[attr]
    out = decide(state, {attr: {"type": "choice", "instructions": question["instructions"],
                                "criteria": question["criteria"]}}, timeout=TIMEOUT)
    answer = out["answers"][attr]
    read = {"model": out.get("model"), "choice": answer["choice"], "confidence": answer["confidence"],
            "probabilities": answer.get("probabilities") or {}, "cost": (out.get("usage") or {}).get("cost", 0)}
    with _LOCK:
        _MEMO[key] = read
        if cache is not None:
            stored = json.loads(cache.read_text()) if cache.exists() else {}
            cache.write_text(json.dumps({**stored, key: read}, indent=1))
    return read


def forms_doubted(task: str, quote: str, attr: str, options: tuple[str, ...]) -> bool:
    """Whether `attr` of the result in `quote` is doubted and the flag is on (shadow records only)."""
    mode = forms_mode()
    if mode == "off":
        return False
    try:
        read = _read(attr, task, quote)
    except Exception as error:  # noqa: BLE001 -- Jev down or slow: the check stands as it was
        read = {"error": f"{type(error).__name__}: {error}"[:200]}
    found = doubted(read, options)
    with _LOCK:
        _READS.setdefault(task, []).append({"quote": quote, "attr": attr, "options": list(options), "mode": mode,
                                            "read": read, "doubted": found, "applied": found and mode == "on"})
    return found and mode == "on"


def forms_reader():
    """What the router passes to `build_capability_check`: None when the flag is off."""
    return None if forms_mode() == "off" else forms_doubted


def take_reads(task: str) -> list[dict]:
    """The reads made while checking `task`, once (for the turn's `core.jev_forms` event)."""
    with _LOCK:
        return _READS.pop(task, [])


def _read_answer(dim: str, question: str, answer: str) -> dict:
    """jev-answers: Jev's read of a natural answer to a form question (memo, offline cache as `_read`). Raises."""
    state = answer_state(question, answer)
    key = hashlib.sha256(f"answer:{dim}\n{state}".encode()).hexdigest()[:20]
    with _LOCK:
        if key in _MEMO:
            return _MEMO[key]
        cache = _cache_path()
        stored = json.loads(cache.read_text()) if cache is not None and cache.exists() else {}
        if key in stored:
            _MEMO[key] = stored[key]
            return stored[key]
    instructions, criteria = answer_question(dim)
    out = decide(state, {dim: {"type": "choice", "instructions": instructions, "criteria": criteria}}, timeout=TIMEOUT)
    answer_read = out["answers"][dim]
    read = {"model": out.get("model"), "choice": answer_read["choice"], "confidence": answer_read["confidence"],
            "probabilities": answer_read.get("probabilities") or {}, "cost": (out.get("usage") or {}).get("cost", 0)}
    with _LOCK:
        _MEMO[key] = read
        if cache is not None:
            stored = json.loads(cache.read_text()) if cache.exists() else {}
            cache.write_text(json.dumps({**stored, key: read}, indent=1))
    return read


def answer_reader():
    """What the engine uses after the code binding: None unless NETZOO_JEV_FORMS is on (shadow reads nothing here).
    The function keeps its reads in `.reads`."""
    if forms_mode() != "on":
        return None
    reads: list[dict] = []

    def read(dim: str, question: str, answer: str) -> str | None:
        try:
            found = _read_answer(dim, question, answer)
        except Exception as error:  # noqa: BLE001 -- Jev down or slow: the question stays open
            found = {"error": f"{type(error).__name__}: {error}"[:200]}
        value = answer_value(dim, found)
        reads.append({"dim": dim, "read": found, "value": value})
        return value
    read.reads = reads  # this reply's reads, for its `task.answers_read` record
    return read
