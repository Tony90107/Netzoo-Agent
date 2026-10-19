"""The slim reading (spec docs/superpowers/specs/2026-10-19-slim-reading-fields-design.md, user decision 2026-10-19).

Only what the user said is written, in four field classes (`scripts/judgment_defaults.yaml`, `slim_fields`):

- A, read every time (step 1): A1 what each thing the request says asks for, A2 the role of each registered name code
  finds, A3 the data the user has or lacks (and whether that is all), A4 run or ask;
- B, read only when code picks them from the candidates' contracts (step 3): B1 scale, B2 regulators, B3 how
  layers are modeled, B4 the condition a candidate's contract turns on, B5 settings of candidate controls, B6 counts;
- C, prohibitions, written only when stated (step 1, or code from A/B): C1 off-menu result, C2 claim, C3 action
  outside the analysis, C4 special data situation, C5 unregistered method, C6 required data lacking, C7 a setting or
  number the contract does not take;
- D, auxiliary (step 1): D1 groups, D2 comparison, D3 sign, D4 requirement, D5 raw files, D6 file doubt.

Each field is read once; an answer fills its field with basis `answered` and is never re-read. `interpretation.
slim_reader.to_menu` turns this into the decision table's state (`MenuReading`), which `decide_menu` judges.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["RESULT_SAID", "ResultItem", "SlimReading", "Stated"]

RESULT_SAID = ("menu_result", "kind_of_result", "workflow_only", "method_choice", "purpose_or_topic",
               "off_menu_result", "unsure_between_results", "question_to_us")
"""What a thing the request asks says. Words that only describe data or context are no A1 item: they are not written."""
Basis = Literal["explicit", "implied", "answered"]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ResultItem(_Model):
    """A1: one thing the request says, and what it asks for."""

    quote: str
    said: Literal[RESULT_SAID]  # type: ignore[valid-type]
    value: str = ""
    """menu_result: the result; kind_of_result: network or regulation."""
    values: list[str] = Field(default_factory=list)
    """unsure_between_results: the results the words leave open."""
    outside_name: str = ""
    """off_menu_result: the user's words naming the result (C1)."""


class Stated(_Model):
    """One stated fact of a B, C or D field (or A3 data): its value and the user's words; alternatives when unsure."""

    field: str
    """A3, B1-B6, C2-C4 or D1-D6."""
    name: str = ""
    """The decision table's dimension the value is of: granularity (B1); regulators or mirna_driver (B2); integration
    or layers (B3); a condition or `setting:<control>` (B4); a control (B5); sample_count, feature_count or
    single_feature_count (B6); claims (C2); delivery (C3); a condition (C4); groups (D1); compare (D2); signed (D3);
    requirements (D4); data_stage (D5); unsure_files (D6); a data kind (A3)."""
    value: str = ""
    values: list[str] = Field(default_factory=list)
    """When the user is unsure: the values the words leave open."""
    quote: str = ""
    item: int = -1
    """The A1 item it belongs to (B1-B3, D2-D4); -1 for the whole request."""
    workflow: str = ""
    """B5: the workflow whose control it is ("" for every candidate that has it)."""
    basis: Basis = "explicit"
    verdicts: dict[str, Literal["met", "contradicted", "not_addressed"]] = Field(default_factory=dict)
    """D4: each candidate workflow's contract on the requirement (the requirement check)."""
    must: bool | None = None
    """D4: the user's answer when asked whether it is a must."""


class SlimReading(_Model):
    status: Literal["read", "failed"] = "read"
    results: list[ResultItem] = Field(default_factory=list)
    roles: dict[str, Literal["target", "choice", "background"]] = Field(default_factory=dict)
    unregistered_methods: list[str] = Field(default_factory=list)
    """C5: the user's words naming a method or variant no registered workflow is."""
    data: list[Stated] = Field(default_factory=list)
    """A3: field "A3", name = the data kind, value = has or lacks."""
    only_these: bool = False
    only_quote: str = ""
    """A3: the user's words saying the data listed are all they have."""
    run: Literal["run", "ask"] = "ask"
    run_quote: str = ""
    """A4: run -- the user asks to run it now (their words); ask -- anything else."""
    stated: list[Stated] = Field(default_factory=list)
    """B1-B6, C2-C4 and D1-D6 as stated (C1, C5, C6 and C7 are code's, from A1, A2, A3 and B5/B6)."""
