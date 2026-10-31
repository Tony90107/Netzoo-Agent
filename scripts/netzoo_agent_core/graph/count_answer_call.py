"""The answer turn of a yes/no question about a sample minimum (docs/research-log/count-answers-2026-10-31).

The agent-answer step leaves a quoted count rule to code (`answer_anchor`: counts are judged in code through the count
question), so when the fact agent asks the count as yes/no -- "Will you have at least three usable biopsies?" -- the
bound answer had no step that used it (the user's app test: a "No" still ended DO on LIONESS-COEXPRESSION and BONOBO).
Here code uses it: the question quotes an input check with `limit: min_samples` of one of its workflows and names
that minimum; a "No" means the count is below it, and each workflow of the call is judged with today's count rule
(`workflow_conditions.data_issue`). "Yes", or anything else, changes nothing.

Off by default: NETZOO_COUNT_ANSWERS=shadow records `core.count_answer`, =on applies it.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

__all__ = ["answered_count_question", "apply_count_answer", "count_answer_mode", "counted_core"]

WORKFLOWS = Path(__file__).resolve().parents[3] / "workflows"
NUMBERS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}


def count_answer_mode() -> str:
    mode = os.environ.get("NETZOO_COUNT_ANSWERS", "off").strip().lower()
    return mode if mode in ("shadow", "on") else "off"


def _fold(text: str) -> str:
    return " ".join(str(text).casefold().split()).rstrip(". ")


@lru_cache(maxsize=1)
def _minimum_checks() -> dict[str, list[str]]:
    """Per workflow: the verbatim text of its input checks whose limit is `min_samples`."""
    import yaml

    found: dict[str, list[str]] = {}
    for path in sorted(WORKFLOWS.glob("*.yaml")):
        spec = yaml.safe_load(path.read_text())
        found[spec["workflow"]] = [check["text"].strip() for check in spec.get("input_checks") or []
                                   if check.get("limit") == "min_samples" and check.get("text")]
    return found


def _names_number(question: str, number: int) -> bool:
    words = re.findall(r"[a-z]+|\d+", question.casefold())
    return any(word == str(number) or NUMBERS.get(word) == number for word in words)


def answered_count_question(task_state) -> dict | None:
    """The yes/no agent question about a sample minimum answered (bound in code) this turn, or None."""
    from ..workflow_conditions import conditions_for

    state = task_state or {}
    for item in state.get("facts") or []:
        labels = item.get("labels") or {}
        if (item.get("source") != "agent" or item.get("turn") != state.get("turns") or item.get("status", "known") != "known"
                or item.get("value") not in ("yes", "no") or not labels.get("contract")):
            continue
        quoted = _fold(labels["contract"])
        for workflow in [labels.get("workflow"), *(item.get("workflows") or [])]:
            conditions = conditions_for(workflow) if workflow else None
            if conditions is None or conditions.min_samples is None:
                continue
            check = next((text for text in _minimum_checks().get(conditions.workflow, []) if _fold(text) in quoted), None)
            if check and _names_number(item.get("question", ""), conditions.min_samples):
                return {**item, "workflow": conditions.workflow, "minimum": conditions.min_samples, "check": check}
    return None


def counted_core(core, question: dict):
    """(the call, action): a "No" rules out each workflow whose own minimum the count fails."""
    from ..contracts.core_decision import CoreDecision, DeclinedPart
    from ..workflow_conditions import conditions_for, data_issue

    if core.kind != "DO":
        return core, "not_do"
    if question["value"] != "no":
        return core, "answer_yes"
    below = question["minimum"] - 1
    ruled = [w for w in core.workflows if (c := conditions_for(w)) is not None and data_issue(c, below, None)]
    left = [w for w in core.workflows if w not in ruled]
    if not ruled:
        return core, "none_ruled_out"
    record = {"kind_before": core.kind, "basis_before": core.basis, "workflow": question["workflow"],
              "minimum": question["minimum"], "ruled_out": ruled, "left": left}
    if left:
        return core.model_copy(update={"workflows": left,
                                       "evidence": {**core.evidence, "count_answer": record}}), "narrowed"
    workflow, answer = question["workflow"], (question.get("answer_quote") or "No").strip()
    line = (f'You answered "{answer}" to "{question.get("question", "").strip()}". {workflow}\'s contract: '
            f'"{question["check"].rstrip(".")}". So {workflow} cannot do this as you asked.')
    return CoreDecision(kind="DECLINE", basis="count_answer", evidence={**core.evidence, "count_answer": record},
                        declined=[DeclinedPart(quote=answer, reasons=[line], line=line)]), "declined"


def apply_count_answer(context, state, core, user_task: str):
    """The call after a sample-minimum answer (shadow: as it came, with what it would have done recorded)."""
    from .context import record_event

    mode = count_answer_mode()
    question = answered_count_question(state.get("task_state")) if mode != "off" else None
    if question is None:
        return core
    after, action = counted_core(core, question)
    record_event(context, state, "core.count_answer", "classify", {
        "mode": mode, "action": action, "kind_before": core.kind, "basis_before": core.basis,
        "would_have": {"kind": after.kind, "basis": after.basis, "workflows": list(after.workflows)},
        "workflow": question["workflow"], "minimum": question["minimum"], "value": question["value"]})
    return after if mode == "on" else core
