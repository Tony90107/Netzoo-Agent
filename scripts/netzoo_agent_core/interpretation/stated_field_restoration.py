"""Restore stated values and artifact-entailed scalar fields.

This is the one place the deterministic layer writes an outcome field, and the
rules are narrow: it may **move** a value the hypothesis wrote in its own
evidence, restore roles from one or more explicit current regulator-to-target
phrases together with their entailed entity types, infer or correct an
artifact only when those explicit roles have exactly one ontology-supported
artifact, restore a single explicit granularity witness, or align an
under-specified or impossible scalar to the sole value declared by the already
selected artifact. It never selects a workflow.

The failure it repairs was the largest single family in the live record on both
models: the model says the same thing twice, in evidence and in the outcome
fields, and any mismatch rejects the whole interpretation. It cites the input
artifact and leaves `input_artifacts` empty; it cites `regulator_type=mirna` and
leaves `regulator_types` empty. The run then falls back to a registry guess
carrying no outcome at all.

Six structural guarantees, not promises:

1. A moved candidate must appear in this hypothesis's own evidence under the
   matching dimension, except for closed current role-pair and granularity
   witnesses. An entity can also be added when it is entailed by a supported
   regulatory role. An artifact can be inferred or corrected only from
   explicit roles when the output ontology leaves exactly one possibility and
   no grounded explicit evidence contradicts it. Nothing is derived from a
   tool name or from the registry.
2. `input_artifact` additionally requires the request's own witnesses to have
   scoped that artifact as current -- two independent sources. Role fields may
   be restored only from closed current role-pair witnesses; selection tags
   are only ever moved. A moved tag is reported back so the caller can keep it
   out of capability selection: the matcher may break a tie with a tag the
   model itself placed in the outcome, and a tag this function moved must never
   pick a tool.
3. `unknown` is never written.
4. The result is re-validated through `RequestedOutcome.model_validate`, not
   copied past validation, so a value outside the closed vocabulary cannot be
   written at all.
5. A candidate is applied only if it removes no fewer consistency issues than it
   creates: any addition that introduces a new `outcome_consistency_issues`
   entry is reverted individually.
6. Ontology alignment applies only where the selected artifact declares exactly
   one operation or granularity. It can run after a field-scoped review patch or
   be restricted to an explicit artifact allowlist when a deterministic goal
   witness supports that artifact. The artifact choice remains subject to its
   own strict evidence validation, so filling a dependent scalar cannot make an
   unsupported artifact pass. Conflicting evidence is retired and reported.

Historical input mentions cannot arrive here: a past-scoped clause yields
`noncurrent_input`, the opposite direction. Ordinary restoration only adds
values stated by a closed current witness or entailed by supported role
evidence. Artifact alignment may replace operation/granularity and retire
evidence that directly contradicts the artifact's sole legal value; each such
change is traced, and the result faces identical strict validation.
"""

from __future__ import annotations

import re

from ..contracts.artifact_semantics import (
    ARTIFACT_SEMANTICS,
    artifacts_supporting_regulatory_roles,
    outcome_consistency_issues,
)
from ..contracts.outcomes import OutcomeEvidence, RequestedOutcome, SemanticInterpretation
from ..contracts.repair_scope import DIMENSION_BY_FIELD
from .outcome_validation import explicit_evidence_grounded
from .request_integrity import (
    granularity_mentions,
    input_mentions,
    regulatory_role_mentions,
)

__all__ = ["restore_stated_fields"]

_UNKNOWN = "unknown"
_ROLE_DIMENSIONS = frozenset(
    {"regulator_type", "regulator_types", "target_type", "target_types"}
)
_REGULATORY_ARTIFACTS = frozenset({
    "regulatory_network",
    "regulatory_network_and_tf_activity",
    "signed_regulatory_effect_network",
})
# (evidence dimension, outcome field). Order is the order candidates are tried.
_MOVABLE = (
    ("input_artifact", "input_artifacts"),
    ("regulator_type", "regulator_types"),
    ("target_type", "target_types"),
    ("selection_tag", "selection_tags"),
)


#: A result named as modules or communities of a network's nodes (Log 300).
_STATED_PARTITION = re.compile(r"\b(?:modules?|communit(?:y|ies))\b", re.I)
#: A clause that describes what the user already holds, not what to produce.
_HELD = re.compile(r"\b(?:i|we)\s+(?:already\s+)?(?:have|hold|got|obtained)\b|\balready\b|\bexisting\b", re.I)


def _stated_partition(user_task: str) -> str | None:
    """The quoted module or community result, if the request asks for one."""
    for sentence in re.split(r"[.;!?\n]", user_task):
        match = _STATED_PARTITION.search(sentence)
        if match and not _HELD.search(sentence):
            start = max(0, sentence.rfind(" ", 0, max(0, match.start() - 1)) + 1)
            return sentence[start:match.end()].strip()
    return None


def _witnessed_current(user_task: str) -> dict[str, str]:
    witnessed: dict[str, str] = {}
    for item in input_mentions(user_task):
        if item.status == "current" and item.artifact != _UNKNOWN:
            witnessed.setdefault(item.artifact, item.text_span)
    return witnessed


def _with_value(outcome: RequestedOutcome, field: str, value: str) -> RequestedOutcome | None:
    """Re-validate rather than copy past validation; None when the value cannot be written."""
    payload = outcome.model_dump()
    payload[field] = [*payload[field], value]
    try:
        return RequestedOutcome.model_validate(payload)
    except Exception:
        return None


def _without_roles(outcome: RequestedOutcome) -> RequestedOutcome | None:
    payload = outcome.model_dump()
    payload["regulator_types"] = []
    payload["target_types"] = []
    payload["unresolved_dimensions"] = [
        item for item in payload["unresolved_dimensions"]
        if item not in _ROLE_DIMENSIONS
    ]
    try:
        return RequestedOutcome.model_validate(payload)
    except Exception:
        return None


def _without_sample_entity(
    task: str,
    outcome: RequestedOutcome,
) -> RequestedOutcome | None:
    """Keep sample counts as observation metadata, not network nodes.

    ``sample_specific`` means one separately inferred network per sample; the
    nodes in each gene-gene or multi-omic feature network are still features.
    This normalization does not select a workflow. It only removes the
    ``sample`` entity when a semantic review incorrectly promoted sample count
    or sample indexing to a network node.
    """
    if outcome.artifact_type == "multi_omic_network":
        eligible = "sample" in outcome.entity_types
    elif outcome.artifact_type in {
        "regulatory_network", "signed_regulatory_effect_network",
    }:
        # A regulator-to-target network's nodes are regulators and targets; no
        # capability producing either artifact declares `sample`. “每位病患”
        # was read as a node in every legacy trial of one traced round, which
        # made a complete per-patient request unsupported. The TF-activity
        # artifact is excluded: its TF-by-sample matrix really has sample rows.
        eligible = "sample" in outcome.entity_types
    else:
        eligible = (
            re.search(r"\b(?:sparsif(?:y|ied|ication)|sparse)\b|稀疏化|稀疏", task, re.I)
            and re.search(r"\bp[- ]?values?\b|p值", task, re.I)
            and outcome.artifact_type == "coexpression_network"
            and outcome.granularity == "sample_specific"
            and "gene" in outcome.entity_types
            and "sample" in outcome.entity_types
        )
    if not eligible:
        return None
    payload = outcome.model_dump()
    payload["entity_types"] = [
        value for value in payload["entity_types"] if value != "sample"
    ]
    payload["unresolved_dimensions"] = [
        value for value in payload["unresolved_dimensions"]
        if value != "entity_type"
    ]
    try:
        return RequestedOutcome.model_validate(payload)
    except Exception:
        return None


def _with_scalar(outcome: RequestedOutcome, field: str, value: str) -> RequestedOutcome | None:
    payload = outcome.model_dump()
    payload[field] = value
    payload["unresolved_dimensions"] = [
        item for item in payload["unresolved_dimensions"]
        if item != DIMENSION_BY_FIELD[field]
    ]
    try:
        return RequestedOutcome.model_validate(payload)
    except Exception:
        return None


def _with_explicit_roles(
    outcome: RequestedOutcome,
    roles: tuple[tuple[str, str], ...],
) -> RequestedOutcome | None:
    """Restore all roles witnessed by closed explicit phrases as one change.

    Regulatory outcomes require every declared role to also appear in
    ``entity_types``. Applying a coordinated phrase one regulator at a time
    creates an invalid intermediate outcome (the other regulator is then
    missing from its entities), so no individual restoration can pass strict
    consistency checks. Treat the phrase's complete role set as one atomic
    update.
    """
    roles = tuple(dict.fromkeys(roles))
    if not roles:
        return None
    payload = outcome.model_dump()
    for field, values_to_add in (
        ("regulator_types", tuple(regulator for regulator, _ in roles)),
        ("target_types", tuple(target for _, target in roles)),
    ):
        # A closed phrase such as “miRNA 對基因” resolves an unknown in that
        # same role dimension. Preserve other known values in multi-role requests.
        values = [item for item in payload[field] if item != _UNKNOWN]
        for value in values_to_add:
            if value not in values:
                values.append(value)
        payload[field] = values
    for entity in dict.fromkeys(
        value for regulator, target in roles for value in (regulator, target)
    ):
        if entity not in payload["entity_types"]:
            payload["entity_types"].append(entity)
    payload["unresolved_dimensions"] = [
        item for item in payload["unresolved_dimensions"]
        if item not in _ROLE_DIMENSIONS and item != "entity_type"
    ]
    try:
        return RequestedOutcome.model_validate(payload)
    except Exception:
        return None


def _with_role_entity(
    outcome: RequestedOutcome,
    dimension: str,
    value: str,
) -> RequestedOutcome | None:
    """Move one supported role and its entailed entity as a single change."""
    if value == _UNKNOWN:
        return None
    field = "regulator_types" if dimension == "regulator_type" else "target_types"
    payload = outcome.model_dump()
    values = [item for item in payload[field] if item != _UNKNOWN]
    if value not in values:
        values.append(value)
    payload[field] = values
    if value not in payload["entity_types"]:
        payload["entity_types"].append(value)
    payload["unresolved_dimensions"] = [
        item for item in payload["unresolved_dimensions"]
        if item not in _ROLE_DIMENSIONS and item != "entity_type"
    ]
    try:
        return RequestedOutcome.model_validate(payload)
    except Exception:
        return None


def _with_supported_role_entities(
    outcome: RequestedOutcome,
    evidence: list[OutcomeEvidence],
) -> tuple[RequestedOutcome | None, list[str]]:
    """Add entities entailed by already supported regulatory roles."""
    if outcome.artifact_type not in _REGULATORY_ARTIFACTS:
        return None, []
    supported = {
        (item.dimension, item.value)
        for item in evidence
        if item.dimension in {"regulator_type", "target_type"}
        and item.value != _UNKNOWN
    }
    payload = outcome.model_dump()
    added = []
    for field, dimension in (
        ("regulator_types", "regulator_type"),
        ("target_types", "target_type"),
    ):
        for value in payload[field]:
            if (
                value != _UNKNOWN
                and (dimension, value) in supported
                and value not in payload["entity_types"]
            ):
                payload["entity_types"].append(value)
                added.append(value)
    if not added:
        return None, []
    try:
        return RequestedOutcome.model_validate(payload), added
    except Exception:
        return None, []


def restore_stated_fields(
    user_task: str, interpretation: SemanticInterpretation,
    *, align_artifact_constraints: bool = False,
    align_artifact_constraints_for: frozenset[str] = frozenset(),
    restore_explicit_scalar_evidence: bool = False,
) -> tuple[SemanticInterpretation, list[dict[str, object]]]:
    """Return stated values and unique role-based artifact fixes, plus a record."""
    witnessed = _witnessed_current(user_task)
    restored: list[dict[str, object]] = []
    hypotheses = []
    for index, hypothesis in enumerate(interpretation.outcome_hypotheses):
        outcome = hypothesis.outcome
        evidence = list(hypothesis.evidence)
        unwitnessed_inputs = set(outcome.input_artifacts) - set(witnessed)
        if unwitnessed_inputs:
            payload = outcome.model_dump()
            payload["input_artifacts"] = [
                value for value in payload["input_artifacts"]
                if value not in unwitnessed_inputs
            ]
            candidate = RequestedOutcome.model_validate(payload)
            evidence = [
                item for item in evidence
                if not (
                    item.dimension == "input_artifact"
                    and item.value in unwitnessed_inputs
                )
            ]
            for value in sorted(unwitnessed_inputs):
                restored.append({
                    "hypothesis": index,
                    "field": "input_artifacts",
                    "value": value,
                    "source": "removed_without_current_input_witness",
                    "witnessed_span": None,
                })
            outcome = candidate
        partition = (
            _stated_partition(user_task)
            if len(interpretation.outcome_hypotheses) == 1 and outcome.artifact_type == _UNKNOWN else None
        )
        if partition is not None:
            # Log 300: "Which workflow finds gene modules within each patient?"
            # read as an unknown result; the request names it.
            candidate = _without_roles(outcome.model_copy(update={"artifact_type": "community_assignment"}))
            if candidate is not None and not set(outcome_consistency_issues(candidate)) - {
                "artifact_granularity:community_assignment"
            }:
                evidence = [item for item in evidence if item.dimension != "artifact_type"] + [OutcomeEvidence(
                    dimension="artifact_type", value="community_assignment", source="explicit",
                    text_span=partition,
                    rationale="The request names modules or communities, the ontology's community assignment.",
                )]
                restored.append({
                    "hypothesis": index, "field": "artifact_type", "value": "community_assignment",
                    "previous_value": _UNKNOWN, "source": "stated_partition_entailment",
                    "witnessed_span": partition,
                })
                outcome = candidate
        baseline = set(outcome_consistency_issues(outcome))
        granularity_witnesses = (
            {
                mention.granularity: mention.text_span
                for mention in granularity_mentions(user_task)
            }
            if restore_explicit_scalar_evidence else {}
        )
        if len(granularity_witnesses) == 1:
            witnessed_granularity, witnessed_span = next(
                iter(granularity_witnesses.items())
            )
            if outcome.granularity == _UNKNOWN:
                candidate = _with_scalar(
                    outcome, "granularity", witnessed_granularity
                )
                if candidate is not None:
                    outcome = candidate
                    restored.append({
                        "hypothesis": index,
                        "field": "granularity",
                        "value": witnessed_granularity,
                        "source": "explicit_granularity_witness",
                        "witnessed_span": witnessed_span,
                    })
            # A same-value entry that is inferred, or quotes text the request
            # does not contain, used to block the witness. The value was then
            # stated, verbatim, yet read as unstated -- and the matcher, which
            # only lets stated dimensions make a match exact, tied LIONESS-PUMA
            # with PUMA on requests saying “每位病患”. The witness's own quote
            # replaces such an entry; a grounded explicit entry is kept as is.
            weaker = [
                item for item in evidence
                if item.dimension == "granularity"
                and item.value == witnessed_granularity
                and not explicit_evidence_grounded(user_task, item)
            ]
            if outcome.granularity == witnessed_granularity and weaker and not any(
                item.dimension == "granularity"
                and item.value == witnessed_granularity
                and explicit_evidence_grounded(user_task, item)
                for item in evidence
            ):
                evidence = [item for item in evidence if item not in weaker]
            if (
                outcome.granularity == witnessed_granularity
                and not any(
                    item.dimension == "granularity"
                    and item.value == witnessed_granularity
                    for item in evidence
                )
                and len(evidence) < 12
            ):
                evidence.append(OutcomeEvidence(
                    dimension="granularity",
                    value=witnessed_granularity,
                    source="explicit",
                    text_span=witnessed_span,
                    rationale=(
                        "The request explicitly states the output granularity."
                    ),
                ))
                restored.append({
                    "hypothesis": index,
                    "field": "granularity_evidence",
                    "value": witnessed_granularity,
                    "source": "explicit_granularity_witness",
                    "witnessed_span": witnessed_span,
                })
        role_mentions = regulatory_role_mentions(user_task)
        if role_mentions:
            explicit_roles = tuple(
                (mention.regulator_type, mention.target_type)
                for mention in role_mentions
            )
            role_artifacts = artifacts_supporting_regulatory_roles(
                explicit_roles
            )
            candidate = _with_explicit_roles(
                outcome, explicit_roles,
            )
            inferred_artifact = None
            matching_artifact_evidence = False
            conflicting_artifact_evidence = []
            if candidate is not None and len(role_artifacts) == 1:
                role_artifact = next(iter(role_artifacts))
                matching_artifact_evidence = any(
                    item.dimension == "artifact_type"
                    and item.value == role_artifact
                    for item in evidence
                )
                conflicting_artifact_evidence = [
                    item for item in evidence
                    if item.dimension == "artifact_type"
                    and item.value not in {_UNKNOWN, role_artifact}
                ]
                grounded_conflicting_artifact = any(
                    item.dimension == "artifact_type"
                    and item.value not in {_UNKNOWN, role_artifact}
                    and explicit_evidence_grounded(user_task, item)
                    for item in conflicting_artifact_evidence
                )
                if outcome.artifact_type != role_artifact:
                    evidence_after_retiring_conflict = (
                        len(evidence) - len(conflicting_artifact_evidence)
                    )
                    if grounded_conflicting_artifact or (
                        not matching_artifact_evidence
                        and evidence_after_retiring_conflict >= 12
                    ):
                        candidate = None
                    else:
                        candidate = _with_scalar(
                            candidate, "artifact_type", role_artifact,
                        )
                        if candidate is not None:
                            inferred_artifact = role_artifact
            if candidate is not None and not (
                set(outcome_consistency_issues(candidate)) - baseline
            ):
                previous_outcome = outcome
                if candidate != previous_outcome:
                    for mention in role_mentions:
                        if (
                            mention.regulator_type not in previous_outcome.regulator_types
                            or mention.target_type not in previous_outcome.target_types
                        ):
                            restored.append({
                                "hypothesis": index,
                                "field": "roles",
                                "value": (
                                    f"{mention.regulator_type}-to-{mention.target_type}"
                                ),
                                "source": "explicit_role_witness",
                                "witnessed_span": mention.text_span,
                            })
                    # `_with_explicit_roles` also retires `unknown` entries in
                    # role dimensions that the request closes. When the known
                    # role was already present, the loop above records no
                    # addition; without a record here the final no-op guard
                    # below would discard the corrected outcome.
                    for field in ("regulator_types", "target_types"):
                        before = getattr(previous_outcome, field)
                        after = getattr(candidate, field)
                        if _UNKNOWN in before and _UNKNOWN not in after:
                            restored.append({
                                "hypothesis": index,
                                "field": "roles",
                                "value": f"resolved_placeholder:{field}",
                                "previous_value": list(before),
                                "source": "explicit_role_witness",
                                "witnessed_span": "; ".join(dict.fromkeys(
                                    mention.text_span for mention in role_mentions
                                )),
                            })
                    outcome = candidate
                    baseline = set(outcome_consistency_issues(outcome))
                    if inferred_artifact is not None:
                        if conflicting_artifact_evidence:
                            evidence = [
                                item for item in evidence
                                if item not in conflicting_artifact_evidence
                            ]
                            for item in conflicting_artifact_evidence:
                                restored.append({
                                    "hypothesis": index,
                                    "field": "artifact_type_evidence",
                                    "value": item.value,
                                    "source": "removed_conflicting_role_ontology_evidence",
                                    "witnessed_span": item.text_span,
                                })
                        if not matching_artifact_evidence:
                            evidence.append(OutcomeEvidence(
                                dimension="artifact_type",
                                value=inferred_artifact,
                                source="inferred",
                                rationale=(
                                    "The explicit regulator-to-target roles leave exactly "
                                    "one artifact under the output ontology."
                                ),
                            ))
                        restored.append({
                            "hypothesis": index,
                            "field": "artifact_type",
                            "value": inferred_artifact,
                            "previous_value": previous_outcome.artifact_type,
                            "source": (
                                "unique_role_ontology_entailment"
                                if previous_outcome.artifact_type == _UNKNOWN
                                else "unique_role_ontology_correction"
                            ),
                            "witnessed_span": None,
                        })
                for mention in role_mentions:
                    for dimension, value in (
                        ("regulator_type", mention.regulator_type),
                        ("target_type", mention.target_type),
                    ):
                        grounded = any(
                            item.dimension == dimension
                            and item.value == value
                            and explicit_evidence_grounded(user_task, item)
                            for item in evidence
                        )
                        if grounded:
                            continue
                        evidence = [
                            item for item in evidence
                            if not (item.dimension == dimension and item.value == value)
                        ]
                        if len(evidence) < 12:
                            evidence.append(OutcomeEvidence(
                                dimension=dimension,
                                value=value,
                                source="explicit",
                                text_span=mention.text_span,
                                rationale=(
                                    "The request explicitly states the bounded "
                                    "regulator-to-target role."
                                ),
                            ))
                            restored.append({
                                "hypothesis": index,
                                "field": f"{dimension}_evidence",
                                "value": value,
                                "source": "explicit_role_witness",
                                "witnessed_span": mention.text_span,
                            })
                    # A supported role also entails the corresponding network
                    # entity. Claims-mode models sometimes leave an explicit
                    # entity quote such as "TF regulation" that is not present
                    # in a coordinated request like "both TF and miRNA
                    # regulation". The role witness supports that entity, so
                    # discard only the ungrounded duplicate entity quote; keep
                    # any independently grounded entity evidence.
                    for value in dict.fromkeys((
                        mention.regulator_type, mention.target_type,
                    )):
                        grounded_entity = any(
                            item.dimension == "entity_type"
                            and item.value == value
                            and explicit_evidence_grounded(user_task, item)
                            for item in evidence
                        )
                        if grounded_entity:
                            continue
                        stale_entity_evidence = [
                            item for item in evidence
                            if item.dimension == "entity_type"
                            and item.value == value
                            and item.source == "explicit"
                        ]
                        if stale_entity_evidence:
                            evidence = [
                                item for item in evidence
                                if item not in stale_entity_evidence
                            ]
                            restored.append({
                                "hypothesis": index,
                                "field": "entity_type_evidence",
                                "value": value,
                                "source": "explicit_role_witness",
                                "witnessed_span": mention.text_span,
                            })
            if (
                len(role_artifacts) == 1
                and outcome.artifact_type in role_artifacts
                and not any(
                    item.dimension == "artifact_type"
                    and item.value == outcome.artifact_type
                    for item in evidence
                )
                and len(evidence) < 12
            ):
                evidence.append(OutcomeEvidence(
                    dimension="artifact_type",
                    value=outcome.artifact_type,
                    source="inferred",
                    rationale=(
                        "The explicit regulator-to-target roles jointly match this "
                        "artifact under the output ontology."
                    ),
                ))
                restored.append({
                    "hypothesis": index,
                    "field": "artifact_type_evidence",
                    "value": outcome.artifact_type,
                    "source": "role_ontology_entailment",
                    "witnessed_span": None,
                })
        supported_entities, added_entities = _with_supported_role_entities(
            outcome, evidence
        )
        if supported_entities is not None and not (
            set(outcome_consistency_issues(supported_entities)) - baseline
        ):
            outcome = supported_entities
            baseline = set(outcome_consistency_issues(outcome))
            for value in added_entities:
                restored.append({
                    "hypothesis": index,
                    "field": "entity_types",
                    "value": value,
                    "source": "supported_role_entailment",
                    "witnessed_span": None,
                })
        normalized_entities = _without_sample_entity(user_task, outcome)
        if normalized_entities is not None:
            evidence = [
                item for item in evidence
                if not (item.dimension == "entity_type" and item.value == "sample")
            ]
            restored.append({
                "hypothesis": index,
                "field": "entity_types",
                "value": "sample",
                "previous_value": list(outcome.entity_types),
                "source": "artifact_ontology",
                "witnessed_span": None,
            })
            outcome = normalized_entities
            baseline = set(outcome_consistency_issues(outcome))
        if (
            align_artifact_constraints
            or outcome.artifact_type in align_artifact_constraints_for
        ):
            rule = ARTIFACT_SEMANTICS[outcome.artifact_type]
            for field, permitted in (
                ("operation", rule.operations),
                ("granularity", rule.granularities),
            ):
                if permitted is None or len(permitted) != 1:
                    continue
                current = getattr(outcome, field)
                entailed = next(iter(permitted))
                dimension = DIMENSION_BY_FIELD[field]
                if current == entailed:
                    continue
                candidate = _with_scalar(outcome, field, entailed)
                if candidate is None:
                    continue
                retired = [
                    item.value for item in evidence
                    if item.dimension == dimension and item.value != entailed
                ]
                evidence = [
                    item for item in evidence
                    if item.dimension != dimension or item.value == entailed
                ]
                if field == "operation" and not any(
                    item.dimension == dimension and item.value == entailed
                    for item in evidence
                ):
                    evidence.append(OutcomeEvidence(
                        dimension="operation",
                        value=entailed,
                        source="inferred",
                        rationale=(
                            "The selected artifact ontology uniquely defines the "
                            "canonical scientific operation."
                        ),
                    ))
                restored.append({
                    "hypothesis": index,
                    "field": field,
                    "value": entailed,
                    "previous_value": current,
                    "source": "artifact_ontology",
                    "witnessed_span": None,
                    "evidence_retired": retired,
                })
                outcome = candidate
                baseline = set(outcome_consistency_issues(outcome))
        # Fields the artifact choice itself made illegal. Clearing them removes
        # `artifact_roles` and can create nothing: a non-regulatory artifact has
        # no legal role, so there is no value here to preserve. This is the
        # deletion half of the authorization, the field-level analogue of
        # retiring evidence a patch made stale.
        if outcome.artifact_type not in {"regulatory_network", _UNKNOWN} and (
            outcome.regulator_types or outcome.target_types
            or _ROLE_DIMENSIONS.intersection(outcome.unresolved_dimensions)
        ):
            cleared = _without_roles(outcome)
            if cleared is not None and not (
                set(outcome_consistency_issues(cleared)) - baseline
            ):
                # Retire the role evidence with the roles (Log 143). Left in
                # place, validation's gap-closing reconcile re-adds the quoted
                # role to the emptied field and `artifact_roles` returns.
                evidence = [
                    item for item in evidence
                    if item.dimension not in {"regulator_type", "target_type"}
                ]
                restored.append({
                    "hypothesis": index,
                    "field": "roles",
                    "value": "cleared",
                    "source": "stale_under_artifact",
                    "witnessed_span": None,
                })
                outcome = cleared
                baseline = set(outcome_consistency_issues(outcome))
        for dimension, field in _MOVABLE:
            stated = [
                item.value for item in hypothesis.evidence
                if item.dimension == dimension and item.value != _UNKNOWN
            ]
            for value in dict.fromkeys(stated):
                if value in getattr(outcome, field):
                    continue
                if dimension == "input_artifact" and value not in witnessed:
                    continue
                source = (
                    "witness_and_evidence" if value in witnessed else "evidence"
                )
                candidate = (
                    _with_role_entity(outcome, dimension, value)
                    if dimension in {"regulator_type", "target_type"}
                    else _with_value(outcome, field, value)
                )
                if candidate is None:
                    continue
                if set(outcome_consistency_issues(candidate)) - baseline:
                    # This move would trade one rejection for another.
                    continue
                outcome = candidate
                restored.append({
                    "hypothesis": index,
                    "field": field,
                    "value": value,
                    "source": source,
                    "witnessed_span": witnessed.get(value),
                })
                if dimension in {"regulator_type", "target_type"}:
                    restored.append({
                        "hypothesis": index,
                        "field": "entity_types",
                        "value": value,
                        "source": "supported_role_entailment",
                        "witnessed_span": None,
                    })
        updates = {}
        if outcome is not hypothesis.outcome:
            updates["outcome"] = outcome
        if evidence != list(hypothesis.evidence):
            updates["evidence"] = evidence
        hypotheses.append(hypothesis if not updates else hypothesis.model_copy(update=updates))
    if not restored:
        return interpretation, []
    return interpretation.model_copy(update={"outcome_hypotheses": hypotheses}), restored
