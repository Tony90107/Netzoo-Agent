"""Routing and capability decision contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field
from workflow_registry import ActionName, IntentType, PreferenceKey, RecommendedAction

from .outcomes import CapabilityMatchStatus, OutcomeHypothesis, RequestedOutcome

class PreferenceProposal(BaseModel):
    key: PreferenceKey
    value: str
    reason: str


class IntentDecision(BaseModel):
    """LLM-owned answer/execute choice with no workflow-selection authority."""

    mode: Literal["answer", "execute"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=300)


class RouterDecision(BaseModel):
    """LLM-owned semantic routing proposal, bounded by the action allowlist."""

    action: ActionName
    selected_action: ActionName | None = Field(
        default=None,
        description="Selected action; action remains as the migration-compatible alias.",
    )
    candidate_actions: list[ActionName] = Field(default_factory=list, max_length=6)
    in_scope: bool = True
    intent_type: IntentType = "unknown"
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=600)
    semantic_goal: str | None = Field(default=None, max_length=240)
    clarification_question: str | None = Field(default=None, max_length=300)
    outcome_hypotheses: list[OutcomeHypothesis] = Field(
        default_factory=list,
        max_length=3,
        description=(
            "Bounded interpretations of the scientific result. Preserve competing "
            "interpretations instead of erasing known evidence. An empty list "
            "triggers one workflow-independent semantic interpretation call."
        )
    )

    @property
    def requested_outcome(self) -> RequestedOutcome | None:
        """Compatibility view until all consumers read outcome hypotheses directly."""
        if len(self.outcome_hypotheses) != 1:
            return None
        return self.outcome_hypotheses[0].outcome

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
    candidate_actions: list[ActionName] = Field(default_factory=list, max_length=6)
    recommended_actions: list[RecommendedAction] = Field(
        default_factory=list,
        description=(
            "Code-owned workflow guidance sequence derived from one exact outcome "
            "match. Router output must not populate this field."
        ),
    )
    requested_outcome: RequestedOutcome | None = None
    outcome_hypotheses: list[OutcomeHypothesis] = Field(
        default_factory=list, max_length=3
    )
    capability_match_status: CapabilityMatchStatus | None = None
    matched_actions: list[RecommendedAction] = Field(default_factory=list)
    hypothesis_actions: list[RecommendedAction] = Field(default_factory=list, max_length=6)
    alternative_actions: list[RecommendedAction] = Field(default_factory=list)
    mismatch_dimensions: list[str] = Field(default_factory=list)
    clarification_question: str | None = None
    missing_inputs: list[str] = Field(default_factory=list)
    expression_file: str | None = None
    design_file: str | None = None
    motif_file: str | None = None
    ppi_file: str | None = None
    mirna_file: str | None = None
    coexpression_file: str | None = None
    output_file: str | None = None
    lioness_output: str | None = None
    network_file: str | None = None
    omics_layer_1: str | None = None
    omics_layer_2: str | None = None
    output_dir: str | None = None
    prefix: str | None = None
    with_header: bool = False
    genes_axis: Literal["auto", "rows", "columns"] = "auto"
    output_format: Literal["matrix", "edge_list"] = "matrix"
    lambda1: float | None = Field(default=None, ge=0.0, le=1.0)
    lambda2: float | None = Field(default=None, ge=0.0, le=1.0)
    library_name: str | None = None
    library_id: str | None = None
    docs_query: str | None = None
    web_query: str | None = None
    preference_updates: list[PreferenceProposal] = Field(default_factory=list)

__all__ = ['IntentDecision', 'PreferenceProposal', 'RouterDecision', 'TaskDecision']
