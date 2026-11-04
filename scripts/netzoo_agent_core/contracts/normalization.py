"""What a normalization request needs corrected, and how the method was chosen (2026-11-04).

A request often says what is wrong with the data instead of naming a method ("sequenced at very different
depths", "accounts for gene length"). A model reads those needs, each with an exact quote; code keeps only quotes
found in the request and maps the needs to methods (`normalization_request.methods_for_needs`).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .strict_schema import strict_json_schema

__all__ = ["NormalizationChoice", "NormalizationNeedProposal", "NeedReading", "NormalizationNeed"]

NormalizationNeed = Literal["sequencing_depth", "gene_length", "group_differences", "same_distribution"]
NormalizationMethod = Literal["snail", "rle", "tmm", "quantile", "fpkm"]


class NeedReading(BaseModel):
    model_config = ConfigDict(extra="forbid")
    need: NormalizationNeed
    text_span: str = Field(description="Exact contiguous quote from the request that states this need.")


class NormalizationNeedProposal(BaseModel):
    """Whether the request asks to rescale an expression or count matrix now, and what it wants corrected."""

    model_config = ConfigDict(extra="forbid")
    asks_to_normalize: bool = Field(description=(
        "True only when the request asks, now, to rescale, normalize or make comparable the values of an "
        "expression or count matrix (not a question about it, and not an analysis that merely uses the data)."
    ))
    needs: list[NeedReading] = Field(max_length=4, description=(
        "What the request says must be corrected. sequencing_depth: samples differ in sequencing depth or "
        "library size. gene_length: values must account for gene length. group_differences: samples come from "
        "different tissues, conditions or groups whose real differences must be kept. same_distribution: every "
        "sample should end with the same value distribution. Leave empty when the request states none."
    ))

    @classmethod
    def model_json_schema(cls, *args, **kwargs):
        """The provider sees the strict-mode form; validation is unchanged (Log 208)."""
        return strict_json_schema(super().model_json_schema(*args, **kwargs))


class NormalizationChoice(BaseModel):
    """How normalize_expression's method was chosen: named in the request, read from its stated needs, or the
    default. With more than one candidate the method is asked, never picked."""

    model_config = ConfigDict(extra="forbid")
    source: Literal["named", "need", "default", "answered"]
    needs: list[NeedReading] = Field(default_factory=list)
    candidates: list[NormalizationMethod] = Field(default_factory=list)
