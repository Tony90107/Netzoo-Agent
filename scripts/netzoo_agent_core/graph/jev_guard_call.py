"""The Jev guard (docs/research-log/jev-shadow-2026-10-27/PLAN-FRESH.md). Off by default: NETZOO_JEV_GUARD=shadow
records what it would do, =on applies it.

TypeSafe's Jev decision model reads the request and the registry only -- never the reading or the call -- and picks
one of the four kinds. After the contract veto, a confident Jev CLARIFY or ASK may turn a DO or DECLINE into that
question; nothing else changes. An ASK needs the sentence where the user says they are unsure, picked by Jev from the
request's own sentences (code-cut, so the quote is verbatim); without one the call is left as it came. Jev never makes
a DO or a DECLINE, never picks a workflow and writes no reason. A call that fails leaves the core unchanged.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from concurrent.futures import Future, ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path

import yaml

from ..contracts.core_decision import CoreDecision, FactQuestion
from .context import record_event

__all__ = ["ABOUT_LINES", "KIND_CRITERIA", "apply_jev_guard", "guarded_core", "jev_mode", "request_sentences",
           "start_jev"]

URL = "https://openrouter.ai/api/alpha/decisions"
MODEL = "typesafe/jev-1.13"
THRESHOLD = 0.7
TIMEOUT = 20
WORKFLOWS = Path(__file__).resolve().parents[3] / "workflows"

KIND_INSTRUCTIONS = (
    "Decide what this network-analysis assistant should do with the user's request on its first turn. "
    "It can only run the registered workflows listed in the state. Pick the kind of reply."
)
# The shadow round's wording (jev-shadow-2026-10-27/jev_call.py), unchanged: spec 2026-10-15 section 3.
KIND_CRITERIA = {
    "DO": "The user names the result they want, a registered workflow can produce it as asked, and nothing the "
          "user is unsure about would change that verdict. Unstated settings or files are fine: later input "
          "checks handle them.",
    "ASK": "The wanted result is clear, but one specific unknown would change the verdict (for example which of "
           "two named results they want, whether a file is the right kind, or a count or setting the user says "
           "they are unsure of). Ask only about an unknown the user shows uncertainty about or that decides "
           "whether a workflow can do it.",
    "CLARIFY": "The user does not say what result they want: only a topic or purpose (understand regulation, do "
               "some network analysis, see what we find), or they name workflows without saying the goal. The "
               "goal must be clarified before choosing a workflow.",
    "DECLINE": "The wanted result is clear but cannot be done as asked: no registered workflow produces it, or "
               "the request needs something a workflow's declared inputs, controls or ranges rule out.",
}
SENTENCE_INSTRUCTIONS = (
    "Pick the sentence of the user's request where the user says they are unsure of a fact about their data or "
    "setup that decides whether the request can be done, or which workflow does it. Pick none when no sentence "
    "does."
)
ABOUT_INSTRUCTIONS = "What kind of fact is the user unsure of in that sentence?"
ABOUT_CRITERIA = {
    "which_file": "which of two files, exports or tables they have",
    "data_property": "a property of their data (how values were transformed, value type, sample origin, call origin)",
    "count": "a count such as samples, features or layers",
    "input_exists": "whether an input the result needs exists or was made",
    "which_result": "which of two named results they want",
}
ABOUT_LINES = {
    "which_file": "Which of the files do you have?",
    "data_property": "What is the case for your data on this point?",
    "count": "What is the number?",
    "input_exists": "Do you have this input?",
    "which_result": "Which result do you want?",
}
_KINDS = ("DO", "DECLINE")
_QUESTIONS = ("ASK", "CLARIFY")
_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix="jev")


def jev_mode() -> str:
    mode = os.environ.get("NETZOO_JEV_GUARD", "off").strip().lower()
    return mode if mode in ("shadow", "on") else "off"


@lru_cache(maxsize=1)
def registry_text() -> str:
    lines = []
    for path in sorted(WORKFLOWS.glob("*.yaml")):
        spec = yaml.safe_load(path.read_text())
        cap = spec.get("output_capability") or {}
        controls = []
        for control in spec.get("controls") or []:
            bits = [control["name"], control.get("type", "")]
            if control.get("allowed_values"):
                bits.append("one of " + "/".join(map(str, control["allowed_values"])))
            if control.get("minimum") is not None or control.get("maximum") is not None:
                bits.append(f"range {control.get('minimum')}..{control.get('maximum')}")
            controls.append(" ".join(bit for bit in bits if bit))
        regulators = ("; regulators " + ", ".join(cap["regulator_types"])) if cap.get("regulator_types") else ""
        lines.append(
            f"- {spec['workflow']}: {spec['description'].strip()} Produces {cap.get('artifact_type')} "
            f"({', '.join(cap.get('granularities') or [])}{regulators}). "
            f"Required inputs: {', '.join(spec.get('required_inputs') or [])}. "
            f"Controls: {'; '.join(controls) or 'none'}.")
    return "\n".join(lines)


def request_sentences(task: str) -> list[str]:
    """The request's sentences, verbatim (a quote is always the user's own words)."""
    return [part.strip() for part in re.split(r"(?<=[.?!])\s+", task.strip()) if len(part.strip()) >= 8]


def _decide(state: str, questions: dict) -> dict:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("no_key")
    body = json.dumps({"model": MODEL, "state": state, "questions": questions}).encode()
    url = os.environ.get("NETZOO_JEV_URL", "").strip() or URL  # a test can point it elsewhere (smoke: Jev down)
    request = urllib.request.Request(url, data=body, headers={"Authorization": f"Bearer {key}",
                                                              "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.loads(response.read())


def _read(task: str) -> dict:
    """Jev's kind, and -- when it says ASK -- the sentence and the kind of fact. Raises on any failure."""
    state = f"Registered workflows:\n{registry_text()}\n\nUser request (first turn):\n{task}"
    out = _decide(state, {"kind": {"type": "choice", "instructions": KIND_INSTRUCTIONS, "criteria": KIND_CRITERIA}})
    kind = out["answers"]["kind"]
    read = {"model": out.get("model"), "kind": kind["choice"], "confidence": kind["confidence"],
            "probabilities": kind.get("probabilities"), "cost": (out.get("usage") or {}).get("cost", 0)}
    sentences = request_sentences(task)
    if kind["choice"] == "ASK" and sentences:
        options = {f"s{i}": text for i, text in enumerate(sentences, 1)} | {"none": "no sentence says this"}
        fact = _decide(state, {
            "sentence": {"type": "choice", "instructions": SENTENCE_INSTRUCTIONS, "criteria": options},
            "about": {"type": "choice", "instructions": ABOUT_INSTRUCTIONS, "criteria": ABOUT_CRITERIA}})
        sentence, about = fact["answers"]["sentence"], fact["answers"]["about"]
        read |= {"sentence": options.get(sentence["choice"]) if sentence["choice"] != "none" else None,
                 "sentence_confidence": sentence["confidence"], "about": about["choice"],
                 "cost": read["cost"] + (fact.get("usage") or {}).get("cost", 0)}
    return read


def start_jev(task: str) -> Future | None:
    """Jev's read of the request, started in the background (it needs only the text); None when the guard is off."""
    return None if jev_mode() == "off" else _POOL.submit(_read, task)


def guarded_core(core: CoreDecision, read: dict, clarify) -> tuple[CoreDecision, str]:
    """(the call after the guard, what it did). `clarify` builds the CLARIFY view when needed."""
    if core.kind not in _KINDS:
        return core, "not_acting"
    if read["kind"] not in _QUESTIONS or read["confidence"] < THRESHOLD:
        return core, "agrees_or_unsure"
    evidence = {**core.evidence, "jev_guard": {"kind_before": core.kind, "basis_before": core.basis,
                                               "jev": read["kind"], "confidence": read["confidence"]}}
    if read["kind"] == "CLARIFY":
        try:
            need = clarify()
        except Exception:  # noqa: BLE001 -- no view to show: the call stays as it came
            return core, "clarify_failed"
        return CoreDecision(kind="CLARIFY", basis="jev_goal", clarify=need, evidence=evidence), "clarify"
    sentence = read.get("sentence")
    if not sentence or read.get("sentence_confidence", 0) < THRESHOLD:
        return core, "no_sentence"
    question = (f"Before I go ahead, could you settle this point you mentioned? "
                f"{ABOUT_LINES.get(read.get('about'), '')}").strip()
    fact = FactQuestion(question=question, user_quote=sentence, workflows=list(core.workflows),
                        uncertainty="said_unknown", depends_on=f"jev:{read.get('about') or ''}")
    return CoreDecision(kind="ASK", basis="jev_fact", facts=[fact], workflows=list(core.workflows),
                        evidence=evidence), "ask"


def apply_jev_guard(context, state, decision, core: CoreDecision, user_task: str, pending: Future | None):
    """The call after the guard (shadow: the call as it came, with what the guard would have done recorded)."""
    mode = jev_mode()
    if mode == "off" or pending is None:
        return core
    try:
        read = pending.result(timeout=TIMEOUT * 3)
    except Exception as exc:  # noqa: BLE001 -- any failure leaves the call as it came, and says so
        record_event(context, state, "core.jev_guard", "classify",
                     {"status": f"not_run:{type(exc).__name__}", "mode": mode, "kind_before": core.kind})
        return core

    def clarify():
        from ..interpretation.core_decision import _clarify_need

        return _clarify_need(decision, decision.capability_check, task=user_task)

    after, action = guarded_core(core, read, clarify)
    record_event(context, state, "core.jev_guard", "classify", {
        "status": "checked", "mode": mode, "action": action, "kind_before": core.kind, "basis_before": core.basis,
        "would_have": {"kind": after.kind, "basis": after.basis, "workflows": after.workflows},
        "jev": read})
    return after if mode == "on" else core
