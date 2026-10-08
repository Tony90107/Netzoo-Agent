"""The capability check: what the request asks for, and which sheet entry gives it (Log 387).

Log 385: routing quoted the wanted result correctly 42 times in 45, then had
to name it with the nearest artifact of a vocabulary that has no "none of
these", so pseudotime, splicing and spatial deconvolution became TF networks.
Here the model reads the request sentence by sentence, quotes each thing it
asks for, and lists the capability-sheet entries that give it -- an empty list
is a normal answer. Entry ids are enums of the sheet, so none can be invented;
quotes and sentence coverage are checked in code
(`interpretation.capability_check`).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, create_model

from ..capability_sheet import not_produced_ids, produces_ids
from .strict_schema import strict_json_schema

__all__ = ["CapabilityCheck", "CheckedRequirement", "MAX_SENTENCES", "RequirementKind", "proposal_model",
           "proposal_sentences"]

RequirementKind = Literal["result", "about_methods", "context"]


MAX_SENTENCES = 12
"""Sentences after the twelfth are not read; the coverage check lists them as not checked."""


@lru_cache(maxsize=MAX_SENTENCES + 1)
def proposal_model(sentences: int = 1) -> type[BaseModel]:
    """The provider-facing schema: one required field per request sentence, sheet ids as enums.

    Log 387 smoke run: with one free-length list of sentences gpt-4o-mini returned
    only the first (the data sentence) 3 times in 4, so the goal was never read.
    Strict mode requires every property, so a field per sentence cannot be skipped.
    """
    produces = Literal[produces_ids()]  # type: ignore[valid-type]
    not_produced = Literal[not_produced_ids()]  # type: ignore[valid-type]
    requirement = create_model(
        "RequirementReading",
        __config__=ConfigDict(extra="forbid"),
        quote=(str, Field(description="Exact contiguous words from the sentence, copied without translation.")),
        kind=(RequirementKind, Field(description=(
            "result: something the user wants produced or answered about their data or biology. "
            "about_methods: a question about the methods themselves (which to use, how one works, what it "
            "needs). context: what the user has, did or must respect."))),
        delivered_by=(list[produces], Field(description=(
            "For a result: the PRODUCES entries whose result gives what the quote asks for, as asked. Empty "
            "when none does; empty for about_methods and context."))),
        not_by=(list[not_produced], Field(description=(
            "For a result: NOT PRODUCED entries that describe what the quote asks for; may be empty."))),
    )
    fields = {
        f"s{index}": (list[requirement], Field(description=(
            f"Everything sentence {index} of the request says, one item per thing.")))
        for index in range(1, max(1, min(sentences, MAX_SENTENCES)) + 1)
    }
    model = create_model("CapabilityCheckProposal", __config__=ConfigDict(extra="forbid"), **fields)
    model.model_json_schema = classmethod(  # type: ignore[method-assign]
        lambda cls, *args, **kwargs: strict_json_schema(BaseModel.model_json_schema.__func__(cls, *args, **kwargs)))
    return model


def proposal_sentences(proposal) -> list[list]:
    """The requirement lists of a proposal, sentence by sentence."""
    return [getattr(proposal, f"s{index}") for index in range(1, len(type(proposal).model_fields) + 1)]


class CheckedRequirement(BaseModel):
    """One verified requirement and what the sheet says about it."""

    model_config = ConfigDict(extra="forbid")
    quote: str
    kind: RequirementKind
    status: Literal["available", "with_step", "not_available", "not_checked"]
    """`not_checked` for about_methods and context; `not_available` when no produces entry gives it."""
    delivered_by: list[str] = Field(default_factory=list)
    not_by: list[str] = Field(default_factory=list)


class CapabilityCheck(BaseModel):
    """The turn's capability check, as the reply and the card read it."""

    model_config = ConfigDict(extra="forbid")
    requirements: list[CheckedRequirement] = Field(default_factory=list)
    unchecked: list[str] = Field(default_factory=list)
    """Request sentences no verified requirement covers (the coverage check)."""
    full_gap: bool = False
    """Every result is not available and every sentence was read: no workflow is the answer."""

    def results(self) -> list[CheckedRequirement]:
        return [item for item in self.requirements if item.kind == "result"]
