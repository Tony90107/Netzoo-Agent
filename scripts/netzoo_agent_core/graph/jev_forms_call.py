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

__all__ = ["answer_reader", "apply_data_first", "data_first_core", "forms_doubted", "forms_mode", "forms_reader",
           "take_reads"]

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


def data_first_core(core, user_task: str, task_state, check=None):
    """jev-data-first-2026-10-27 (ROUND.md): a call asking only form questions, whose workflows the user's data rules
    out, becomes the guard's data confirm instead -- the question that decides the request comes first (j4 S32).

    Returns (call, action, typed read). The guard's own typed check and `conditioned_core` are used unchanged."""
    from ..interpretation.jev_forms import FORM_DIMENSIONS
    from .jev_guard_call import answered_core, asked_sentences, check_typed_data, condition_answer, conditioned_core

    if core.kind != "ASK" or not core.facts or any(fact.depends_on not in FORM_DIMENSIONS for fact in core.facts):
        return core, "not_form_ask", None
    workflows = list(dict.fromkeys(name for fact in core.facts for names in fact.outcomes.values() for name in names))
    if not workflows:
        return core, "no_workflows", None
    bound = condition_answer(task_state)
    if bound is not None:  # the answer turn of the confirm this step asked: the guard declines only on a DO (its rule)
        if bound["value"] != "yes":
            return core, f"answer_{bound['value']}", None
        after, action = answered_core(core.model_copy(update={"kind": "DO", "workflows": workflows}), bound,
                                      bound.get("answer_quote", ""), {"answer": "fails", "confidence": 1.0, "by": "code"})
        answer = {**after.evidence.get("jev_answer", {}), "kind_before": core.kind, "basis_before": core.basis}
        return after.model_copy(update={"evidence": {**after.evidence, "jev_answer": answer}}), action, None
    typed = (check or check_typed_data)(user_task, workflows)
    after, action = conditioned_core(core.model_copy(update={"kind": "DO", "workflows": workflows}), typed,
                                     asked_sentences(task_state))
    if action != "ask":
        return core, action, typed
    condition = {**after.evidence["jev_condition"], "kind_before": core.kind, "basis_before": core.basis,
                 "form_questions": [fact.depends_on for fact in core.facts]}
    return after.model_copy(update={"evidence": {**after.evidence, "jev_condition": condition}}), "ask", typed


def apply_data_first(context, state, core, user_task: str):
    """The call after the data-first step: only with NETZOO_JEV_FORMS and NETZOO_JEV_GUARD on; any failure leaves it."""
    from .context import record_event
    from .jev_guard_call import jev_mode

    if forms_mode() != "on" or jev_mode() != "on":
        return core
    try:
        after, action, typed = data_first_core(core, user_task, state.get("task_state"))
    except Exception as exc:  # noqa: BLE001 -- Jev down or slow: the form question stands
        record_event(context, state, "core.jev_data_first", "classify", {"action": f"not_run:{type(exc).__name__}"})
        return core
    if action != "not_form_ask":  # "declined": the confirm's yes on its answer turn (ROUND.md amendment)
        record_event(context, state, "core.jev_data_first", "classify", {
            "action": action, "kind_before": core.kind, "basis_before": core.basis,
            "would_have": {"kind": after.kind, "basis": after.basis, "workflows": after.workflows}, "typed": typed})
    return after
