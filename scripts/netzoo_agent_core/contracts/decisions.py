"""Routing and capability decision contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field
from workflow_registry import ActionName, IntentType, PreferenceKey, RecommendedAction

class PreferenceProposal(BaseModel):
    key: PreferenceKey
    value: str
    reason: str

class RouterDecision(BaseModel):
    """Small LLM-facing interface; deterministic code hydrates execution details."""

    action: ActionName
    in_scope: bool = True
    intent_type: IntentType = "unknown"
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=300)
    recommended_actions: list[RecommendedAction] = Field(
        default_factory=list, max_length=4
    )

class TaskDecision(BaseModel):
    """A capability-aware routing decision for the allow-listed NetZoo agent."""

    action: ActionName
    in_scope: bool = Field(
        description="True only when the requested operation is supported by this agent."
    )
    should_execute: bool = Field(
        description="True only when a tool call is necessary to fulfil the request now."
    )
    intent_type: IntentType = Field(
        default="unknown",
        description=(
            "High-level user intent. answer_question means explain concepts, "
            "formats, inputs, or usage without running local tools."
        ),
    )
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    recommended_actions: list[RecommendedAction] = Field(
        default_factory=list,
        description=(
            "Allow-listed local capabilities that fit the user's goal, ordered as a "
            "useful workflow. Populate this even when action=no_tool because the user "
            "asked for advice rather than immediate execution."
        ),
    )
    missing_inputs: list[str] = Field(default_factory=list)
    expression_file: str | None = None
    motif_file: str | None = None
    ppi_file: str | None = None
    mirna_file: str | None = None
    output_file: str | None = None
    lioness_output: str | None = None
    network_file: str | None = None
    output_dir: str | None = None
    prefix: str | None = None
    with_header: bool = False
    genes_axis: Literal["auto", "rows", "columns"] = "auto"
    library_name: str | None = None
    library_id: str | None = None
    docs_query: str | None = None
    web_query: str | None = None
    preference_updates: list[PreferenceProposal] = Field(default_factory=list)

__all__ = ['PreferenceProposal', 'RouterDecision', 'TaskDecision']
