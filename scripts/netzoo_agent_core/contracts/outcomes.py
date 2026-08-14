"""Typed scientific outcomes and deterministic capability-match results."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from workflow_registry import (
    ArtifactType,
    EntityType,
    Granularity,
    Operation,
    RecommendedAction,
)


CapabilityMatchStatus = Literal["exact", "ambiguous", "unsupported"]
EvidenceDimension = Literal[
    "operation",
    "artifact_type",
    "entity_type",
    "regulator_type",
    "target_type",
    "granularity",
]


class RequestedOutcome(BaseModel):
    """Bounded description of the scientific result requested by the user."""

    model_config = ConfigDict(extra="forbid")

    operation: Operation
    artifact_type: ArtifactType
    entity_types: list[EntityType] = Field(default_factory=list, max_length=8)
    display_entities: list[str] = Field(default_factory=list, max_length=8)
    regulator_types: list[Literal["tf", "mirna", "unknown"]] = Field(
        default_factory=list, max_length=3
    )
    target_types: list[Literal["gene", "unknown"]] = Field(
        default_factory=list, max_length=2
    )
    granularity: Granularity
    unresolved_dimensions: list[str] = Field(default_factory=list, max_length=4)

    @field_validator("display_entities", "unresolved_dimensions")
    @classmethod
    def _bounded_text_items(cls, values: list[str]) -> list[str]:
        if any(not item.strip() or len(item) > 120 for item in values):
            raise ValueError("outcome text items must contain 1-120 characters")
        return values


class OutcomeEvidence(BaseModel):
    """One bounded fact supporting an outcome hypothesis."""

    model_config = ConfigDict(extra="forbid")

    dimension: EvidenceDimension
    value: str = Field(min_length=1, max_length=80)
    source: Literal["explicit", "inferred"]
    rationale: str = Field(min_length=1, max_length=240)


class OutcomeHypothesis(BaseModel):
    """One possible scientific outcome plus its evidence and assumptions."""

    model_config = ConfigDict(extra="forbid")

    outcome: RequestedOutcome
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[OutcomeEvidence] = Field(default_factory=list, max_length=12)
    assumptions: list[str] = Field(default_factory=list, max_length=4)

    @model_validator(mode="before")
    @classmethod
    def _nest_flattened_outcome(cls, value):
        """Normalize an equivalent provider transport shape before validation."""
        if not isinstance(value, Mapping) or "outcome" in value:
            return value
        outcome_fields = set(RequestedOutcome.model_fields)
        flattened = outcome_fields.intersection(value)
        if not flattened:
            return value
        normalized = dict(value)
        normalized["outcome"] = {
            field_name: normalized.pop(field_name) for field_name in flattened
        }
        return normalized

    @field_validator("assumptions")
    @classmethod
    def _bounded_assumptions(cls, values: list[str]) -> list[str]:
        if any(not item.strip() or len(item) > 160 for item in values):
            raise ValueError("assumptions must contain 1-160 characters")
        return values


class CapabilityMatch(BaseModel):
    """Code-owned relationship between one requested outcome and the registry."""

    model_config = ConfigDict(extra="forbid")

    status: CapabilityMatchStatus
    matched_actions: list[RecommendedAction] = Field(default_factory=list, max_length=6)
    hypothesis_actions: list[RecommendedAction] = Field(
        default_factory=list, max_length=6
    )
    alternative_actions: list[RecommendedAction] = Field(
        default_factory=list, max_length=2
    )
    mismatch_dimensions: list[str] = Field(default_factory=list, max_length=5)
    clarification_question: str | None = Field(default=None, max_length=300)


__all__ = [
    "CapabilityMatch",
    "CapabilityMatchStatus",
    "EvidenceDimension",
    "OutcomeEvidence",
    "OutcomeHypothesis",
    "RequestedOutcome",
]
