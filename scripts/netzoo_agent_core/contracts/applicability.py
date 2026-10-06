"""Whether a listed workflow can be applied to the data the request has (plan item 4, Log 380)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from workflow_registry import ActionName

DataKind = Literal["tf_priors", "mirna", "covariates", "second_omics", "mutations", "network"]
DataState = Literal["stated", "ruled_out", "unstated"]

__all__ = ["CandidateApplicability", "DataFact", "DataKind", "DataState"]


class DataFact(BaseModel):
    """One kind of data a workflow needs beyond expression, as the request states it."""

    kind: DataKind
    state: DataState
    quote: str = ""
    source: Literal["model", "binding", "purpose", "routing", "words"] = Field(
        description="Who established the state: the data-facts call, a bound file, the verified design, "
                    "a quoted routing reading, or the request's wording (when nothing else read it).",
    )


class CandidateApplicability(BaseModel):
    """A listed workflow judged against the request's data: never execution authority.

    ``applicable``: every needed kind is stated. ``not_applicable``: a needed
    kind is ruled out. ``insufficient_information``: none is ruled out but one
    is unstated -- the reply asks rather than recommends.
    """

    action: ActionName
    status: Literal["applicable", "not_applicable", "insufficient_information"]
    basis: list[DataFact] = Field(default_factory=list)
