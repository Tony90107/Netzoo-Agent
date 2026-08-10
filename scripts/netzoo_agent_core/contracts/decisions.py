"""Routing and capability decision contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from workflow_registry import ActionName, IntentType, PreferenceKey, RecommendedAction

from .outcomes import CapabilityMatchStatus, RequestedOutcome


def _require_outcome_in_transport_schema(schema: dict) -> None:
    """Require explicit Router classification without breaking internal fixtures."""
    required = schema.setdefault("required", [])
    if "requested_outcome" not in required:
        required.append("requested_outcome")


def _unclassified_requested_outcome() -> RequestedOutcome:
    """Represent a non-scientific request without using a nullable contract."""
    return RequestedOutcome(
        operation="unknown",
        artifact_type="unknown",
        granularity="not_applicable",
        unresolved_dimensions=["scientific outcome"],
    )


class PreferenceProposal(BaseModel):
    key: PreferenceKey
    value: str
    reason: str

class RouterDecision(BaseModel):
    """Small LLM-facing interface; deterministic code hydrates execution details."""

    model_config = ConfigDict(json_schema_extra=_require_outcome_in_transport_schema)

    action: ActionName
    in_scope: bool = True
    intent_type: IntentType = "unknown"
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=300)
    semantic_goal: str | None = Field(default=None, max_length=240)
    requested_outcome: RequestedOutcome = Field(
        default_factory=_unclassified_requested_outcome,
        description=(
            "Required classification field. Describe the scientific result the user "
            "wants. For a request with no scientific result, use operation=unknown, "
            "artifact_type=unknown, and granularity=not_applicable."
        )
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
            "Code-owned workflow guidance sequence derived from one exact outcome "
            "match. Router output must not populate this field."
        ),
    )
    requested_outcome: RequestedOutcome | None = None
    capability_match_status: CapabilityMatchStatus | None = None
    matched_actions: list[RecommendedAction] = Field(default_factory=list)
    alternative_actions: list[RecommendedAction] = Field(default_factory=list)
    mismatch_dimensions: list[str] = Field(default_factory=list)
    clarification_question: str | None = None
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
