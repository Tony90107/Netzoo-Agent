"""Core decision spec, phase 2 (section 6): the facts a request leaves uncertain that decide its call.

The fact agent reads the request beside the contracts of the workflows that may answer it and proposes each fact the
user shows they are unsure of, citing the user's words and the contract's words. Code keeps a proposal only under
rules R1-R6 (`interpretation.fact_check`); the kept ones are the ASK questions. There is no fixed list of facts:
the contracts themselves bound what can be asked.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .core_decision import FactQuestion

Outcome = Literal["supported", "not_supported", "other_workflow"]


class FactProposal(BaseModel):
    """One proposal of the fact agent (its structured output)."""

    model_config = ConfigDict(extra="forbid")
    user_quote: str = Field(description=(
        "Exact words of the request that show the user is unsure of the fact: they say they do not know it, give "
        "two incompatible versions of it, or use words that can be read two ways."))
    uncertainty: Literal["said_unknown", "two_versions", "two_readings"] = Field(description=(
        "said_unknown: the user says they do not know or have not decided it. two_versions: the request gives two "
        "incompatible versions of it. two_readings: the request's own words can be read two ways."))
    workflow: str = Field(description="The listed workflow whose contract makes the fact decide the request.")
    contract_quote: str = Field(description=(
        "Exact words of that workflow's contract, copied as listed, that make the fact decide the request."))
    question: str = Field(description=(
        "One short question to the user whose answer settles the fact; its yes answer leads to the yes outcome."))
    yes_outcome: Outcome = Field(description=(
        "What a yes answer means for the request: supported (the workflow does it), not_supported (no listed "
        "workflow does it as asked), or other_workflow (another listed workflow does it instead)."))
    yes_workflow: str = Field(description="For other_workflow, that workflow; otherwise empty.")
    no_outcome: Outcome = Field(description="What a no answer means, as for yes_outcome.")
    no_workflow: str = Field(description="For other_workflow, that workflow; otherwise empty.")


class FactProposals(BaseModel):
    model_config = ConfigDict(extra="forbid")
    facts: list[FactProposal] = Field(max_length=3, description=(
        "Each fact the request leaves uncertain that decides, by the contracts, whether it can be done or which "
        "workflow does it; empty when there is none -- a normal answer."))


class RejectedFact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rule: str
    proposal: dict


class FactCheck(BaseModel):
    """The turn's fact check, as `decide_core` reads it (code-owned)."""

    model_config = ConfigDict(extra="forbid")
    status: Literal["checked", "not_run", "failed", "blocked"] = "not_run"
    model: str = ""
    candidates: list[str] = Field(default_factory=list)
    accepted: list[FactQuestion] = Field(default_factory=list)
    rejected: list[RejectedFact] = Field(default_factory=list)
    legacy: list[FactQuestion] = Field(default_factory=list)
    """What the fixed `needed_facts` dimensions would have asked this turn -- shadow only while the agent runs."""
