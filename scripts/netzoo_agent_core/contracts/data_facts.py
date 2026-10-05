"""What the request says about the data it has, as a model proposes it (Log 376).

Logs 371 and 373 read whether a request has a TF motif prior and a PPI network
with word lists and failed both ways. Logs 374-375 read it in the
study-purpose call: the reading was right (no false "stated"), but sharing
that prompt cost the conclusions it reads. It is now its own small call,
asked only on a tie with a verified question, and its quote is checked only
for provenance.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .strict_schema import strict_json_schema

__all__ = ["DataFactsProposal"]


class DataFactsProposal(BaseModel):
    """Whether the request says it has prior knowledge of TF binding or protein interactions."""

    model_config = ConfigDict(extra="forbid")
    priors: Literal["stated", "ruled_out", "unstated"]
    priors_span: str = Field(description=(
        "Exact contiguous quote saying the request has, or does not have, a TF motif or binding prior or a "
        "protein-interaction network; empty when unstated."))

    @classmethod
    def model_json_schema(cls, *args, **kwargs):
        """The provider sees the strict-mode form; validation is unchanged (Log 208)."""
        return strict_json_schema(super().model_json_schema(*args, **kwargs))
