"""A fact-agent question on a doubt the task has already answered (docs/research-log/no-reask-2026-11-01): the pure
part.

count-answers live P4 r3 asked "Will you have at least three matched samples?" again after "Yes"; P3 r2 asked "Do you
have at least three tumour samples?" after the count question was answered "2". The fact agent proposes the doubt
again on the same user words, and nothing compares its questions with the answers the task holds (the fact key, the
words' place in the request, moves when the follow-up wraps the request). Only an answer to an agent or count question
blocks: a form answer (one group each, regulators to genes) settles a different thing than a question on the same
sentence may ask (j6 X06).
"""
from __future__ import annotations

from .task_answers import _overlap, _state

__all__ = ["RULE", "answered_doubt", "split_answered"]

RULE = "R9 answered"
BLOCKING = ("agent", "count")


def answered_doubt(question, task_state):
    """The known agent or count answer whose user words overlap this question's, or None."""
    state = _state(task_state)
    quote = getattr(question, "user_quote", "") or ""
    if state is None or not quote.strip():
        return None
    return next((fact for fact in state.known() if fact.source in BLOCKING and _overlap(quote, fact.user_quote)), None)


def split_answered(questions, task_state) -> tuple[list, list[tuple]]:
    """(the questions to keep, [(a blocked question, the answer that blocks it)])."""
    kept, blocked = [], []
    for question in questions:
        fact = answered_doubt(question, task_state)
        if fact is None:
            kept.append(question)
        else:
            blocked.append((question, fact))
    return kept, blocked
