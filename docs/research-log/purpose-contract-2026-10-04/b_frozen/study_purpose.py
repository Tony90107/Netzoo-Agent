"""The study purpose a model proposes for a request, before verification (Log 355).

Log 353: word lists read 100% of the wording they were written for and
little of new wording, for designs and conclusions alike, across four
held-out sets. Log 354: one strict call proposing the design and the
conclusions, each with an exact quote, followed by deterministic
verification (`routing/study_purpose_verify.py`), read 86% of designs and 90%
of conclusions on the same data with no false reading. The proposal is never
used unverified.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .strict_schema import strict_json_schema

__all__ = ["PurposeClaim", "StudyPurposeProposal"]


class PurposeClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim: Literal["group_difference", "individual_change", "regulator_change", "causal", "prediction"]
    text_span: str = Field(description="Exact contiguous quote from the request that states this conclusion.")


class StudyPurposeProposal(BaseModel):
    """How the request's samples relate and what it wants to conclude, as it states them."""

    model_config = ConfigDict(extra="forbid")
    design: Literal["paired", "groups", "none"]
    design_span: str = Field(description="Exact contiguous quote stating the design; empty when design is none.")
    claims: list[PurposeClaim] = Field(max_length=3)

    @classmethod
    def model_json_schema(cls, *args, **kwargs):
        """The provider sees the strict-mode form; validation is unchanged (Log 208)."""
        return strict_json_schema(super().model_json_schema(*args, **kwargs))
