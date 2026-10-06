"""One request's requirements, read once and shared by every stage."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from .authorization import OperationAuthorization

__all__ = ["RequestRequirements", "StatedValue"]


class StatedValue(BaseModel):
    """A value the user stated in their own words (a path, taxon or control)."""

    field: str
    value: Any
    origin: Literal["this_turn", "earlier_turn"] = Field(
        description="earlier_turn: stated in the request this turn continues, carried as typed state.",
    )
    span: tuple[int, int] | None = Field(
        default=None, description="Where the value appears in this turn's full message.",
    )


class RequestRequirements(BaseModel):
    """Code-owned record of what one request asks for and forbids.

    Built once per turn from the full message (never from the bounded routing
    window) plus the typed values a continuation carries from the request it
    continues. Routing, planning, plan evaluation and the next turn read this
    one record instead of re-reading differently cut copies of the text.
    """

    source_sha256: str
    source_chars: int
    routed_chars: int = Field(description="Characters the router and model calls read.")
    omitted_chars: int = Field(
        default=0, description="Characters of the request left out of the routing window.",
    )
    stated: list[StatedValue] = Field(default_factory=list)
    operations: OperationAuthorization
    # Filled after routing; a reading of the request, not the user's words.
    goal: str | None = None
    open_conditions: list[str] = Field(default_factory=list)
    # Plan item 4 (Log 380): the data-facts reading and each listed workflow's
    # applicability to it (applicable / not applicable / insufficient information).
    data_facts: dict[str, str] | None = None
    applicability: list[dict[str, Any]] = Field(default_factory=list)
    # Plan item 5 (Log 383): the turn's data-needs plan.
    data_plan: dict[str, Any] | None = None

    def stated_value(self, field: str) -> Any:
        """The value the user stated for *field*, this turn first."""
        for origin in ("this_turn", "earlier_turn"):
            for item in self.stated:
                if item.field == field and item.origin == origin:
                    return item.value
        return None
