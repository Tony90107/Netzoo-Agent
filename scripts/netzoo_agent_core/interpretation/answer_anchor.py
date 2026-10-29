"""Whether a contract line an agent question quoted can decide the user's answer (docs/research-log/
agent-answer-anchor-2026-10-29): the pure part.

R01 (`jev-agent-answers-2026-10-28`, withdrawn) judged the reply against whatever line the question quoted, and j4 S15's
line was `lambda1`'s setting text, unrelated to "We'll keep 300 genes" -> a wrong refusal. The line is the model's
choice, so code first checks it: verbatim in the workflow's contract, not a count rule (counts are judged in code),
and naming a required input (by its identifier or the identifier's stem) or a boolean control a capability-sheet
expectation ties to a value. Only then may Jev's reading of the answer against it decide anything.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

__all__ = ["anchored"]

WORKFLOWS = Path(__file__).resolve().parents[3] / "workflows"


def _fold(text: str) -> str:
    return " ".join(str(text).casefold().split()).rstrip(". ")


def _strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [found for item in value.values() for found in _strings(item)]
    if isinstance(value, list):
        return [found for item in value for found in _strings(item)]
    return []


@lru_cache(maxsize=1)
def _contracts() -> dict[str, dict]:
    """Per workflow: its contract text (folded), count-rule lines, required-input names and tied controls."""
    from workflow_registry import ACTION_DEFINITIONS

    from .expects import expectations

    found = {}
    for path in sorted(WORKFLOWS.glob("*.yaml")):
        spec = yaml.safe_load(path.read_text())
        action = ACTION_DEFINITIONS.get(spec.get("action"))
        if action is None:
            continue
        inputs = [name for name in (*action.required_inputs, *(n for group in action.required_input_groups for n in group))
                  if "output" not in name]  # an output folder is no input (`lioness_output`)
        names = {name: {name.casefold(), name.split("_")[0].casefold()} for name in inputs}
        counts = {_fold(check["text"]) for check in spec.get("input_checks") or [] if check.get("limit")}
        counts |= {_fold(step) for step in spec.get("validation_steps") or [] if " " in str(step)}
        tied = {item.control for item in expectations(spec["action"]) if item.control is not None}
        controls = {control.name.casefold(): _fold(control.description or "")
                    for control in action.controls if control.name in tied}
        found[spec["workflow"]] = {"text": _fold(" ".join(_strings(spec))), "counts": counts, "inputs": names,
                                   "controls": controls}
    return found


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", text.casefold()))


def anchored(contract: str, workflows) -> str | None:
    """The workflow whose contract the line anchors as a decidable condition, or None (`answer_anchor` doc)."""
    line = _fold(contract)
    if not line:
        return None
    for workflow in workflows or ():
        found = _contracts().get(workflow)
        if found is None or line not in found["text"] or any(line in rule or rule in line for rule in found["counts"]):
            continue
        words = _words(line)
        if any(names & words for names in found["inputs"].values()):
            return workflow
        if any(name in words or (described and described == line) for name, described in found["controls"].items()):
            return workflow
    return None
