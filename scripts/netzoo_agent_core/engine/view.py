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
    target_field: str | None = None
    """The one input the clarification wizard is asking for right now.

    A terminal reads this out of the rendered prompt text. A UI needs it as
    data: the plan alone cannot say which field is current, because the
    answers collected so far live in the machine, not in the plan.
    """
    choosing_bundle: bool = False
    """True while the answer selects a whole input bundle rather than a field."""
    preflight_correction: bool = False
    """True when the plan failed input validation rather than lacking an input.

    This mode accepts ``field=path`` assignments, which the per-field wizard
    rejects, so a driver must not offer the same form for both.
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
