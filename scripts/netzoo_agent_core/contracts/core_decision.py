"""The turn's core decision (spec docs/superpowers/specs/2026-10-15-core-decision-design.md).

One four-way call per turn -- clarify the goal, ask a deciding fact, decline, or do -- produced by
`interpretation.core_decision.decide_core` and nowhere else. It is written on the decision and in the trace
(`core.decision`). Phase 1 acts on a CLARIFY call (`with_core`, the CLARIFY reply); the other kinds are still
recorded in shadow.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CoreKind = Literal["CLARIFY", "ASK", "DECLINE", "DO", "UNCHECKED"]


class FactQuestion(BaseModel):
    """A fact the user is unsure of whose answer changes the call (spec section 6)."""

    model_config = ConfigDict(extra="forbid")
    question: str
    user_quote: str = ""
    """The request's own words saying the fact is unknown."""
    workflows: list[str] = Field(default_factory=list)
    """The workflows whose call depends on it."""
    contract_quote: str = ""
    """The workflow contract's words that make it matter (empty for a legacy `needed_facts` dimension)."""
    depends_on: str = ""
    """Legacy (phase 0): the `needed_facts.DIMENSIONS` key or `choice` the question came from."""
    outcomes: dict[str, list[str]] = Field(default_factory=dict)
    """Each answer and the workflows it leads to."""
    settled_by_input_check: bool = False
    """Phase 2 R5: the workflow's own input check settles it before a run on the named files; said, never asked."""
    uncertainty: str = ""
    """Phase 2: said_unknown, two_versions or two_readings (the fact agent's reading of the user's words)."""
    if_yes: str = ""
    if_no: str = ""
    """Phase 2: what each answer leads to -- supported, not_supported, or other_workflow:<NAME>."""


class DeclinedPart(BaseModel):
    """A requirement that cannot be done as asked."""

    model_config = ConfigDict(extra="forbid")
    quote: str
    reasons: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    """Workflows offered after the denial, never as the result asked for."""
    line: str = ""
    """Phase 3: the reply line for it, rendered once from the check (the DECLINE view renders from the call alone)."""


class ClarifyNeed(BaseModel):
    """What must be clarified before any workflow is chosen (spec section 5)."""

    model_config = ConfigDict(extra="forbid")
    missing: Literal["result", "data", "both"] = "result"
    candidates: list[str] = Field(default_factory=list)
    """Workflows whose results the reply may list as possible -- never as fitting."""
    inputs: list[str] = Field(default_factory=list)
    """The input artifact types the request states (the candidates are those that take one of them)."""
    question: str = ""
    goal_quote: str = ""
    """The request's words the reading gave for its aim (or for a result no requirement reads)."""


class CoreDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: CoreKind
    partial: bool = False
    """DO only: some requirements are declined; a subset is never run on its own."""
    workflows: list[str] = Field(default_factory=list)
    declined: list[DeclinedPart] = Field(default_factory=list)
    facts: list[FactQuestion] = Field(default_factory=list)
    clarify: ClarifyNeed | None = None
    run_allowed: bool = False
    basis: str = ""
    """The rule of `decide_core` that made the call, for the trace and tests."""
    evidence: dict[str, Any] = Field(default_factory=dict)
