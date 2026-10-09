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
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, create_model

from ..capability_sheet import not_produced_ids, produces_ids
from .strict_schema import strict_json_schema

__all__ = ["CapabilityCheck", "CheckedRequirement", "MAX_SENTENCES", "RequirementKind", "proposal_model",
           "proposal_sentences", "second_opinion_model"]

RequirementKind = Literal["result", "about_methods", "context"]
SentenceRole = Literal["background", "asks", "methods_question", "mixed"]


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
    ask = create_model(
        "Ask",
        __config__=ConfigDict(extra="forbid"),
        quote=(str, Field(description="Exact contiguous words from the sentence, copied without translation.")),
        delivered_by=(list[produces], Field(description=(
            "The PRODUCES entries whose result gives what the quote asks for, as asked; empty when none does."))),
        not_by=(list[not_produced], Field(description=(
            "NOT PRODUCED entries that describe what the quote asks for; may be empty."))),
        # Log 388: code checks these against each entry's granularity and layers (Log 387 G5:
        # a per-patient network credited to OTTER, a three-layer network to DRAGON).
        scale=(Literal["per_sample", "whole_cohort", "unstated"], Field(description=(
            "per_sample: one result for each sample, patient or individual. whole_cohort: one result for all "
            "the samples together. unstated: the request does not say."))),
        omics_layers=(int, Field(description=(
            "How many different omics data types the asked-for result must model together; 0 when it is not a "
            "multi-omic result."))),
        # Log 389: typed attributes code compares with each entry (Log 388: per-cell networks
        # credited to LIONESS, lncRNA regulators to PUMA, the sign of regulation to PANDA).
        data_unit=(Literal["bulk_samples", "single_cells", "not_stated"], Field(description=(
            "What each unit of the asked-for result is computed from: bulk samples (tissues, patients, cell "
            "lines), or single cells."))),
        regulator_kinds=(list[Literal["tf", "mirna", "lncrna", "other"]], Field(description=(
            "The kinds of regulators the asked-for result must contain; empty when it is not about regulators."))),
        needs_sign=(bool, Field(description=(
            "Whether the asked-for result must say if a regulator activates or represses its targets."))),
        # Log 394 (Log 390 LN8: communities of a gene-gene co-expression network went to CONDOR).
        input_network=(Literal["regulator_gene", "gene_gene", "other", "none"], Field(description=(
            "The kind of existing network the asked-for result is computed from: regulator_gene (regulators "
            "linked to target genes), gene_gene (e.g. co-expression), other (e.g. protein interactions), "
            "or none when it is not computed from an existing network."))),
    )
    # Log 387 dev round: with a kind beside the entry lists, a data sentence was given
    # 16 not-produced entries. Only an ask can name entries now.
    # Log 387 dev round 2: data sentences ("We have expression from 50 kidney samples ...")
    # were filed as asks. The sentence's role comes first; code drops asks the role rules out.
    sentence = create_model(
        "SentenceReading",
        __config__=ConfigDict(extra="forbid"),
        role=(SentenceRole, Field(description=(
            "background: it only says what the user has, did or must respect. asks: it asks for results. "
            "methods_question: it only asks about the methods. mixed: more than one of these."))),
        has=(list[str], Field(description=(
            "Exact quotes of what the user has, did or must respect (data, samples, constraints)."))),
        about_methods=(list[str], Field(description=(
            "Exact quotes of questions about the methods themselves: which to use, how one works, what it needs."))),
        asks=(list[ask], Field(description=(
            "Each thing the user wants produced or answered about their data or biology, one item per thing."))),
    )
    fields = {
        f"s{index}": (sentence, Field(description=f"Sentence {index} of the request."))
        for index in range(1, max(1, min(sentences, MAX_SENTENCES)) + 1)
    }
    model = create_model("CapabilityCheckProposal", __config__=ConfigDict(extra="forbid"), **fields)
    model.model_json_schema = classmethod(  # type: ignore[method-assign]
        lambda cls, *args, **kwargs: strict_json_schema(BaseModel.model_json_schema.__func__(cls, *args, **kwargs)))
    return model


@lru_cache(maxsize=32)
def second_opinion_model(pairs: int) -> type[BaseModel]:
    """Log 390: one required yes/no per (request words, registered result) pair."""
    fields = {
        f"a{index}": (bool, Field(description=(
            f"Pair {index}: true only if the workflow's results, together, give what the request words ask for.")))
        for index in range(1, pairs + 1)
    }
    model = create_model("SecondOpinion", __config__=ConfigDict(extra="forbid"), **fields)
    model.model_json_schema = classmethod(  # type: ignore[method-assign]
        lambda cls, *args, **kwargs: strict_json_schema(BaseModel.model_json_schema.__func__(cls, *args, **kwargs)))
    return model


def proposal_sentences(proposal) -> list:
    """The sentence readings of a proposal, in order."""
    return [getattr(proposal, f"s{index}") for index in range(1, len(type(proposal).model_fields) + 1)]


class CheckedRequirement(BaseModel):
    """One verified requirement and what the sheet says about it."""

    model_config = ConfigDict(extra="forbid")
    quote: str
    kind: RequirementKind
    status: Literal["available", "with_step", "partial", "not_available", "not_checked"]
    """`not_checked` for about_methods and context; `not_available` when no produces entry gives it;
    `partial` when one reading of the passage names an entry and another names none."""
    delivered_by: list[str] = Field(default_factory=list)
    not_by: list[str] = Field(default_factory=list)
    attrs: dict[str, Any] = Field(default_factory=dict)
    """The ask's typed attributes (scale, layers, data unit, regulators, sign), for the second opinion."""
    blank: bool = False
    """Log 397: no reading named any sheet entry, delivering or not -- a verdict with no reason."""
    second_opinion: bool = False
    """Log 390: credited by the second opinion on a conflict with an exact routing match."""


class CapabilityCheck(BaseModel):
    """The turn's capability check, as the reply and the card read it."""

    model_config = ConfigDict(extra="forbid")
    requirements: list[CheckedRequirement] = Field(default_factory=list)
    unchecked: list[str] = Field(default_factory=list)
    """Request sentences no verified requirement covers (the coverage check)."""
    full_gap: bool = False
    """Every result is not available and every sentence was read: no workflow is the answer."""
    unavailable: bool = False
    """Log 394: the check could not run this turn (its budget spent, or the model failed twice)."""
    cleared: list[str] = Field(default_factory=list)
    """Log 392: the routing candidates a full gap cleared, so an outside-step note tied to one
    of them (ALPACA beside CONDOR) is still said."""

    def results(self) -> list[CheckedRequirement]:
        return [item for item in self.requirements if item.kind == "result"]
