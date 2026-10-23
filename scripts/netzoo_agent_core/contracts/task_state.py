"""Harness repair P3 (spec 2026-10-23, sections 7.2 and 8): what one task keeps across turns.

A task is the request the user opened. Its open questions keep stable ids; an answer is bound to one only in code, when
the reply names exactly one of its options (`engine.task_updates.bind_answers`); and the clarification rounds are counted,
so a third round is never asked (ROUND-P3.md). It is saved beside the session's messages, which compaction may drop, and
it never holds an execution approval.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

__all__ = ["MAX_ROUNDS", "TASK_STATE_VERSION", "PendingQuestion", "TaskFact", "TaskState", "TaskStateError",
           "load_task_state"]

TASK_STATE_VERSION = 1
MAX_ROUNDS = 2
"""Spec 7.2: at most two rounds of scientific clarification (goal or deciding facts) per task."""

Source = Literal["count", "dimension", "agent", "goal"]


class PendingQuestion(BaseModel):
    """A question the task asked (or queued) and has no answer for."""

    model_config = ConfigDict(extra="forbid")
    question_id: str
    source: Source
    what: str = ""
    """The `needed_facts` dimension or count it waits on; the agent's workflows; empty for the goal."""
    question: str
    user_quote: str = ""
    workflows: list[str] = Field(default_factory=list)
    options: dict[str, list[str]] = Field(default_factory=dict)
    """Each answer and the workflows it leads to -- code-owned outcomes (a dimension's values, a count's candidates)."""
    labels: dict[str, str] = Field(default_factory=dict)
    """How the question names each answer ("somatic" -> "somatic mutations")."""
    yes_no: bool = False
    """An agent question: answered yes or no, recorded only (its outcome direction is the model's)."""
    status: Literal["asked", "queued"] = "asked"


class TaskFact(BaseModel):
    """An answer the user gave to one of the task's questions, bound in code."""

    model_config = ConfigDict(extra="forbid")
    question_id: str
    source: Source
    what: str = ""
    question: str
    user_quote: str = ""
    options: dict[str, list[str]] = Field(default_factory=dict)
    labels: dict[str, str] = Field(default_factory=dict)
    value: str
    answer_quote: str
    """The user's reply it was bound from."""
    turn: int
    status: Literal["known", "superseded"] = "known"


class TaskState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = TASK_STATE_VERSION
    task_id: str
    revision: int = 0
    goal: str = ""
    """The request that opened the task, without the follow-up wrapping."""
    pending: list[PendingQuestion] = Field(default_factory=list)
    facts: list[TaskFact] = Field(default_factory=list)
    rounds: int = 0
    """Turns of this task that ended in ASK or CLARIFY."""
    status: Literal["active", "exhausted", "closed"] = "active"
    turns: int = 0

    def known(self) -> list[TaskFact]:
        return [fact for fact in self.facts if fact.status == "known"]

    def waiting(self) -> bool:
        """Whether the task still waits on the user (a session holding it is resumable, never cleaned up)."""
        return self.status != "closed" and bool(self.pending)


class TaskStateError(ValueError):
    """A saved task state this version cannot use: newer than it, or damaged. The session is not resumed with an
    empty one in its place (spec 8: an unknown version is never read as no state)."""


def load_task_state(payload: dict) -> TaskState | None:
    """The task state a session payload holds; None for a session saved before P3."""
    raw = payload.get("task_state")
    if raw is None:
        return None
    version = raw.get("version") if isinstance(raw, dict) else None
    if not isinstance(version, int):
        raise TaskStateError("The session's task state is damaged (no version); it was left as saved.")
    if version > TASK_STATE_VERSION:
        raise TaskStateError(f"The session's task state was saved by a newer NetZoo (version {version}); this one "
                             f"reads version {TASK_STATE_VERSION}. It was left as saved.")
    try:
        return TaskState.model_validate(raw)
    except ValidationError as error:
        raise TaskStateError(f"The session's task state is damaged ({error.error_count()} problems); it was left "
                             "as saved.") from error
