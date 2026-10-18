"""The closed-menu reading and decision (spec docs/superpowers/specs/2026-10-18-closed-menu-judgment-design.md, 3.1).

The reader fills `MenuReading`: what the user said, dimension by dimension, each value quoted or marked not stated,
unsure or conflicting. It never says whether anything can be done. `interpretation.menu_decision.decide_menu` reads
it with the defaults table (`scripts/judgment_defaults.yaml`) and makes `MenuDecision`, with no model call.

Phase 0: nothing builds a `MenuReading` from a request yet; gold readings and unit tests do.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["Answer", "Count", "Declined", "MenuDecision", "MenuReading", "Question", "Requirement", "Said",
           "SettingAsked", "TieChoice", "Wanted"]

Status = Literal["stated", "not_stated", "unsure", "conflicting"]
Basis = Literal["explicit", "implied", "answered"]
Form = Literal["deliverable", "question_to_us", "purpose", "data_description", "context"]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Said(_Model):
    """One dimension as the user put it. Implied counts as stated only with words as clear as saying it (draft 3)."""

    status: Status = "not_stated"
    value: str | None = None
    """The value, when stated."""
    values: list[str] = Field(default_factory=list)
    """The readings in play, when unsure or conflicting."""
    basis: Basis | None = None
    quotes: list[str] = Field(default_factory=list)

    def known(self) -> str | None:
        return self.value if self.status == "stated" else None


class Count(_Model):
    status: Status = "not_stated"
    value: int | None = None
    values: list[int] = Field(default_factory=list)
    quotes: list[str] = Field(default_factory=list)


class Requirement(_Model):
    """How a result must be computed or what it must contain, matched to each candidate's contract."""

    quote: str
    verdicts: dict[str, Literal["met", "contradicted", "not_addressed"]] = Field(default_factory=dict)
    """Workflow -> what its contract says about the requirement (filled by the contract check)."""
    must: bool | None = None
    """The user's answer when asked whether it is a must; False drops it from the count."""


class Wanted(_Model):
    """One thing the user wants delivered (or a question, purpose or description, typed by `form`)."""

    quote: str
    form: Form = "deliverable"
    artifact: Said = Field(default_factory=Said)
    integration: Said = Field(default_factory=Said)
    granularity: Said = Field(default_factory=Said)
    regulators: Said = Field(default_factory=Said)
    layers: Said = Field(default_factory=Said)
    signed: Said = Field(default_factory=Said)
    compare: Said = Field(default_factory=Said)
    outside_name: str = ""
    """artifact = off_menu: the user's own words naming the result."""
    requirements: list[Requirement] = Field(default_factory=list)


class SettingAsked(_Model):
    quote: str
    workflow: str = ""
    """The workflow the setting is for; empty -> whichever candidate runs (each is judged)."""
    control: str
    """A YAML control of that workflow, or `unregistered`."""
    value: str = ""
    """One of the control's allowed values, chosen by the reader from the list it is shown."""
    unsure: bool = False
    values: list[str] = Field(default_factory=list)
    """The values in play when the user is unsure (log-transformed or not)."""


class MenuReading(_Model):
    status: Literal["read", "failed"] = "read"
    wanted: list[Wanted] = Field(default_factory=list)
    named_workflows: list[str] | None = None
    """Registered names; None -> code counts them in the request's words (method_names.workflows_in)."""
    context_mentions: list[str] = Field(default_factory=list)
    """Registered names the user mentions only as background ("from our earlier LIONESS run", "COBRA's adjusted
    matrix"), never as the method to run or a choice; code drops them from the names it counts (phase 0, C44)."""
    unregistered_methods: list[str] = Field(default_factory=list)
    """Methods or variants the user asks to use that NetZoo does not register (their words)."""
    claims: Said = Field(default_factory=Said)
    delivery: Said = Field(default_factory=Said)
    conditions: dict[str, Said] = Field(default_factory=dict)
    """data_unit, data_stage, mutation_origin, value_type, mirna_driver, time_model, spatial, group_membership,
    input_network, samples_matched."""
    data: list[str] = Field(default_factory=list)
    """data_available values the user says they have."""
    data_absent: list[str] = Field(default_factory=list)
    only_data: bool = False
    """The user says `data` is all they have."""
    groups: list[str] = Field(default_factory=list)
    """Words naming groups or conditions among the samples (AD and controls, responders and non-responders)."""
    sample_count: Count = Field(default_factory=Count)
    feature_count: Count = Field(default_factory=Count)
    """All features modeled together (both layers for DRAGON)."""
    single_feature_count: int | None = None
    """The one feature count of a single data type (COBRA's genes), when exactly one is stated."""
    settings: list[SettingAsked] = Field(default_factory=list)
    unsure_files: list[str] = Field(default_factory=list)
    """The user's words doubting what a named file holds (which export, which matrix); the input check settles them
    before a run (spec R5), and they are asked about otherwise."""
    run_requested: bool = False


class Answer(_Model):
    """A user's answer to one question; `item` -1 is the request level."""

    item: int
    dimension: str
    value: str


class Question(_Model):
    item: int
    dimension: str
    options: list[tuple[str, str]]
    """(value, user-facing label); "not sure, suggest one" and "none of these" are added by the reply."""
    quote: str = ""
    kind: Literal["intent", "condition", "requirement"] = "intent"


class Declined(_Model):
    quote: str
    reasons: list[str] = Field(default_factory=list)
    instead: list[str] = Field(default_factory=list)


class TieChoice(_Model):
    group: str | None
    workflows: list[str]
    fits: list[str] = Field(default_factory=list)
    """Workflows a stated field makes fit better (`tie_options.fits_when`)."""


class MenuDecision(_Model):
    kind: Literal["CLARIFY", "ASK", "DECLINE", "DO", "UNCHECKED"]
    basis: str
    questions: list[Question] = Field(default_factory=list)
    workflows: list[str] = Field(default_factory=list)
    ties: list[TieChoice] = Field(default_factory=list)
    declined: list[Declined] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    needs: list[str] = Field(default_factory=list)
    unconfirmed: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    """Steps outside NetZoo said before the workflow (raw files to process, a file type to convert)."""
    settled: list[str] = Field(default_factory=list)
    """Doubts about a named file that the input check settles before anything runs."""
    partial: bool = False
    run_ready: bool = False
    final_round: bool = False
