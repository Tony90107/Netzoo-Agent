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

__all__ = ["CONDITIONS", "CapabilityCheck", "CheckedRequirement", "MAX_SENTENCES", "RequirementKind",
           "SecondOpinionAnswer", "conditions_model", "proposal_model", "proposal_sentences", "reread_as_proposal",
           "reread_model", "second_opinion_model", "unstated_conditions"]

RequirementKind = Literal["result", "about_methods", "context"]
SentenceRole = Literal["background", "asks", "methods_question", "mixed"]


MAX_SENTENCES = 12
"""Sentences after the twelfth are not read; the coverage check lists them as not checked."""


@lru_cache(maxsize=1)
def _ask_model() -> type[BaseModel]:
    """One asked-for result and the sheet entries that give it (shared by the check and its re-read)."""
    produces = Literal[produces_ids()]  # type: ignore[valid-type]
    not_produced = Literal[not_produced_ids()]  # type: ignore[valid-type]
    return create_model(
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
        # Log 402, re-applied in Log 403: result forms no registered workflow gives (heldout7 ON5,
        # heldout8 QN5/QN8/QN10, heldout10 SN1/SN5).
        group_membership=(Literal["one_group", "several_groups", "not_about_groups"], Field(description=(
            "When the asked-for result groups genes, regulators or samples: whether each may belong to only one "
            "group or to several groups at once; not_about_groups otherwise."))),
        time_model=(Literal["dynamic", "not_dynamic"], Field(description=(
            "dynamic: the asked-for result must model how the system changes from one time point to the next "
            "(time lags, transitions, trajectories). not_dynamic otherwise, including results compared between or "
            "related to time points, stages or follow-up."))),
        spatial=(Literal["uses_neighbors", "not_spatial"], Field(description=(
            "uses_neighbors: the asked-for result must use where samples sit in space or which are neighbours."))),
        # Log 403 (plan item 2): asking whether a method gives a result is still asking for that result;
        # how it was asked is kept apart from what is asked for.
        asked_as=(Literal["request", "question"], Field(description=(
            "request: the user wants the result produced. question: the user asks whether, or which, method "
            "produces it."))),
    )


CONDITIONS = {
    # field: (values, the value that rules results out, description)
    "data_unit": (("bulk_samples", "single_cells", "not_stated"), "single_cells",
                  "What each sample or profile of the user's data is: bulk samples (tissues, patients, cell lines, or "
                  "cells summed into pseudo-bulk profiles), or single cells."),
    "samples_matched": (("same_samples", "different_samples", "not_stated"), "different_samples",
                        "Whether the user's different omics data types were measured on the same samples."),
    "spatial": (("uses_neighbors", "not_spatial"), "uses_neighbors",
                "uses_neighbors: the results must use where samples sit in space or which are neighbours."),
    "time_model": (("dynamic", "not_dynamic"), "dynamic",
                   "dynamic: the results must model how the system changes from one time point to the next."),
    "group_membership": (("several_groups", "one_group", "not_stated"), "several_groups",
                         "several_groups: a gene, regulator or sample must be allowed in more than one group."),
}
"""Log 412: the conditions a request states outside the sentence of an ask, as typed values.

heldout17 KN1 ("The 80 samples are cells from a single 10x run.") and KN3 ("The two layers were not
measured on the same samples."): the check filed each condition as something the user has, and judged
the ask from its own sentence (data_unit not_stated), so a per-sample co-expression network and a
DRAGON network were credited 4 times in 4. Each condition comes with the words that state it; code
keeps one only when those words are in the request, and applies it to the asks
(`interpretation.capability_check`).
"""


@lru_cache(maxsize=1)
def conditions_model() -> type[BaseModel]:
    fields = {}
    for name, (values, _rules_out, description) in CONDITIONS.items():
        fields[name] = (Literal[values], Field(description=description))  # type: ignore[valid-type]
        fields[f"{name}_quote"] = (str, Field(description=(
            f"The exact words of the request that state {name}; empty when it is not stated.")))
    return create_model("RequestConditions", __config__=ConfigDict(extra="forbid"), **fields)


def unstated_conditions() -> dict:
    """The conditions of a reading that states none (a re-read reads asks only)."""
    return {key: value for name, (values, _rules_out, _description) in CONDITIONS.items()
            for key, value in ((name, values[-1]), (f"{name}_quote", ""))}


@lru_cache(maxsize=MAX_SENTENCES + 1)
def proposal_model(sentences: int = 1) -> type[BaseModel]:
    """The provider-facing schema: one required field per request sentence, sheet ids as enums.

    Log 387 smoke run: with one free-length list of sentences gpt-4o-mini returned
    only the first (the data sentence) 3 times in 4, so the goal was never read.
    Strict mode requires every property, so a field per sentence cannot be skipped.
    """
    ask = _ask_model()
    # Log 387 dev round: with a kind beside the entry lists, a data sentence was given
    # 16 not-produced entries. Only an ask can name entries now.
    # Log 387 dev round 2: data sentences ("We have expression from 50 kidney samples ...")
    # were filed as asks. The sentence's role comes first; code drops asks the role rules out.
    sentence = create_model(
        "SentenceReading",
        __config__=ConfigDict(extra="forbid"),
        role=(SentenceRole, Field(description=(
            "background: it only says what the user has, did or must respect. asks: it asks for results, as a "
            "request or as a question about which method gives them. methods_question: it only asks how a method "
            "works or what it needs, naming no result. mixed: more than one of these."))),
        has=(list[str], Field(description=(
            "Exact quotes of what the user has, did or must respect (data, samples, constraints)."))),
        about_methods=(list[str], Field(description=(
            "Exact quotes of questions about how a method works or what it needs, naming no result."))),
        asks=(list[ask], Field(description=(
            "Each result the user wants produced, or asks whether or which method produces, about their data or "
            "biology; one item per result."))),
    )
    fields = {
        f"s{index}": (sentence, Field(description=f"Sentence {index} of the request."))
        for index in range(1, max(1, min(sentences, MAX_SENTENCES)) + 1)
    }
    # The provider's strict schema still requires it; the default reads recordings and fixtures from before Log 412.
    fields["conditions"] = (conditions_model(), Field(
        default_factory=lambda: conditions_model()(**unstated_conditions()), description=(
        "Conditions the request states anywhere -- in another sentence, or a follow-up to an earlier request -- "
        "about the user's data or about what every asked-for result must satisfy.")))
    model = create_model("CapabilityCheckProposal", __config__=ConfigDict(extra="forbid"), **fields)
    model.model_json_schema = classmethod(  # type: ignore[method-assign]
        lambda cls, *args, **kwargs: strict_json_schema(BaseModel.model_json_schema.__func__(cls, *args, **kwargs)))
    return model


@lru_cache(maxsize=MAX_SENTENCES + 1)
def reread_model(sentences: int = 1) -> type[BaseModel]:
    """Log 406: a second reading of words the check left unread, with only one thing to say about them.

    The check's sentence reading can file a sentence as background or as a question about methods
    (heldout11 VN5q: "Is there a method that models how each TF-gene edge at one time point depends
    on the edges at the previous time point?", 3 of 3), or quote one result of a sentence and
    nothing of the next one in it (heldout13 P1: "uploaded automatically to a public database").
    Asked again with the same choices it chooses the same; here the only field is what results
    the words ask for -- an empty list is a normal answer.
    """
    ask = _ask_model()
    sentence = create_model(
        "SentenceAsks",
        __config__=ConfigDict(extra="forbid"),
        asks=(list[ask], Field(description=(
            "Each result these words ask to be produced, or ask whether or which method produces, about the "
            "user's data or biology; one item per result; empty when they ask for none."))),
    )
    fields = {
        f"s{index}": (sentence, Field(description=f"Passage {index}."))
        for index in range(1, max(1, min(sentences, MAX_SENTENCES)) + 1)
    }
    model = create_model("CapabilityReread", __config__=ConfigDict(extra="forbid"), **fields)
    model.model_json_schema = classmethod(  # type: ignore[method-assign]
        lambda cls, *args, **kwargs: strict_json_schema(BaseModel.model_json_schema.__func__(cls, *args, **kwargs)))
    return model


def reread_as_proposal(reread, conditions=None) -> BaseModel:
    """The re-read in the check's own proposal shape, every passage an `asks` sentence.

    Log 413: it carries the request's conditions as the check read them, so a result the re-read finds is
    held to them too (heldout18 CK6-2: "patient subtypes" re-read beside "A patient should be able to
    belong to two subtypes").
    """
    count = len(type(reread).model_fields)
    return proposal_model(count).model_validate({
        **{f"s{index}": {"role": "asks", "has": [], "about_methods": [],
                         "asks": [item.model_dump() for item in getattr(reread, f"s{index}").asks]}
           for index in range(1, count + 1)},
        "conditions": conditions.model_dump() if conditions is not None else unstated_conditions()})


SecondOpinionAnswer = Literal["all", "part", "none"]


@lru_cache(maxsize=32)
def second_opinion_model(pairs: int) -> type[BaseModel]:
    """Log 390: one required answer per (request words, registered result) pair.

    Log 403 (plan items 2 and 5): "part" -- the words ask for more than one result and the
    workflow gives some of them -- so a request that mixes a doable and an undoable result
    in one quote (heldout8 QP2-QP4: communities, then an interactive 3D view) is partly
    available, not a full gap that drops the doable half.
    """
    fields = {
        f"a{index}": (SecondOpinionAnswer, Field(description=(
            f"Pair {index}: all -- the workflow's results, together, give everything the request words ask for; "
            "part -- the words ask for more than one result and the workflow's results give some of them; "
            "none -- they give none of it.")))
        for index in range(1, pairs + 1)
    }
    model = create_model("SecondOpinion", __config__=ConfigDict(extra="forbid"), **fields)
    model.model_json_schema = classmethod(  # type: ignore[method-assign]
        lambda cls, *args, **kwargs: strict_json_schema(BaseModel.model_json_schema.__func__(cls, *args, **kwargs)))
    return model


def proposal_sentences(proposal) -> list:
    """The sentence readings of a proposal, in order."""
    count = sum(1 for name in type(proposal).model_fields if name[1:].isdigit())
    return [getattr(proposal, f"s{index}") for index in range(1, count + 1)]


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
    asked_as: Literal["request", "question"] = "request"
    """Log 403: whether the user wants it produced or asks whether/which method produces it."""


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
    provisional: bool = False
    """Log 401: only the backup model read the request (the check's own model failed), so what it
    found is reported but never acted on -- a gap it finds does not clear routing (Log 400: all three
    false gaps of heldout9 came from the backup model)."""
    cleared: list[str] = Field(default_factory=list)
    """Log 392: the routing candidates a full gap cleared, so an outside-step note tied to one
    of them (ALPACA beside CONDOR) is still said."""
    conditions: dict[str, str] = Field(default_factory=dict)
    """Log 412: the request-level conditions whose words were found in the request and that rule results out
    (e.g. data_unit single_cells), applied to every ask they concern."""
    gap_unconfirmed: bool = False
    """Log 403: a full gap the second opinion was owed but could not give (its budget spent, or the
    model failed), so, as for the backup model, the gap is reported unconfirmed and clears nothing
    (traces: 11 second opinions blocked by the turn budget on h8-h9, o10, f10)."""

    def results(self) -> list[CheckedRequirement]:
        return [item for item in self.requirements if item.kind == "result"]

    def unconfirmed(self) -> bool:
        """Log 403: nothing this turn's check says was confirmed by the check's own model."""
        return self.unavailable or self.provisional or self.gap_unconfirmed
