"""Typed scientific outcomes and deterministic capability-match results."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from workflow_registry import (
    ACTION_DEFINITIONS,
    ActionName,
    ArtifactType,
    EntityType,
    Granularity,
    Operation,
    RecommendedAction,
)

# Every registered runnable capability can tie at once: an outcome that resolved
# nothing is partially compatible with all of them. A live full-corpus round hit
# exactly that and aborted with hypothesis_actions:too_long, losing the whole
# run. Derive the bound from the registry so it cannot drift behind it again.
# Public because the same tie has to fit through every contract it is copied
# into: widening only the producer cost a second full-corpus round.
RUNNABLE_CAPABILITY_COUNT = sum(
    1 for definition in ACTION_DEFINITIONS.values()
    if definition.run and definition.output_capability is not None
)


CapabilityMatchStatus = Literal["exact", "fallback", "ambiguous", "unsupported", "not_applicable"]
MatchBasis = Literal["semantic", "partial_evidence", "registry_features", "workflow_name", "semantic_validation_recovery", "provider_unavailable", "confirmed_context", "assumed_outcome"]
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

    operation: Operation = Field(description=(
        "Required scientific operation, even for guidance requests. Infer it from the "
        "original scientific goal, not a tool name or request_mode. Use unknown with "
        "unresolved_dimensions when genuinely unresolved; never omit this field."
    ))
    input_artifacts: list[ArtifactType] = Field(
        default_factory=list, max_length=4,
        description=(
            "Current inputs for the requested analysis, separate from output artifact_type. "
            "Exclude historical datasets and merely proposed intermediate outputs. "
            "A list of plain strings: each item is one exact artifact_type literal "
            "from the closed vocabulary defined in the system prompt. Never invent or "
            "translate a name, and never wrap an item in an object; evidence, roles "
            "and rationales belong in the hypothesis evidence list, not here."
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
    granularity: Granularity = Field(description=(
        "Required output granularity, not the input entity type. Cohort-wide sample "
        "distances or cluster labels are aggregate; separately inferred per-sample "
        "results are sample_specific. Never omit this field."
    ))
    unresolved_dimensions: list[str] = Field(default_factory=list, max_length=4)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        from .artifact_semantics import ARTIFACT_SEMANTICS, artifact_field_constraints

        schema = handler.resolve_ref_schema(handler(core_schema))
        # Keep required fields visible in EVERY conditional branch. Previously
        # these branches were only refinement fragments. Observed replies omitted
        # operation (and sometimes granularity); root required was preserved by
        # the SDK, but function calling does not guarantee schema compliance.
        # Do not copy all optional fields/descriptions into every branch: the root
        # still owns them, and redundant schema text consumes the routing budget.
        variants = []
        for artifact in ARTIFACT_SEMANTICS:
            constraints = artifact_field_constraints(artifact)
            fields = {}
            for name in dict.fromkeys([*schema["required"], *constraints]):
                field = deepcopy(schema["properties"][name])
                field.pop("title", None)
                field.pop("description", None)
                constraint = constraints.get(name, {})
                if "items" in constraint:
                    field["items"].update(constraint["items"])
                field.update({key: value for key, value in constraint.items() if key != "items"})
                if "const" in constraint:
                    field["enum"] = [constraint["const"]]
                fields[name] = field
            variants.append({"type": "object", "required": list(schema["required"]), "properties": fields})
        schema["anyOf"] = variants
        return schema

    @field_validator(
        "input_artifacts", "entity_types", "regulator_types", "target_types",
        mode="before",
    )
    @classmethod
    def _unwrap_single_key_transport_objects(cls, values):
        """Normalize an equivalent provider transport shape before validation.

        Providers mirror this model's own field names and return
        `{"artifact_type": "mutation_matrix"}` where one closed-vocabulary literal
        belongs. A single-key wrapper carries exactly that literal, so unwrapping
        it discards nothing and the value still faces the same strict enum. Any
        shape whose meaning would have to be chosen -- extra keys, an unknown key,
        a non-string value -- is left untouched for strict validation to locate.
        No name is ever mapped onto another. Free-text lists are excluded, since
        an object there is a genuine error rather than a wrapper.
        """
        if not isinstance(values, (list, tuple)):
            return values
        return [_unwrapped_literal(item) for item in values]

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


# Field names a provider mirrors from this contract when it wraps a literal.
_TRANSPORT_WRAPPER_KEYS = frozenset(
    {"artifact_type", "artifact", "type", "name", "value", "input_artifact"}
)


def _unwrapped_literal(item):
    """Return the literal a mirrored outcome object carries, else it unchanged.

    Providers echo this contract's own field names, either as a bare wrapper or
    as a copy of the artifact's field-constraint object. Sibling outcome fields
    have no representation inside one item of a closed-vocabulary list, so
    reading the single artifact literal such an object names discards nothing
    the contract could have stored. Exactly one wrapper key may carry a string,
    every other key must itself be an outcome field, and the literal still faces
    the same strict enum. Any other shape is left for validation to locate.
    """
    if not isinstance(item, Mapping) or not item:
        return item
    named = [
        key for key in item
        if key in _TRANSPORT_WRAPPER_KEYS and isinstance(item[key], str)
    ]
    if len(named) != 1:
        return item
    siblings = set(item) - {named[0]}
    if siblings and not siblings <= _OUTCOME_FIELD_NAMES:
        return item
    return item[named[0]]


# Resolved after RequestedOutcome is defined; a mirrored object may only echo
# this contract's own field names.
_OUTCOME_FIELD_NAMES: frozenset[str] = frozenset()


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
        raw_evidence = normalized.get("evidence")
        if raw_evidence is None:
            raw_evidence = ()
        # A provider may return any JSON shape for a declared field. Unexpected
        # shapes are left untouched so strict validation reports their exact path
        # and type, instead of an untyped lookup here raising TypeError and
        # turning a repairable schema failure into an unavailable-router report.
        if not isinstance(raw_outcome, Mapping) or not isinstance(raw_evidence, (list, tuple)):
            return normalized
        raw_tags = raw_outcome.get("selection_tags")
        selection_tags = {
            tag
            for tag in (raw_tags if isinstance(raw_tags, (list, tuple)) else ())
            if isinstance(tag, str)
        }
        aliases = {"selection_tag", "selection_tags", "registry_tag", "registry_tags"}
        evidence = []
        for item in raw_evidence:
            if not isinstance(item, Mapping):
                evidence.append(item)
                continue
            normalized_item = dict(item)
            dimension = normalized_item.get("dimension")
            if not isinstance(dimension, str):
                evidence.append(normalized_item)
                continue
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


class OutcomePatch(BaseModel):
    """Only the outcome fields the review is changing.

    An omitted field is not "unknown": it means the first pass already got that
    field right and it is carried forward unchanged. Re-emitting a whole outcome
    is what produced 22 fresh `schema_validation` failures across the live record
    while fixing 2, so the review is asked for a delta instead of a rewrite.
    """

    model_config = ConfigDict(extra="forbid")

    operation: Operation | None = None
    input_artifacts: list[ArtifactType] | None = Field(default=None, max_length=4)
    artifact_type: ArtifactType | None = None
    entity_types: list[EntityType] | None = Field(default=None, max_length=8)
    display_entities: list[str] | None = Field(default=None, max_length=8)
    regulator_types: list[Literal["tf", "mirna", "unknown"]] | None = Field(
        default=None, max_length=3
    )
    target_types: list[Literal["gene", "unknown"]] | None = Field(
        default=None, max_length=2
    )
    selection_tags: list[str] | None = Field(default=None, max_length=16)
    granularity: Granularity | None = None
    unresolved_dimensions: list[str] | None = Field(default=None, max_length=4)


class EvidenceRemoval(BaseModel):
    """One evidence entry the review withdraws, named by dimension and value."""

    model_config = ConfigDict(extra="forbid")

    dimension: EvidenceDimension
    value: str = Field(min_length=1, max_length=80)


class SemanticPatch(BaseModel):
    """A field-scoped repair of one first-pass hypothesis, never a rewrite.

    The merge only carries forward values the first pass itself produced; it
    never supplies a value no model wrote. The merged interpretation is then run
    through the same strict validation as any other, with nothing relaxed.
    """

    model_config = ConfigDict(extra="forbid")

    hypothesis_index: int = Field(
        default=0, ge=0, le=2,
        description=(
            "Which first-pass hypothesis this repair adjudicates as the single "
            "primary scientific outcome. Zero-based, in the proposal's own order."
        ),
    )
    request_mode: Literal["guidance", "execute", "unknown"] | None = None
    semantic_goal: str | None = Field(default=None, min_length=1, max_length=240)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    outcome: OutcomePatch = Field(default_factory=OutcomePatch)
    evidence_removals: list[EvidenceRemoval] = Field(default_factory=list, max_length=12)
    evidence_additions: list[OutcomeEvidence] = Field(default_factory=list, max_length=12)
    assumptions: list[str] | None = Field(default=None, max_length=4)

    @model_validator(mode="before")
    @classmethod
    def _normalize_nested_evidence_lists(cls, value):
        """Accept only an equivalent nesting of the evidence lists, never conflicts.

        A live round returned this patch shape five times out of five for one
        request, with the root's `evidence_additions` placed inside the nested
        `outcome` object and nothing else wrong. Both names describe the same
        repair, so the nesting is equivalent, not ambiguous.
        """
        if not isinstance(value, Mapping):
            return value
        outcome = value.get("outcome")
        if not isinstance(outcome, Mapping):
            return value
        normalized = dict(value)
        nested = dict(outcome)
        for field in ("evidence_additions", "evidence_removals"):
            if field not in nested:
                continue
            if field in normalized and normalized[field] != nested[field]:
                raise ValueError(f"Conflicting patch evidence list: {field}")
            normalized[field] = nested.pop(field)
        normalized["outcome"] = nested
        return normalized


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
    # Candidates behind an ambiguous match, not a recommendation. A wholly
    # unresolved outcome legitimately lists every capability, and the caller
    # already refuses to promote anything but a lone candidate.
    hypothesis_actions: list[RecommendedAction] = Field(
        default_factory=list, max_length=RUNNABLE_CAPABILITY_COUNT
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


_OUTCOME_FIELD_NAMES = frozenset(RequestedOutcome.model_fields)
