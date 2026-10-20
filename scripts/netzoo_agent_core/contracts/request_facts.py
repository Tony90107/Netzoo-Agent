"""ROUND-03 (collab/ROUND-03-PLAN.md): the request's counts and settings as one record that every later step cites.

The capability check reads the data size and the method's settings in several places of one reply -- for the request
as a whole, again inside each asked result, and a count the user is unsure of both as candidates and as an unknown
fact. On 977 recorded readings the request-level and result-level sample counts were both written 545 times and
differed 3 times (all C47: two cohorts); settings were written twice 321 times and never differed. Each place used to
travel as its own copy. Here each fact is kept once, with every read of it, and the result checks, the count questions
and the run's controls name the facts they used (`interpretation.request_facts`).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["FactConflict", "FactEvidence", "FactProperty", "RequestFact"]

FactProperty = Literal["sample_count", "feature_count", "setting"]


class FactEvidence(BaseModel):
    """One read of a fact: where in the reading it was written, and the request words it quoted."""

    model_config = ConfigDict(extra="forbid")
    reader: Literal["request", "result", "count_alternatives", "unknown_facts", "side_by_side", "input_file"]
    """request: the reading's request-level fields; result: an asked result's own fields; count_alternatives /
    unknown_facts: a count the user gave as candidates, or said they do not know; side_by_side (ROUND-07): a count the
    reading wrote as one number whose words give another beside it; input_file (ROUND-07): code counted it in the
    file the request names (`quote` is the file's path, `span` empty)."""
    quote: str
    span: list[int]
    result: str = ""
    """For a result read: the result's words (the scope the value was written for)."""
    role: Literal["value", "alternative", "operand"] = "value"
    """As ROUND-02's evidence (`contracts.slim_reading.Evidence`): the value itself, one of several candidates, or a
    part of a total code derived."""


class RequestFact(BaseModel):
    """One count or setting of the request, kept once whatever number of places the reading wrote it in."""

    model_config = ConfigDict(extra="forbid")
    id: str
    """Stable within the turn: the property and the request words that state it (a re-read keeps the same id)."""
    property: FactProperty
    name: str = ""
    """setting: WORKFLOW.setting, or unregistered; counts: empty."""
    value: str = ""
    """The one value (a count as digits, a setting's value words; empty for a setting stated without a value)."""
    values: list[str] = Field(default_factory=list)
    """state unsure: each candidate the user gave."""
    state: Literal["stated", "unsure"] = "stated"
    origin: Literal["user_stated", "derived", "file"] = "user_stated"
    """derived: computed by code (a total over several data types) -- never words the user said; file (ROUND-07): the
    samples code counted in the expression file the request names, as preflight counts them."""
    quote: str = ""
    span: list[int] = Field(default_factory=list)
    value_quote: str = ""
    """setting: the words giving its value, when apart from its name."""
    value_span: list[int] = Field(default_factory=list)
    belongs_to: str = ""
    """The data object it counts, in the user's words. The check's reading has no field for it, so it stays empty
    (unread) -- never filled from guesswork; the scope a value was written for is in `evidence[].result`."""
    evidence: list[FactEvidence] = Field(default_factory=list)
    derived_from: list[str] = Field(default_factory=list)
    formula: str = ""
    applies_to: list[str] | None = None
    """ROUND-04, reading shape 2: the asked results it applies to, in the request's words; None for every result (and
    for shape 1, where the scope is each read's `evidence[].result`)."""
    scope_unverified: bool = False
    """ROUND-04: the reading named results for it, but none of their words is in the request -- applied only when the
    request asks for one result, never guessed among several."""

    def reads(self) -> int:
        """How many times the reading wrote this fact."""
        return len(self.evidence)


class FactConflict(BaseModel):
    """Two facts of one property that both apply to a result and disagree; which one the result used, and why."""

    model_config = ConfigDict(extra="forbid")
    property: FactProperty
    name: str = ""
    result: str
    used: list[str]
    """The fact ids the result was judged on."""
    set_aside: list[str]
    reason: Literal["result_own_value", "latest_stated", "several_values", "unsure_candidates", "settled_by_file",
                    "file_disagrees", "count_reading_precedence"] = "result_own_value"
    """result_own_value: the result's own words state a count, so the request-level one is not applied to it;
    latest_stated: of two values of one setting, the one stated last is used (both rules are
    `method_conditions.with_request_method`'s, unchanged); several_values (ROUND-04): two different sample counts
    apply to the result, so neither is used -- a doubtful count never decides anything. ROUND-07:
    unsure_candidates -- a stated count inside the words of the user's candidates (or beside a count they said they do
    not know) is set aside, the doubt stands (`used` the candidates, empty for an unknown); settled_by_file -- the
    count code took from the named file settles the candidates (`used` the file's count); file_disagrees -- the file's
    count is none of the candidates, so nothing is settled and the user is asked (`used` the candidates).
    count_reading_precedence -- the dedicated candidate-count reading owns this quantity's property and domain;
    an unknown-fact reading of the same candidates in overlapping words is recorded but not judged again. Unlike
    the other reasons, its set_aside fact may have a different property (features misread as samples)."""
