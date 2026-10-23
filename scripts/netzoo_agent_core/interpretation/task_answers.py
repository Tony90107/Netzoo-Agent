"""Harness repair P3 (ROUND-P3.md): what a task's answers and rounds do in the next turn, in code.

- A wait on a `needs_fact` dimension or a candidate count the user answered is settled by that answer through its own
  code-owned outcomes: the row is given by the workflows the answer leads to, or not available with the answer as its
  reason. It is never asked again. Agent questions are only recorded: what their yes or no leads to is the model's
  writing (ask_facts open item 1), so the next reading decides with the reply in its words.
- After two rounds of clarification (spec 7.2) an ASK or CLARIFY is marked exhausted: it keeps its kind and says what is
  missing, but no longer asks; nothing is declined or run for it.
"""

from __future__ import annotations

import re

from ..contracts.capability_check import full_gap
from ..contracts.task_state import MAX_ROUNDS, TaskState

__all__ = ["EXHAUSTED_NOTE", "answered_check", "clarification_rounds", "exhausted", "fold"]

EXHAUSTED_NOTE = ("I have asked about this request twice already, so I will not ask again. Below is what is still "
                  "missing; tell me when you know it, or describe a new request. Nothing was ruled out for this, and "
                  "nothing runs until then.")


def fold(text: str) -> str:
    """Words compared across turns: case, underscores, punctuation and thousands commas set aside."""
    text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", (text or "").casefold().replace("_", " "))
    return " ".join(re.sub(r"[^\w.+-]+", " ", text).split()).strip(" .")


def _state(task_state) -> TaskState | None:
    if task_state is None or isinstance(task_state, TaskState):
        return task_state
    return TaskState.model_validate(task_state)


def _overlap(a: str, b: str) -> bool:
    a, b = fold(a), fold(b)
    return bool(a and b) and (a in b or b in a)


def answered_check(check, task_state):
    """The check with each wait a known answer settles resolved by that answer's own outcome."""
    state = _state(task_state)
    if check is None or state is None:
        return check
    from ..capability_sheet import entry
    from .capability_check import _status

    facts = [fact for fact in state.known() if fact.source in ("count", "dimension")]
    rows, changed = [], False
    for row in check.requirements:
        fact = next((fact for fact in facts if row.status == "needs_fact" and fact.what == (row.depends_on or "")
                     and (fact.source == "count") == row.by_code and fact.value in row.outcomes
                     and _overlap(row.unknown_quote, fact.user_quote)), None)
        if fact is not None:
            keys = list(row.outcomes[fact.value])
            label = fact.labels.get(fact.value) or fact.value
            names = list(dict.fromkeys(entry(key).workflow for found in row.outcomes.values() for key in found))
            row = row.model_copy(update={"status": _status(keys), "delivered_by": keys} if keys else {
                "status": "not_available", "delivered_by": [],
                "limits": [*row.limits, f'You answered "{fact.answer_quote}" to "{fact.question}": with {label}, '
                                        f"none of the workflows matched to this result ({', '.join(names)}) gives it"]})
            changed = True
        rows.append(row)
    if not changed:
        return check
    results = [row for row in rows if row.kind == "result"]
    return check.model_copy(update={"requirements": rows, "full_gap": full_gap(results, check.unchecked)})


def clarification_rounds(core, task_state):
    """The call, marked exhausted when the task already asked its two rounds and would ask again."""
    state = _state(task_state)
    if state is None or state.status == "closed" or core.kind not in ("ASK", "CLARIFY") or state.rounds < MAX_ROUNDS:
        return core
    return core.model_copy(update={"evidence": {**core.evidence,
                                                "clarification": {"rounds": state.rounds, "status": "exhausted"}}})


def exhausted(core) -> bool:
    return bool(core is not None and (core.evidence.get("clarification") or {}).get("status") == "exhausted")
