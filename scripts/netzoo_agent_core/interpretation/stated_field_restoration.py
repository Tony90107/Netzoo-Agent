"""Restore stated values and artifact-entailed scalar fields.

This is the one place the deterministic layer writes an outcome field, and the
rules are narrow: it may **move** a value the hypothesis wrote in its own
evidence, restore roles from one explicit current ``TF-to-gene`` or
``miRNA-to-gene`` phrase together with their entailed entity types, restore a
single explicit granularity witness, or align an under-specified or impossible
scalar to the sole value declared by the already selected artifact. It never
selects an artifact or workflow.

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
   regulatory role. Nothing is derived from a tool name or from the registry.
2. `input_artifact` additionally requires the request's own witnesses to have
   scoped that artifact as current -- two independent sources. Role fields may
   be restored only from one closed current role-pair witness; selection tags
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
6. After a field-scoped review patch, ontology alignment applies only where the
   selected artifact declares exactly one operation or granularity. The artifact
   choice remains subject to its own strict evidence validation, so filling a
   dependent scalar cannot make an unsupported artifact pass. Conflicting
   evidence is retired and reported.

Historical input mentions cannot arrive here: a past-scoped clause yields
`noncurrent_input`, the opposite direction. Ordinary restoration only adds
values stated by a closed current witness or entailed by supported role
evidence. Artifact alignment may replace operation/granularity and retire
evidence that directly contradicts the artifact's sole legal value; each such
change is traced, and the result faces identical strict validation.
"""

from __future__ import annotations

import re

from ..contracts.artifact_semantics import ARTIFACT_SEMANTICS, outcome_consistency_issues
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
    regulator: str,
    target: str,
) -> RequestedOutcome | None:
    """Fill only missing roles/entities from one closed explicit role phrase."""
    payload = outcome.model_dump()
    for field, value in (
        ("regulator_types", regulator),
        ("target_types", target),
    ):
        # A closed phrase such as “miRNA 對基因” resolves an unknown in that
        # same role dimension. Preserve other known values in multi-role requests.
        values = [item for item in payload[field] if item != _UNKNOWN]
        if value not in values:
            values.append(value)
        payload[field] = values
    for entity in (regulator, target):
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
    restore_explicit_scalar_evidence: bool = False,
) -> tuple[SemanticInterpretation, list[dict[str, object]]]:
    """Return the interpretation with stated values moved into place, plus a record."""
    witnessed = _witnessed_current(user_task)
    restored: list[dict[str, object]] = []
    hypotheses = []
    for index, hypothesis in enumerate(interpretation.outcome_hypotheses):
        outcome = hypothesis.outcome
        evidence = list(hypothesis.evidence)
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
        if outcome.artifact_type in _REGULATORY_ARTIFACTS | {_UNKNOWN}:
            role_mentions = regulatory_role_mentions(user_task)
            if len(role_mentions) == 1:
                mention = role_mentions[0]
                candidate = _with_explicit_roles(
                    outcome, mention.regulator_type, mention.target_type,
                )
                if candidate is not None and not (
                    set(outcome_consistency_issues(candidate)) - baseline
                ):
                    changed = candidate != outcome
                    if changed:
                        for dimension, value in (
                            ("regulator_type", mention.regulator_type),
                            ("target_type", mention.target_type),
                        ):
                            if not any(
                                item.dimension == dimension and item.value == value
                                for item in evidence
                            ) and len(evidence) < 12:
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
                            "field": "roles",
                            "value": (
                                f"{mention.regulator_type}-to-{mention.target_type}"
                            ),
                            "source": "explicit_role_witness",
                            "witnessed_span": mention.text_span,
                        })
                        outcome = candidate
                        baseline = set(outcome_consistency_issues(outcome))
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
        if align_artifact_constraints:
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
