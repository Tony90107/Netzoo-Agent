"""Code-owned evidence records of the harness repair (spec 2026-10-23-evidence-bound-harness-repair-design, section 5).

P1 records obligations only: each fact a turn still needs, and what the turn did with it. A fact the user is unsure of
leaves a turn asked, covered by an asked question on the same fact, queued past the two-question cap, or settled by a
code judgment -- never because the fact agent answered with an empty list, a proposal was rejected or the cap was
reached (`interpretation.obligations.ask_plan`).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Obligation(BaseModel):
    """One open fact of the turn (spec 5.2), written by `ask_plan` into the core decision's evidence."""

    model_config = ConfigDict(extra="forbid")
    fact_key: str
    """`<source>:<what>@<start>-<end>`: where in the request the user's words for it are (`obligations.fact_key`)."""
    source: Literal["count", "dimension", "agent"]
    """count: a candidate count judged in code; dimension: a `needed_facts` wait; agent: a kept fact-agent question."""
    question: str
    user_quote: str = ""
    workflows: list[str] = Field(default_factory=list)
    status: Literal["asked", "queued", "settled_in_code"]
    """asked this turn; queued past the cap (still open); settled_in_code: the agent's question on a count code
    judged (phase 5b, R8) -- the count's own judgment answers it."""
    asked_as: str = ""
    """The fact key of the asked question it is bound to -- overlapping user words and a shared workflow, from another
    source; empty when it is its own. Code checks only that binding, not that both ask the same thing (P1 audit: 3 of
    33 recorded pairs ask another fact on the same words)."""
