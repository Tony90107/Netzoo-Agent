"""The turn's data-needs plan: what the question needs, what the request has, what the reply asks and says.

Plan item 5 (Log 383). Code-owned; never execution authority.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

__all__ = ["DataNeed", "DataPlan", "NeedKind"]

NeedKind = Literal["tf_priors", "mirna"]


class DataNeed(BaseModel):
    """One kind of data the question needs, as the request states it, and what the reply does about it."""

    kind: NeedKind
    state: Literal["stated", "ruled_out", "unstated"]
    source: Literal["binding", "model", "words"] = Field(
        description="A file the request binds, the data-facts reading (quote verified), or the request's words "
                    "when nothing read it.")
    quote: str = ""
    action: Literal["none", "ask", "say_ruled_out"]


class DataPlan(BaseModel):
    """What this turn's question needs and what the reply must do about it.

    ``answerable``: False when the question asks only for conclusions no
    registered workflow supports (prediction, causation): nothing is asked.
    ``basis``: where the need was read -- the study purpose's quoted
    questions, the routing reading when no question was quoted, or neither.
    """

    answerable: bool
    basis: Literal["claims", "question", "reading", "none", "unanswerable"]
    needs: list[DataNeed] = Field(default_factory=list)

    def asks(self) -> list[NeedKind]:
        return [need.kind for need in self.needs if need.action == "ask"]

    def ruled_out(self) -> list[DataNeed]:
        return [need for need in self.needs if need.action == "say_ruled_out"]
