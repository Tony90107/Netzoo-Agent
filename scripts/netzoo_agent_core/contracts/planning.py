"""Workflow planning and evidence contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ..settings import MAX_RECOVERY_ATTEMPTS
from .decisions import PreferenceProposal
from .handoffs import WorkflowHandoff

class InputEvidence(BaseModel):
    """Where a workflow input came from and why it is (or is not) usable."""

    field: str
    status: Literal[
        "provided",
        "selected",
        "discovered",
        "derived",
        "demo_bundle",
        "defaulted",
        "missing",
    ]
    value: str | None = None
    reason: str
    candidates: list[str] = Field(default_factory=list)
    candidate_bundle_ids: list[str] = Field(default_factory=list)
    bundle_id: str | None = None
    derived_from: str | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )


class InputRoleAssignment(BaseModel):
    """One LLM-proposed input role mapping grounded in a candidate file."""

    path: str = Field(min_length=1, max_length=4_000)
    role: str = Field(min_length=1, max_length=100)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(default="", max_length=2_000)


class InputRoleMapping(BaseModel):
    """Structured, bounded output for content-based input role discovery."""

    assignments: list[InputRoleAssignment] = Field(default_factory=list, max_length=50)

class GeneLabelSuggestion(BaseModel):
    """One LLM-proposed reading of a label the gene authority did not accept."""

    label: str = Field(min_length=1, max_length=200)
    likely_symbol: str = Field(default="", max_length=200)
    reason: str = Field(default="", max_length=500)


class GeneLabelSuggestions(BaseModel):
    """Structured, bounded output for gene label repair hints."""

    suggestions: list[GeneLabelSuggestion] = Field(
        default_factory=list, max_length=20
    )


class InputBundleOption(BaseModel):
    """One complete coherent input bundle offered as an atomic selection."""

    bundle_id: str = Field(min_length=1, max_length=4_000)
    directory: str = Field(min_length=1, max_length=4_000)
    inputs: dict[str, str] = Field(min_length=1, max_length=20)

class WorkflowStep(BaseModel):
    action: str
    purpose: str
    arguments: dict = Field(default_factory=dict)

class RawCountSignal(BaseModel):
    """The expression matrix a workflow will read looks like raw counts with uneven sample totals (2026-11-05).

    Every number here was read from the file by code (`data.normalization.raw_count_signal`).
    """

    expression_file: str = Field(min_length=1, max_length=4_000)
    samples: int = Field(ge=2)
    max_value: float = Field(ge=0)
    total_min: float = Field(gt=0)
    total_max: float = Field(gt=0)
    #: Share of the non-zero values that are whole numbers; below 0.99 the matrix reads as expected counts
    #: (for example RSEM's expected_count, where reads shared between genes are split fractionally).
    whole_share: float = Field(default=1.0, ge=0, le=1)


class WorkflowPlan(BaseModel):
    workflow: str
    objective: str
    decision: dict
    evidence: list[InputEvidence] = Field(default_factory=list)
    input_bundle_options: list[InputBundleOption] = Field(default_factory=list)
    steps: list[WorkflowStep] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    status: Literal["ready", "needs_input", "needs_confirmation", "respond_only"]
    question: str | None = None
    workflow_handoff: WorkflowHandoff | None = None
    preference_proposals: list[PreferenceProposal] = Field(default_factory=list)
    memory_notes: list[str] = Field(default_factory=list)
    policy_hash: str | None = None
    policy_notes: list[str] = Field(default_factory=list)
    recovery_action: str | None = None
    recovery_error_code: str | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    recovery_step_index: int | None = Field(default=None, ge=0)
    recovery_attempt: int = Field(default=0, ge=0, le=MAX_RECOVERY_ATTEMPTS)
    raw_counts: RawCountSignal | None = Field(default=None, exclude_if=lambda value: value is None)
    """Set when the workflow reads an expression matrix that looks like raw counts with uneven sample totals."""

__all__ = [
    'InputBundleOption',
    'InputEvidence',
    'RawCountSignal',
    'WorkflowStep',
    'WorkflowPlan',
    'WorkflowHandoff',
]
