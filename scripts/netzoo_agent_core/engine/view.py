"""What the conversation machine asks its driver to do next.

A driver is whatever puts questions to the user: the terminal CLI today, a
desktop UI process later.  The machine never reads input and never decides how
a question is displayed; it only says which question is due, with the exact
text the terminal has always used, and lets the driver render it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..contracts.planning import WorkflowPlan
from ..contracts.state import NextTurnPrompt

__all__ = ["Event", "Prompt", "Stop", "Turn"]


PromptKind = Literal[
    "execution_confirmation",
    "input_confirmation",
    "preference_confirmation",
    "clarification",
    "main",
]


@dataclass(frozen=True, slots=True)
class Prompt:
    """A question the driver must put to the user before the machine advances."""

    kind: PromptKind
    text: str
    menu_enabled: bool
    plan: WorkflowPlan | None = None
    next_prompt: NextTurnPrompt | None = None
    noninteractive_text: str | None = None
    """Text a non-tty driver prints before telling the user to ``--resume``.

    Only set for the prompts a pending plan raises; those are the ones a
    non-interactive terminal cannot answer.
    """


@dataclass(frozen=True, slots=True)
class Turn:
    """A task is queued and needs no further input; run the graph turn."""

    task: str
    execute_once: bool


@dataclass(frozen=True, slots=True)
class Stop:
    """The conversation is over."""

    exit_code: int


@dataclass(frozen=True, slots=True)
class Event:
    """One piece of user-visible output the driver should render."""

    kind: Literal["notice", "message", "blank"]
    text: str = ""
