"""Harness repair P3 (ROUND-P3.md): a task's state from one turn to the next -- opened, asked, answered, corrected,
closed. Code only: no model reads the reply here.

An answer is bound to an open question only when the reply names exactly one of that question's own options (a
dimension's value or its label, a count's candidate, a choice's words), or, with exactly one question open and it an
agent's yes-or-no question, when the reply starts with yes or no (spec 7.2: after two questions a bare "yes" fills
neither). Everything else stays open for the next reading.
"""

from __future__ import annotations

import hashlib
import re
import uuid

from ..contracts.task_state import PendingQuestion, TaskFact, TaskState
from ..interpretation.task_answers import fold as _fold

__all__ = ["after_turn", "bind_answers", "opened_goal", "question_id", "reply_answers"]

_PREVIOUS = "Previous NetZoo goal: "
_FOLLOW_UP = "\nUser follow-up:"
_YES = frozenset({"yes", "y", "yeah", "yep", "correct", "right", "true"})
_NO = frozenset({"no", "n", "nope", "false"})


def opened_goal(task: str) -> str:
    """The request a task opened with, without the follow-up wrapping ("Previous NetZoo goal: ...")."""
    text = task
    while text.startswith(_PREVIOUS):
        text = text[len(_PREVIOUS):]
    return text.split(_FOLLOW_UP, 1)[0].strip()


def question_id(source: str, what: str, quote: str) -> str:
    return f"{source}:{what}:{hashlib.sha256(_fold(quote).encode()).hexdigest()[:10]}"


def _pending(core: dict) -> list[PendingQuestion]:
    """The questions a turn's ASK or CLARIFY call asked, then the ones it queued (P1 obligations)."""
    from ..interpretation.needed_facts import DIMENSIONS

    found = []
    if core.get("kind") == "CLARIFY":
        clarify = core.get("clarify") or {}
        quote = clarify.get("goal_quote", "")
        found.append(PendingQuestion(question_id=question_id("goal", "", quote), source="goal",
                                     question=clarify.get("question", ""), user_quote=quote,
                                     workflows=list(clarify.get("candidates") or [])))
    for fact in core.get("facts") or []:
        source = "count" if fact.get("by_code") else "dimension" if fact.get("depends_on") else "agent"
        what = fact.get("depends_on") or "+".join(fact.get("workflows") or [])
        dimension = DIMENSIONS.get(fact.get("depends_on") or "") if source == "dimension" else None
        found.append(PendingQuestion(
            question_id=question_id(source, what, fact.get("user_quote", "")), source=source, what=what,
            question=fact.get("question", ""), user_quote=fact.get("user_quote", ""),
            workflows=list(fact.get("workflows") or []),
            options={} if source == "agent" else dict(fact.get("outcomes") or {}),
            labels=dict(dimension[2]) if dimension else {}, yes_no=source == "agent"))
    for item in (core.get("evidence") or {}).get("obligations") or []:
        if item.get("status") == "queued" and not item.get("asked_as"):
            what = item.get("fact_key", "").split(":", 1)[-1].rsplit("@", 1)[0]
            found.append(PendingQuestion(
                question_id=question_id(item["source"], what, item.get("user_quote", "")), source=item["source"],
                what=what, question=item.get("question", ""), user_quote=item.get("user_quote", ""),
                workflows=list(item.get("workflows") or []), yes_no=item["source"] == "agent", status="queued"))
    return list({question.question_id: question for question in found}.values())


def after_turn(state: TaskState | None, result: dict, task: str) -> TaskState | None:
    """The task after a finished turn: its questions and round when it ended in ASK or CLARIFY, closed otherwise.

    A turn with no core call (an execution turn) leaves the task as it was; a closed task is followed by a new one."""
    core = (result.get("decision") or {}).get("core") or {}
    kind = core.get("kind")
    if state is None or state.status == "closed":
        if kind not in ("ASK", "CLARIFY"):
            return state
        state = TaskState(task_id=uuid.uuid4().hex[:8], goal=opened_goal(task))
    if kind is None:
        return state.model_copy(update={"turns": state.turns + 1})
    if kind in ("ASK", "CLARIFY"):
        exhausted = ((core.get("evidence") or {}).get("clarification") or {}).get("status") == "exhausted"
        return state.model_copy(update={
            "pending": _pending(core), "rounds": state.rounds + 1, "status": "exhausted" if exhausted else "active",
            "revision": state.revision + 1, "turns": state.turns + 1})
    return state.model_copy(update={"pending": [], "status": "closed", "revision": state.revision + 1,
                                    "turns": state.turns + 1})


def _named(question, text: str) -> list[str]:
    """The options of a question (or a fact's question) the folded reply names, by its value or its label."""
    found = []
    for value in question.options:
        names = {_fold(value), _fold(question.labels.get(value, ""))} - {""}
        # A whole word or number: "0.5" never names 5, but a sentence's full stop ends the word ("Somatic. Also ...").
        if any(re.search(rf"(?<!\w)(?<!\w\.){re.escape(name)}(?!\w|\.\w)", text) for name in names):
            found.append(value)
    return found


def bind_answers(state: TaskState | None, reply: str) -> tuple[TaskState | None, list[TaskFact], bool]:
    """The task with the answers the reply gives in code, the facts bound, and whether one corrected a known one."""
    if state is None or state.status == "closed":
        return state, [], False
    text = _fold(reply)
    named = {question.question_id: _named(question, text) for question in state.pending if question.options}
    counts: dict[str, int] = {}
    for values in named.values():
        for value in values:
            counts[_fold(value)] = counts.get(_fold(value), 0) + 1
    picks = {qid: values[0] for qid, values in named.items()
             if len(values) == 1 and counts[_fold(values[0])] == 1}  # a word naming options of two questions binds neither
    asked = [question for question in state.pending if question.status == "asked"]
    first = text.split(" ", 1)[0].rstrip(".") if text else ""
    if not picks and len(asked) == 1 and asked[0].yes_no and first in _YES | _NO:
        picks = {asked[0].question_id: "yes" if first in _YES else "no"}
    turn = state.turns
    bound = [TaskFact(question_id=question.question_id, source=question.source, what=question.what,
                      question=question.question, user_quote=question.user_quote, options=question.options,
                      labels=question.labels, value=picks[question.question_id], answer_quote=reply.strip(), turn=turn)
             for question in state.pending if question.question_id in picks]
    facts, corrected = list(state.facts), False
    taken = {_fold(value) for value in picks.values()}
    for index, fact in enumerate(facts):
        if fact.status != "known" or not fact.options:
            continue
        values = [value for value in _named(fact, text) if _fold(value) not in taken]
        if len(values) == 1 and values[0] != fact.value:  # a correction: the earlier answer is superseded, kept
            facts[index] = fact.model_copy(update={"status": "superseded"})
            bound.append(fact.model_copy(update={"value": values[0], "answer_quote": reply.strip(), "turn": turn}))
            corrected = True
    if not bound:
        return state, [], False
    return state.model_copy(update={
        "pending": [question for question in state.pending if question.question_id not in picks],
        "facts": [*facts, *bound], "revision": state.revision + 1}), bound, corrected


def reply_answers(state, recorder, answer: str, intent: str) -> list[TaskFact]:
    """The open task's questions a follow-up reply answers, bound into the conversation state (`ConversationState`).

    A new goal closes the task, so nothing it asked is carried over; a corrected answer voids the preview and any plan
    made under the earlier one (spec 8.1)."""
    if intent == "new_goal":
        state.task_state = None
        return []
    state.task_state, bound, corrected = bind_answers(state.task_state, answer)
    if bound:
        recorder.append(state.run_id, "task.answers_bound", "cli", {
            "task_id": state.task_state.task_id, "corrected": corrected,
            "facts": [[fact.question_id, fact.value] for fact in bound]})
    if corrected:
        state.clear_preview()
        state.pending_plan = None
    return bound
