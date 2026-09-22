"""Provider contract: each scientific value and its support form one claim.

The internal outcome/evidence ledger is a projection, never a second model output.
Legacy persisted outcomes remain readable; new provider calls use these schemas.
"""

from __future__ import annotations

from typing import Generic, Literal, TypeVar
from pydantic import BaseModel, ConfigDict, Field, model_validator
from workflow_registry import ArtifactType, EntityType, Granularity, Operation
from .outcomes import (
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
    SemanticInterpretation,
)

T = TypeVar("T")


class Support(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: Literal["explicit", "inferred"]
    text_span: str | None = Field(default=None, min_length=1, max_length=160)
    rationale: str = Field(min_length=1, max_length=240)

    @model_validator(mode="after")
    def explicit_requires_quote(self):
        if self.source == "explicit" and not (self.text_span or "").strip():
            raise ValueError("Explicit support requires an original request quote")
        return self

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        """Expose the explicit-quote invariant to structured-output providers."""
        schema = handler.resolve_ref_schema(handler(core_schema))
        quote = {
            key: value
            for key, value in schema["properties"]["text_span"].items()
            if key not in {"anyOf", "default", "title"}
        }
        quote.update({"type": "string", "minLength": 1, "maxLength": 160})

        def variant(source: str, extra: dict[str, dict]) -> dict:
            fields = {
                name: {
                    key: value
                    for key, value in schema["properties"][name].items()
                    if key not in {"title", "description"}
                }
                for name in schema["required"]
            }
            fields["source"] = {"enum": [source]}
            return {
                "type": "object",
                "required": [*schema["required"], *extra],
                "properties": {**fields, **extra},
            }

        schema["anyOf"] = [
            variant("explicit", {"text_span": quote}),
            variant("inferred", {}),
        ]
        return schema


class Claim(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")
    value: T
    support: Support | None = None


class ClaimedOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation: Claim[Operation]
    artifact_type: Claim[ArtifactType]
    granularity: Claim[Granularity]
    input_artifacts: list[Claim[ArtifactType]] = Field(
        default_factory=list, max_length=4
    )
    entity_types: list[Claim[EntityType]] = Field(default_factory=list, max_length=8)
    regulator_types: list[Claim[Literal["tf", "mirna", "unknown"]]] = Field(
        default_factory=list, max_length=3
    )
    target_types: list[Claim[Literal["gene", "unknown"]]] = Field(
        default_factory=list, max_length=2
    )
    selection_tags: list[Claim[str]] = Field(default_factory=list, max_length=16)
    display_entities: list[str] = Field(default_factory=list, max_length=8)
    unresolved_dimensions: list[str] = Field(default_factory=list, max_length=4)


DIMENSIONS = {
    "operation": "operation",
    "artifact_type": "artifact_type",
    "granularity": "granularity",
    "input_artifacts": "input_artifact",
    "entity_types": "entity_type",
    "regulator_types": "regulator_type",
    "target_types": "target_type",
    "selection_tags": "selection_tag",
}


def project_outcome(outcome: ClaimedOutcome):
    values = outcome.model_dump()
    evidence = []
    for field, dimension in DIMENSIONS.items():
        claims = getattr(outcome, field)
        many = isinstance(claims, list)
        items = claims if many else [claims]
        values[field] = [c.value for c in items] if many else claims.value
        for claim in items:
            if claim.support is not None:
                evidence.append(
                    OutcomeEvidence(
                        dimension=dimension,
                        value=claim.value,
                        **claim.support.model_dump(),
                    )
                )
    return RequestedOutcome.model_validate(values), evidence


class ClaimedHypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    outcome: ClaimedOutcome
    confidence: float = Field(ge=0, le=1)
    assumptions: list[str] = Field(default_factory=list, max_length=4)

    def to_internal(self):
        outcome, evidence = project_outcome(self.outcome)
        return OutcomeHypothesis(
            outcome=outcome,
            evidence=evidence,
            confidence=self.confidence,
            assumptions=self.assumptions,
        )


class SemanticClaims(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_mode: Literal["guidance", "execute", "unknown"]
    semantic_goal: str = Field(min_length=1, max_length=240)
    outcome_hypotheses: list[ClaimedHypothesis] = Field(min_length=1, max_length=3)

    def to_internal(self):
        return SemanticInterpretation(
            request_mode=self.request_mode,
            semantic_goal=self.semantic_goal,
            outcome_hypotheses=[h.to_internal() for h in self.outcome_hypotheses],
        )


class ClaimChanges(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation: Claim[Operation] | None = None
    artifact_type: Claim[ArtifactType] | None = None
    granularity: Claim[Granularity] | None = None
    input_artifacts: list[Claim[ArtifactType]] | None = Field(
        default=None, max_length=4
    )
    entity_types: list[Claim[EntityType]] | None = Field(default=None, max_length=8)
    regulator_types: list[Claim[Literal["tf", "mirna", "unknown"]]] | None = Field(
        default=None, max_length=3
    )
    target_types: list[Claim[Literal["gene", "unknown"]]] | None = Field(
        default=None, max_length=2
    )
    selection_tags: list[Claim[str]] | None = Field(default=None, max_length=16)
    display_entities: list[str] | None = Field(default=None, max_length=8)
    unresolved_dimensions: list[str] | None = Field(default=None, max_length=4)


class HypothesisRepair(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hypothesis_index: int = Field(ge=0, le=2)
    outcome: ClaimChanges


class SemanticClaimRepair(BaseModel):
    """Atomic field replacements. Other hypotheses and fields are preserved."""

    model_config = ConfigDict(extra="forbid")
    repairs: list[HypothesisRepair] = Field(default_factory=list, max_length=3)
    request_mode: Literal["guidance", "execute", "unknown"] | None = None
    semantic_goal: str | None = Field(default=None, min_length=1, max_length=240)

    def apply(self, proposal: SemanticClaims) -> SemanticClaims:
        data = proposal.model_dump()
        seen = set()
        for repair in self.repairs:
            index = repair.hypothesis_index
            if index >= len(data["outcome_hypotheses"]) or index in seen:
                raise ValueError("Repair requires a unique existing hypothesis index")
            seen.add(index)
            data["outcome_hypotheses"][index]["outcome"].update(
                repair.outcome.model_dump(exclude_none=True)
            )
        for field in ("request_mode", "semantic_goal"):
            if getattr(self, field) is not None:
                data[field] = getattr(self, field)
        return SemanticClaims.model_validate(data)
