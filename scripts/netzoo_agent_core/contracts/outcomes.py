"""Typed scientific outcomes and deterministic capability-match results."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from workflow_registry import (
    ActionName,
    ArtifactType,
    EntityType,
    Granularity,
    Operation,
    RecommendedAction,
)


CapabilityMatchStatus = Literal["exact", "fallback", "ambiguous", "unsupported", "not_applicable"]
MatchBasis = Literal["semantic", "partial_evidence", "registry_features", "workflow_name", "semantic_validation_recovery", "confirmed_context"]
EvidenceDimension = Literal[
    "operation",
    "input_artifact",
    "artifact_type",
    "entity_type",
    "regulator_type",
    "target_type",
    "granularity",
    "selection_tag",
]


class RequestedOutcome(BaseModel):
    """Bounded description of the scientific result requested by the user."""

    model_config = ConfigDict(extra="forbid")

    operation: Operation
    input_artifacts: list[ArtifactType] = Field(
        default_factory=list, max_length=4,
        description=(
            "Current inputs for the requested analysis, separate from output artifact_type. "
            "Exclude historical datasets and merely proposed intermediate outputs."
        ),
    )
    artifact_type: ArtifactType
    entity_types: list[EntityType] = Field(default_factory=list, max_length=8)
    display_entities: list[str] = Field(default_factory=list, max_length=8)
    regulator_types: list[Literal["tf", "mirna", "unknown"]] = Field(
        default_factory=list, max_length=3
    )
    target_types: list[Literal["gene", "unknown"]] = Field(
        default_factory=list, max_length=2
    )
    selection_tags: list[str] = Field(
        default_factory=list,
        max_length=16,
        description=(
            "Registry-defined intent signals inferred from the user's scientific "
            "purpose. These guide capability composition but do not select or "
            "authorize a workflow by themselves."
        ),
    )
    granularity: Granularity
    unresolved_dimensions: list[str] = Field(default_factory=list, max_length=4)

    @field_validator("unresolved_dimensions")
    @classmethod
    def _exclude_optional_registry_signals(cls, values: list[str]) -> list[str]:
        """Advisory registry tags are not missing scientific requirements."""
        optional = {"selection_tag", "selection_tags", "registry_tag", "registry_tags"}
        return [
            item for item in values
            if item.strip().casefold().replace(" ", "_") not in optional
        ]

    @field_validator("display_entities", "unresolved_dimensions", "selection_tags")
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
    text_span: str | None = Field(default=None, min_length=1, max_length=160)
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
    def _normalize_registry_tag_evidence(cls, value):
        """Keep registry signals separate from the scientific evidence ontology."""
        if not isinstance(value, Mapping):
            return value
        normalized = dict(value)
        raw_outcome = normalized.get("outcome") or normalized
        if not isinstance(raw_outcome, Mapping):
            return normalized
        selection_tags = set(raw_outcome.get("selection_tags") or ())
        aliases = {"selection_tag", "selection_tags", "registry_tag", "registry_tags"}
        evidence = []
        for item in normalized.get("evidence") or ():
            if not isinstance(item, Mapping):
                evidence.append(item)
                continue
            normalized_item = dict(item)
            dimension = normalized_item.get("dimension")
            if dimension in selection_tags:
                normalized_item["dimension"] = "selection_tag"
                normalized_item["value"] = dimension
            elif dimension in aliases:
                normalized_item["dimension"] = "selection_tag"
            evidence.append(normalized_item)
        normalized["evidence"] = evidence
        return normalized

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


class SemanticInterpretation(BaseModel):
    """Workflow-independent scientific meaning produced by the semantic model."""

    model_config = ConfigDict(extra="forbid")

    request_mode: Literal["guidance", "execute", "unknown"] = Field(
        default="unknown",
        description=(
            "Whether the user is asking for conceptual/planning guidance or is "
            "explicitly asking the agent to perform the work now. This is a "
            "semantic classification, not workflow selection or tool authorization."
        ),
    )
    semantic_goal: str = Field(min_length=1, max_length=240)
    outcome_hypotheses: list[OutcomeHypothesis] = Field(
        min_length=1,
        max_length=3,
        description=(
            "One to three evidence-bearing scientific outcome interpretations. "
            "This contract cannot select workflows or authorize execution."
        ),
    )


class SemanticReview(BaseModel):
    """One adjudicated scientific outcome returned by the review pass."""

    model_config = ConfigDict(extra="forbid")

    request_mode: Literal["guidance", "execute", "unknown"] = Field(
        default="unknown",
        description=(
            "Adjudicated request mode from the full user request; this does not "
            "select a workflow."
        ),
    )
    semantic_goal: str = Field(min_length=1, max_length=240)
    outcome_hypothesis: OutcomeHypothesis = Field(
        description=(
            "The single primary scientific outcome after independently reviewing "
            "the first-pass proposal. Remaining uncertainty belongs in the typed "
            "outcome's unknown and unresolved fields, not in intent alternatives."
        )
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_hypothesis_metadata(cls, value):
        """Accept only an equivalent nesting of one hypothesis, never conflicts."""
        if not isinstance(value, Mapping):
            return value
        hypothesis = value.get("outcome_hypothesis")
        if not isinstance(hypothesis, Mapping):
            return value
        normalized = dict(value)
        nested = dict(hypothesis)
        for field in ("confidence", "evidence", "assumptions"):
            if field not in normalized:
                continue
            if field in nested and nested[field] != normalized[field]:
                raise ValueError(f"Conflicting review hypothesis metadata: {field}")
            nested[field] = normalized.pop(field)
        normalized["outcome_hypothesis"] = nested
        return normalized


class RejectedMethod(BaseModel):
    """Code-owned incompatibility scoped to the current input, not a whole method."""

    model_config = ConfigDict(extra="forbid")
    action: RecommendedAction
    workflow: str
    reason_code: Literal["incompatible_input", "unsupported_input"]
    input_artifacts: list[ArtifactType]
    accepted_input_artifacts: list[ArtifactType]
    reason: str


class CapabilityMatch(BaseModel):
    """Code-owned relationship between one requested outcome and the registry."""

    model_config = ConfigDict(extra="forbid")

    status: CapabilityMatchStatus
    match_basis: MatchBasis = "semantic"
    rejected_methods: list[RejectedMethod] = Field(default_factory=list)
    matched_actions: list[ActionName] = Field(default_factory=list, max_length=6)
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
    "SemanticInterpretation",
]
