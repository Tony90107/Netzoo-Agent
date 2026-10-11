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
    SELECTION_TAG_GLOSSARY,
)

from .strict_schema import strict_json_schema

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
# "unverified_evidence": the reading was kept although one or more of its quotes
# could not be located in the request. It is the only basis that is not a claim
# about how well the request matched a capability but about how far the reading
# itself is trusted, and `invoke_router` holds anything carrying it below
# `exact` and away from execution.
MatchBasis = Literal["semantic", "partial_evidence", "registry_features", "workflow_name", "semantic_validation_recovery", "provider_unavailable", "confirmed_context", "assumed_outcome", "unverified_evidence"]
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
            "purpose or requested algorithmic approach. Audit the runtime catalog "
            "even when the primary artifact is already known, and include every "
            "supported signal. These guide capability composition but do not select "
            "or authorize a workflow by themselves."
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

    @model_validator(mode="before")
    @classmethod
    def _normalize_evidence_transport(cls, value):
        """Normalize provider spellings that do not change semantic evidence.

        Inferred evidence never claims to quote the request. Some structured
        output providers nevertheless serialize its optional ``text_span`` as
        an empty string; preserving that spelling carries no information and
        would otherwise abort the entire semantic repair. Ordinary explicit
        evidence is intentionally untouched and must still contain a grounded
        quote.

        An ontology bundle is necessarily synthesized from evidence for two or
        more concrete artifacts. One contiguous quote cannot be the source for
        that conjunction, so providers that label the bundle evidence explicit
        are normalized to inference while preserving their rationale. This is
        based only on the typed artifact ontology; it neither reads request text
        nor chooses a workflow.
        """
        if not isinstance(value, Mapping):
            return value
        from .artifact_semantics import ARTIFACT_COMPONENTS

        if (
            value.get("dimension") == "artifact_type"
            and value.get("value") in ARTIFACT_COMPONENTS
            and value.get("source") == "explicit"
        ):
            normalized = dict(value)
            normalized["source"] = "inferred"
            normalized["text_span"] = None
            return normalized
        span = value.get("text_span")
        if value.get("source") == "inferred" and isinstance(span, str) and not span.strip():
            normalized = dict(value)
            normalized["text_span"] = None
            return normalized
        return value

    @model_validator(mode="after")
    def _explicit_evidence_carries_its_quote(self):
        """`explicit` asserts the request said it, so the request must be quoted.

        Without this the contract permitted the one shape it was then certain to
        reject: `_grounded_span` fails an empty quote, so every such entry became
        `ungrounded_evidence`. Across 35 live rounds that shape accounted for 185
        of 188 entries in that family, and 79% of them cost the whole
        interpretation. The rule was only ever stated in prompt prose, which the
        schema below contradicted -- `text_span` was optional and defaulted to
        null. The experimental claims contract already enforces it
        (`semantic_claims.Support`); this brings the mainline contract level with it.
        """
        if self.source == "explicit" and not (self.text_span or "").strip():
            raise ValueError("explicit evidence must quote the request")
        return self

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        """State the same rule where the provider can act on it.

        A `model_validator` never reaches `model_json_schema()`, so enforcing the
        rule in Python alone would leave the provider seeing an optional field
        defaulting to null and change only where the failure surfaces -- from
        evidence validation to schema validation, which is the worse of the two
        paths: a first pass that does not parse leaves no proposal to patch, so
        the retry falls back to a whole review, the shape that introduced a fresh
        issue in 71 of 83 recorded pairs. The branch structure mirrors
        `RequestedOutcome`, whose variants this provider already accepts.
        """
        schema = handler.resolve_ref_schema(handler(core_schema))
        quote = {
            key: value for key, value in schema["properties"]["text_span"].items()
            if key not in {"anyOf", "default", "title"}
        }
        quote.update({"type": "string", "minLength": 1, "maxLength": 160})

        def variant(source: str, extra: dict[str, dict]) -> dict:
            # Every required property is restated inside the branch. A first
            # attempt listed only the constrained ones and relied on the branch
            # composing with the root, which is what JSON Schema means and not
            # what the provider does: it read the branch as the whole object and
            # returned evidence entries carrying nothing but `source` and
            # `text_span`. Every trial of a full round failed schema validation.
            # `RequestedOutcome` above restates them for the same reason.
            fields = {
                name: {
                    key: value for key, value in schema["properties"][name].items()
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

        schema["anyOf"] = [variant("explicit", {"text_span": quote}), variant("inferred", {})]
        return schema


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

    @classmethod
    def model_json_schema(cls, *args, **kwargs):
        """The provider sees the strict-mode form; validation is unchanged (Log 208)."""
        return strict_json_schema(super().model_json_schema(*args, **kwargs))

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


class SemanticDiscriminator(BaseModel):
    """A narrow, evidence-backed tie-break among already compatible capabilities."""

    model_config = ConfigDict(extra="forbid")

    selection_tags: list[str] = Field(default_factory=list, max_length=8)
    evidence: list[OutcomeEvidence] = Field(default_factory=list, max_length=8)

    @field_validator("selection_tags")
    @classmethod
    def _registered_tags_only(cls, values: list[str]) -> list[str]:
        unknown = set(values) - set(SELECTION_TAG_GLOSSARY)
        if unknown:
            raise ValueError(f"Unknown semantic discriminator tags: {sorted(unknown)}")
        return list(dict.fromkeys(values))

    @model_validator(mode="after")
    def _evidence_matches_tags(self):
        tags = set(self.selection_tags)
        for item in self.evidence:
            if item.dimension != "selection_tag":
                raise ValueError("Semantic discriminator evidence must use selection_tag")
            if item.value not in tags:
                raise ValueError("Semantic discriminator evidence must support a selected tag")
        if tags and not tags.issubset({item.value for item in self.evidence}):
            raise ValueError("Every selected discriminator tag requires evidence")
        return self


class ConditionClaim(BaseModel):
    """One offered experimental condition the request states, with its quote."""

    model_config = ConfigDict(extra="forbid")

    condition: str = Field(
        max_length=80,
        description="One condition id exactly as offered in the option list.",
    )
    text_span: str = Field(
        min_length=1,
        max_length=300,
        description="Exact original-language quote from the request that states it.",
    )


class MethodPreference(BaseModel):
    """A model's advisory comparison of already-qualified algorithm philosophies."""

    model_config = ConfigDict(extra="forbid")

    action: RecommendedAction
    selection_tags: list[str] = Field(min_length=1, max_length=8)
    text_spans: list[str] = Field(default_factory=list, max_length=4)
    rationale: str = Field(min_length=1, max_length=600)
    assumptions: list[str] = Field(default_factory=list, max_length=4)

    @model_validator(mode="after")
    def _supported_or_conditional(self):
        if not self.text_spans and not self.assumptions:
            raise ValueError("A preference needs request quotes or explicit assumptions")
        return self


class MethodCapabilityGap(BaseModel):
    """A requested registered philosophy absent from the qualified candidates."""

    model_config = ConfigDict(extra="forbid")
    selection_tags: list[str] = Field(min_length=1, max_length=8)
    text_spans: list[str] = Field(min_length=1, max_length=4)
    rationale: str = Field(min_length=1, max_length=600)


class SelectionConditionClaims(BaseModel):
    """Experimental conditions stated in the request (Log 139); may be empty."""

    model_config = ConfigDict(extra="forbid")

    claims: list[ConditionClaim] = Field(default_factory=list, max_length=6)
    preference: MethodPreference | None = None
    capability_gap: MethodCapabilityGap | None = None


class AdvisoryCondition(BaseModel):
    """A validated, quoted experimental condition behind a recommendation."""

    model_config = ConfigDict(extra="forbid")

    axis: str
    value: str
    text_span: str


class AdvisoryRecommendation(BaseModel):
    """An advisory preference among tied candidates; never execution authority."""

    model_config = ConfigDict(extra="forbid")

    action: RecommendedAction
    conditions: list[AdvisoryCondition] = Field(default_factory=list, max_length=6)
    rationale: str = Field(default="", max_length=600)
    supporting_spans: list[str] = Field(default_factory=list, max_length=4)
    assumptions: list[str] = Field(default_factory=list, max_length=4)

    @model_validator(mode="after")
    def _recommendation_has_basis(self):
        if not self.conditions and not self.rationale:
            raise ValueError("An advisory recommendation requires a stated basis")
        return self


class ConcernClaim(BaseModel):
    """One offered practical concern the request states, with its quote (Log 223)."""

    model_config = ConfigDict(extra="forbid")

    concern: str = Field(
        max_length=80,
        description="One concern id exactly as offered in the option list.",
    )
    text_span: str = Field(
        min_length=1,
        max_length=300,
        description="Exact original-language quote from the request that states it.",
    )


class StatedConcernClaims(BaseModel):
    """Practical concerns stated in the request (Log 223); may be empty."""

    model_config = ConfigDict(extra="forbid")

    claims: list[ConcernClaim] = Field(default_factory=list, max_length=6)


class AddressedConcern(BaseModel):
    """A quoted, offered concern that a guidance reply answers from the registry."""

    model_config = ConfigDict(extra="forbid")

    action: RecommendedAction
    concern: str
    text_span: str


class HypothesisBasisClaim(BaseModel):
    """One offered hypothesis basis the request states, with its quote (Log 254)."""

    model_config = ConfigDict(extra="forbid")

    basis: str = Field(
        max_length=80,
        description="One basis id exactly as offered in the option list.",
    )
    text_span: str = Field(
        min_length=1,
        max_length=300,
        description="Exact original-language quote from the request that states this hypothesis.",
    )
    target_artifact: ArtifactType = "unknown"
    target_granularity: Granularity = "unknown"


class StatedHypothesisClaims(BaseModel):
    """Hypothesis bases stated in the request (Log 254); may be empty."""

    model_config = ConfigDict(extra="forbid")

    question_mode: Literal["single_goal", "multiple_hypotheses", "unclear_goal"] = "single_goal"
    claims: list[HypothesisBasisClaim] = Field(default_factory=list, max_length=24)
    concerns: list[ConcernClaim] = Field(default_factory=list, max_length=6)


class StatedHypothesis(BaseModel):
    """A quoted, offered hypothesis basis that the reply presents as its own route."""

    model_config = ConfigDict(extra="forbid")

    axis: str
    basis: str
    text_span: str
    target_artifact: ArtifactType = "unknown"
    target_granularity: Granularity = "unknown"


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
