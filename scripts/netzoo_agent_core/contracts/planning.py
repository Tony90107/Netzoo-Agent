"""Workflow planning and evidence contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ..settings import MAX_RECOVERY_ATTEMPTS
from .decisions import PreferenceProposal

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
    bundle_id: str | None = None
    derived_from: str | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )

class WorkflowStep(BaseModel):
    action: str
    purpose: str
    arguments: dict = Field(default_factory=dict)

class WorkflowPlan(BaseModel):
    workflow: str
    objective: str
    decision: dict
    evidence: list[InputEvidence] = Field(default_factory=list)
    steps: list[WorkflowStep] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    status: Literal["ready", "needs_input", "needs_confirmation", "respond_only"]
    question: str | None = None
    preference_proposals: list[PreferenceProposal] = Field(default_factory=list)
    memory_notes: list[str] = Field(default_factory=list)
    policy_hash: str | None = None
    policy_notes: list[str] = Field(default_factory=list)
    recovery_action: Literal["format_expression_headerless"] | None = None
    recovery_step_index: int | None = Field(default=None, ge=0)
    recovery_attempt: int = Field(default=0, ge=0, le=MAX_RECOVERY_ATTEMPTS)

__all__ = ['InputEvidence', 'WorkflowStep', 'WorkflowPlan']
