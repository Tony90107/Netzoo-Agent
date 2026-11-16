"""What one MCP tool call returns about a NetZoo session.

A window reads a stream of envelopes and redraws as they arrive. An MCP client
asks once and reads one answer, so everything a turn produced has to be one
value. ``TurnResult`` is that value. Its ``reply`` is the agent's own text,
unchanged; every other field is copied from the envelope that carried it.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ErrorView",
    "EvidenceView",
    "OptionView",
    "OutputRef",
    "PlanSummary",
    "StepView",
    "TurnResult",
    "TurnStatus",
    "Via",
]

TurnStatus = Literal["waiting_for_user", "running", "stopped", "error"]

Via = Literal[
    "netzoo_ask",
    "netzoo_execute",
    "netzoo_set_mode",
    "netzoo_list_outputs",
    "none",
]
"""The tool that submits an option. ``none`` marks one that cannot be chosen."""


class OptionView(BaseModel):
    """One answer the agent offered, and the tool that sends it."""

    model_config = ConfigDict(extra="forbid")

    label: str
    description: str = ""
    answer: str = ""
    recommended: bool = False
    available: bool = True
    reason: str = ""
    via: Via = "netzoo_ask"
    paths: list[str] = Field(default_factory=list)


class EvidenceView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    status: str
    value: str | None = None
    reason: str = ""


class StepView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str
    purpose: str = ""
    arguments: dict = Field(default_factory=dict)


class PlanSummary(BaseModel):
    """The parts of a ``WorkflowPlan`` a person reviews before approving it."""

    model_config = ConfigDict(extra="forbid")

    workflow: str
    objective: str = ""
    status: str
    question: str | None = None
    missing_inputs: list[str] = Field(default_factory=list)
    evidence: list[EvidenceView] = Field(default_factory=list)
    steps: list[StepView] = Field(default_factory=list)
    input_bundles: list[dict] = Field(default_factory=list)


class OutputRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    """Project-relative, the spelling ``netzoo_list_outputs`` accepts."""
    host_path: str
    """Where a person finds it; equal to the container path when the launcher did not say."""


class ErrorView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error_type: str
    message: str


class TurnResult(BaseModel):
    """Everything one tool call has to say about the session."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    status: TurnStatus
    mode: Literal["Planning", "Execute", "Test", ""] = ""
    reply: str = ""
    """The agent's messages since the last result, verbatim and in order."""
    notices: list[str] = Field(default_factory=list)
    prompt_kind: str | None = None
    question: str | None = None
    """The exact text the terminal would print for the question now open."""
    target_field: str | None = None
    choosing_bundle: bool = False
    preflight_correction: bool = False
    options: list[OptionView] = Field(default_factory=list)
    plan: PlanSummary | None = None
    plan_hash: str | None = None
    previewed: bool = False
    """A plan's command preview has been shown; it is the one ``plan_hash`` names."""
    can_execute: bool = False
    """A previewed plan is waiting and this server may run it."""
    execute_enabled: bool = False
    progress: list[str] = Field(default_factory=list)
    outputs: list[OutputRef] = Field(default_factory=list)
    usage: dict | None = None
    errors: list[ErrorView] = Field(default_factory=list)
    resumed: bool = False
    """This is the first result since the session was reopened from its saved checkpoint."""
