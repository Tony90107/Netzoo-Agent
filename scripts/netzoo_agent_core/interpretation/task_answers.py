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

__all__ = ["EXHAUSTED_NOTE", "answered_check", "clarification_rounds", "exhausted", "exhausted_body", "fold",
           "settled_quotes", "without_settled"]

EXHAUSTED_NOTE = ("I have asked about this request twice already, so I will not ask again. Below is what is still "
                  "missing; tell me when you know it, or describe a new request. Nothing was ruled out for this, and "
                  "nothing runs until then.")


_ASKING = (("Before I choose a workflow, please tell me:", "Still missing:"),
           ("No workflow has been selected and nothing runs before you answer.", "No workflow has been selected."))


def exhausted_body(content: str) -> str:
    """exhausted-wording-2026-10-28: an ASK body under EXHAUSTED_NOTE says what is missing, never asks it again (j5
    W18 turn 3: "I will not ask again" and then "please tell me" the same question). As the reply that answers
    nothing already does (`engine.task_updates`: "Still missing:")."""
    from .ask_facts import CONFIRM_ASKING  # the guard's data confirm, said as missing too (j4 S35 re-ask)

    for asking, saying in (*_ASKING, *CONFIRM_ASKING):
        content = content.replace(asking, saying)
    return content


def settled_quotes(task_state) -> list[str]:
    """settled-answers-2026-10-29: the reply words of every known form or count answer -- settled in code against the
    contract's typed outcome, so never a new stated condition for the model condition check (j6 X06: "Every TF and
    every gene should end up in exactly one module" bound as one_group, then judged "violates" for CONDOR)."""
    state = _state(task_state)
    return [] if state is None else [fact.answer_quote for fact in state.known()
                                     if fact.source in ("dimension", "count") and fact.answer_quote.strip()]


def without_settled(stated: list[str], task_state) -> list[str]:
    """The stated conditions less those that repeat a settled answer (`settled_quotes`)."""
    settled = settled_quotes(task_state)
    return [quote for quote in stated if not any(_overlap(quote, answer) for answer in settled)]


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


def answered_check(check, task_state, task: str = ""):
    """The check with each wait a known answer settles resolved by that answer's own outcome; a known count answer
    that settled no wait is applied to the request's one credited result (`_applied_counts`)."""
    state = _state(task_state)
    if check is None or state is None:
        return check
    from ..capability_sheet import entry
    from .capability_check import _status
    from .core_decision import form_doubt

    facts = [fact for fact in state.known() if fact.source in ("count", "dimension")]
    rows, changed, settled = [], False, set()
    for row in check.requirements:
        # jev-answers: an answer about a doubted form settles every row waiting on it, whatever words each quotes.
        fact = next((fact for fact in facts if row.status == "needs_fact" and fact.what == (row.depends_on or "")
                     and (fact.source == "count") == row.by_code and fact.value in row.outcomes
                     and (form_doubt(row) or _overlap(row.unknown_quote, fact.user_quote))), None)
        if fact is not None:
            settled.add(fact.question_id)
            keys = list(row.outcomes[fact.value])
            label = fact.labels.get(fact.value) or fact.value
            names = list(dict.fromkeys(entry(key).workflow for found in row.outcomes.values() for key in found))
            row = row.model_copy(update={"status": _status(keys), "delivered_by": keys} if keys else {
                "status": "not_available", "delivered_by": [],
                "limits": [*row.limits, f'You answered "{fact.answer_quote}" to "{fact.question}": with {label}, '
                                        f"none of the workflows matched to this result ({', '.join(names)}) gives it"]})
            changed = True
        rows.append(row)
    rows, applied = _applied_counts(rows, [fact for fact in facts if fact.source == "count"
                                           and fact.question_id not in settled], task)
    if not (changed or applied):
        return check
    results = [row for row in rows if row.kind == "result"]
    return check.model_copy(update={"requirements": rows, "full_gap": full_gap(results, check.unchecked)})


def _applied_counts(rows, facts, task: str):
    """answered-counts-2026-10-29: a count the user answered that settled no wait this turn, applied to the request's
    one credited result -- ad1 j6 X22: "150 or 400 metabolites?" -> "400" bound, but turn 2's re-reading dropped the
    doubt, its row was available with the 400 transcripts alone, and the answer had no wait to settle.

    Features read from inside the doubt's words are replaced by one data type of the answered size; an answered sample
    count replaces the method's. The row is re-fitted and is not available, the answer quoted, when nothing fits.
    Several credited results or a doubt not placed in the request: unchanged."""
    from .method_conditions import method_fitting
    from .request_spans import _span

    credited = [index for index, row in enumerate(rows) if row.kind == "result" and row.delivered_by]
    if len(credited) != 1 or not task:
        return rows, False
    index = credited[0]
    row, applied = rows[index], False
    for fact in facts:
        where = _span(task, fact.user_quote) if fact.user_quote.strip() else None
        if where is None or fact.what not in ("feature_count", "sample_count") or not fact.value.isdigit():
            continue
        value, method = int(fact.value), dict(row.method)
        if fact.what == "sample_count":
            method.update(samples=value, samples_quote=fact.user_quote)
        else:
            items = [item for item in method.get("feature_items", []) if not (where[0] <= item[0] and item[1] <= where[1])]
            items.append([where[0], where[1], value])
            method.update(features=sum(item[2] for item in items), feature_counts=len(items), feature_items=items)
        kept, limits, *_rest = method_fitting(method, list(row.delivered_by))
        update = {"method": method}
        if not kept:
            update.update(status="not_available", delivered_by=[], limits=[
                *row.limits, *limits, f'You answered "{fact.answer_quote}" to "{fact.question}".'])
        row, applied = row.model_copy(update=update), True
    rows = list(rows)
    rows[index] = row
    return rows, applied


def clarification_rounds(core, task_state):
    """The call, marked exhausted when the task already asked its two rounds and would ask again."""
    state = _state(task_state)
    if state is None or state.status == "closed" or core.kind not in ("ASK", "CLARIFY") or state.rounds < MAX_ROUNDS:
        return core
    return core.model_copy(update={"evidence": {**core.evidence,
                                                "clarification": {"rounds": state.rounds, "status": "exhausted"}}})


def exhausted(core) -> bool:
    return bool(core is not None and (core.evidence.get("clarification") or {}).get("status") == "exhausted")
