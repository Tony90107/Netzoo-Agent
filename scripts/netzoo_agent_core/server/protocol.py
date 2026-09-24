"""The wire format shared by the daemon, its workers, and any UI client.

Everything that crosses a process or socket boundary is one ``Envelope``
carrying a typed payload.  Nothing here reaches into the agent: the payloads
are ``model_dump()`` of the contracts the CLI already uses, so a client that
understands ``WorkflowPlan`` needs no second schema.
"""

from __future__ import annotations

import hashlib
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..contracts.planning import WorkflowPlan
from ..contracts.state import NextTurnPrompt
from ..trace_contracts import canonical_json

__all__ = [
    "PROTOCOL_VERSION",
    "ClientMessage",
    "Envelope",
    "ServerMessageType",
    "ViewPayload",
    "plan_hash",
]

PROTOCOL_VERSION = 1

ServerMessageType = Literal[
    "ready",
    "view",
    "message",
    "notice",
    "progress",
    "trace",
    "turn_started",
    "turn_finished",
    "usage",
    "error",
    "stopped",
]

ClientMessageType = Literal[
    "answer",
    "approve_execution",
    "decline_execution",
    "cancel",
    "ping",
]


def plan_hash(plan: WorkflowPlan | dict | None) -> str | None:
    """Stable identity for the plan a client is looking at.

    A UI approves execution against the plan card on screen, which may be
    several seconds behind the worker.  Hashing lets the daemon refuse an
    approval aimed at a plan that has since been replaced, instead of running
    something the user never saw.
    """
    if plan is None:
        return None
    payload = plan.model_dump(mode="json") if isinstance(plan, WorkflowPlan) else plan
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


class Envelope(BaseModel):
    """One message in either direction."""

    model_config = ConfigDict(extra="forbid")

    v: int = PROTOCOL_VERSION
    type: str = Field(min_length=1, max_length=40)
    session_id: str = ""
    seq: int = 0
    payload: dict[str, Any] = Field(default_factory=dict)

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, raw: str) -> "Envelope":
        return cls.model_validate_json(raw)


class ClientMessage(BaseModel):
    """A client request, validated before it can reach a worker."""

    model_config = ConfigDict(extra="forbid")

    type: ClientMessageType
    text: str = Field(default="", max_length=100_000)
    plan_hash: str = Field(default="", max_length=64)
    prompt_seq: int | None = Field(default=None, ge=0)

    @classmethod
    def from_envelope(cls, envelope: Envelope) -> "ClientMessage":
        return cls.model_validate({"type": envelope.type, **envelope.payload})


class ViewPayload(BaseModel):
    """Everything a client needs to render the current question.

    A contract rather than a hand-built dict: this is the payload the window
    reads most closely and the one that has grown the most, and each field
    added to it previously had to be mirrored into the TypeScript by hand.
    """

    model_config = ConfigDict(extra="forbid")

    prompt_kind: Literal[
        "main",
        "clarification",
        "input_confirmation",
        "preference_confirmation",
        "execution_confirmation",
    ]
    text: str
    """The exact string the terminal prints, mode prefix included."""
    menu_enabled: bool
    mode: Literal["Planning", "Execute", "Test"]
    plan: WorkflowPlan | None = None
    plan_hash: str | None = None
    next_prompt: NextTurnPrompt | None = None
    target_field: str | None = None
    """The one input the clarification wizard is asking for right now."""
    choosing_bundle: bool = False
    preflight_correction: bool = False
    """True when the plan failed validation; this mode accepts field=path."""
