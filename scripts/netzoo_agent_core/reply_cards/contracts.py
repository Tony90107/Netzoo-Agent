"""The structured half of a reply: what it says in brief and what can be chosen.

A reply's full text stays exactly what the renderers write; it is what the
conversation keeps, what the LLM context sees on the next turn, and what every
pinned test reads. A card is derived from the same typed decision beside it,
for display only. It never routes, never grants execution, and every option
it offers resolves through the machine's existing trusted paths.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from workflow_registry import RecommendedAction

__all__ = [
    "MAX_OPTIONS",
    "CardKind",
    "OptionResolution",
    "ReplyCard",
    "ReplyChoices",
    "ReplyOption",
]

CardKind = Literal[
    "method_choice",
    "clarification",
    "reading_choice",
    "hypothesis_choice",
    "capability_gap",
    "workflow_guidance",
    "composition",
    "plan_ready",
    "run_completed",
    "run_failed",
    "unresolved",
    "general",
]

OptionResolution = Literal[
    # Explain the chosen registered workflow for the stated goal; runs nothing.
    "confirm_workflow",
    # Start planning the chosen workflow (input discovery, preview); runs nothing.
    "plan_workflow",
    # Send the answer back through routing together with the previous goal.
    "follow_up",
    # Compare exactly `compare_actions` for the previous goal; runs nothing
    # (Log 302: the answer text alone was re-routed and lost the candidates).
    "compare_workflows",
    # Submit the answer verbatim, as if typed: `/execute`, `new`, `/test`.
    "command",
    # Handled by the window alone, e.g. open the Outputs view.
    "open_outputs",
    # Not selectable: shown so the user knows it exists and why it cannot run.
    "none",
]


class ReplyOption(BaseModel):
    """One thing the user can pick, or a related thing this agent cannot do."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=260)
    answer: str = Field(default="", max_length=600)
    """The text the option submits; also what the transcript shows as the reply."""
    recommended: bool = False
    """Only set when the recommendation rests on something the request stated."""
    badge: Literal["", "Recommended", "Best match"] = ""
    """`Recommended`: grounded in stated study facts. `Best match`: the only option
    whose registered output matches every typed dimension of the request."""
    available: bool = True
    reason: str = Field(default="", max_length=260)
    """Why an unavailable option cannot run here."""
    action: RecommendedAction | None = None
    granularity: Literal["aggregate", "sample_specific"] | None = None
    """The scale a workflow option stands for, when its workflow offers both."""
    resolution: OptionResolution = "follow_up"
    paths: list[str] = Field(default_factory=list, max_length=20)
    """Output paths an `open_outputs` option refers to."""
    compare_actions: list[RecommendedAction] = Field(default_factory=list, max_length=6)
    """The workflows a `compare_workflows` option compares, in card order."""


MAX_OPTIONS = 8
"""The most answers one card question lists."""


class ReplyChoices(BaseModel):
    """A question with ordered answers, the best-supported first."""

    model_config = ConfigDict(extra="forbid")

    header: str = Field(min_length=1, max_length=24)
    question: str = Field(min_length=1, max_length=400)
    options: list[ReplyOption] = Field(min_length=1, max_length=MAX_OPTIONS)
    allow_other: bool = True
    ordering: str = Field(default="", max_length=200)
    """How the options were ordered, said plainly, so the order is never a hidden claim."""


class ReplyCard(BaseModel):
    """Key points of one reply, plus its choices and next steps."""

    model_config = ConfigDict(extra="forbid")

    kind: CardKind
    headline: str = Field(default="", max_length=300)
    """Empty when the reply has no brief form; the full text is then the reply."""
    points: list[str] = Field(default_factory=list, max_length=6)
    choices: ReplyChoices | None = None
    unavailable: list[ReplyOption] = Field(default_factory=list, max_length=8)
    next_steps: list[ReplyOption] = Field(default_factory=list, max_length=6)
    ran_nothing: bool = True
    """False only when this turn ran or previewed a registered workflow."""

    def options(self) -> list[ReplyOption]:
        """Every selectable option, choices first, in display order."""
        picks = list(self.choices.options) if self.choices else []
        return [item for item in (*picks, *self.next_steps) if item.available and item.resolution != "none"]
