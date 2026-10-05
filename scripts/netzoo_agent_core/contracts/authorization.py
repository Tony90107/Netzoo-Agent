"""What the user's words permit now, recorded apart from which tool fits."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from workflow_registry import ActionName

OperationKind = Literal["run", "transform", "inspect", "retrieve", "acquire", "any"]


class ForbiddenOperation(BaseModel):
    """An operation the request forbids, quoted from the user's own words."""

    kind: OperationKind
    tools: list[str] = Field(
        default_factory=list,
        description="Workflow names that narrow a run ban; empty forbids the whole kind.",
    )
    quote: str


class OperationAuthorization(BaseModel):
    """Code-owned operation authority, never written by a model.

    Capability matching decides which registered tool fits the request; this
    record holds whether the request asks for an operation now and which ones
    it forbids. A ban vetoes execution whoever proposed it; it never adds any.
    """

    requested: list[OperationKind] = Field(default_factory=list)
    forbidden: list[ForbiddenOperation] = Field(default_factory=list)
    explain_only: str | None = Field(
        default=None, description="The quoted explain-only marker, when present.",
    )
    preview_requested: bool = Field(
        default=False,
        description="The request asks for a preview, dry run or plan; a run ban then means not now.",
    )
    blocked_action: ActionName | None = Field(
        default=None, description="The execution this record refused, if any.",
    )

    @property
    def is_empty(self) -> bool:
        return not (self.requested or self.forbidden or self.explain_only)
