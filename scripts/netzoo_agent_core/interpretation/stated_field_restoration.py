"""Restore stated values and artifact-entailed scalar fields.

This is the one place the deterministic layer writes an outcome field, and the
rules are narrow: it may **move** a value the hypothesis wrote in its own
evidence, or align an under-specified or impossible scalar to the sole value
declared by the already selected artifact. It never selects an artifact or
workflow.

The failure it repairs was the largest single family in the live record on both
models: the model says the same thing twice, in evidence and in the outcome
fields, and any mismatch rejects the whole interpretation. It cites the input
artifact and leaves `input_artifacts` empty; it cites `regulator_type=mirna` and
leaves `regulator_types` empty. The run then falls back to a registry guess
carrying no outcome at all.

Six structural guarantees, not promises:

1. A candidate value must appear verbatim in this hypothesis's own evidence
   under the matching dimension. Nothing is derived from a tool name, from the
   registry, or from matching the request text.
2. `input_artifact` additionally requires the request's own witnesses to have
   scoped that artifact as current -- two independent sources. Role fields and
   selection tags have no such witness, so they are only ever moved.
   A moved tag is reported back so the caller can keep it out of capability
   selection: the matcher may break a tie with a tag the model itself placed in
   the outcome, and a tag this function moved must never pick a tool.
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
already-stated values. Artifact alignment may replace operation/granularity and
retire evidence that directly contradicts the artifact's sole legal value; each
such change is traced, and the result faces identical strict validation.
"""

from __future__ import annotations

import re

from ..contracts.artifact_semantics import ARTIFACT_SEMANTICS, outcome_consistency_issues
from ..contracts.outcomes import OutcomeEvidence, RequestedOutcome, SemanticInterpretation
from ..contracts.repair_scope import DIMENSION_BY_FIELD
from .request_integrity import input_mentions

__all__ = ["restore_stated_fields"]

_UNKNOWN = "unknown"
_ROLE_DIMENSIONS = frozenset(
    {"regulator_type", "regulator_types", "target_type", "target_types"}
)
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


def restore_stated_fields(
    user_task: str, interpretation: SemanticInterpretation,
    *, align_artifact_constraints: bool = False,
) -> tuple[SemanticInterpretation, list[dict[str, object]]]:
    """Return the interpretation with stated values moved into place, plus a record."""
    witnessed = _witnessed_current(user_task)
    restored: list[dict[str, object]] = []
    hypotheses = []
    for index, hypothesis in enumerate(interpretation.outcome_hypotheses):
        outcome = hypothesis.outcome
        evidence = list(hypothesis.evidence)
        baseline = set(outcome_consistency_issues(outcome))
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
                candidate = _with_value(outcome, field, value)
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
        updates = {}
        if outcome is not hypothesis.outcome:
            updates["outcome"] = outcome
        if evidence != list(hypothesis.evidence):
            updates["evidence"] = evidence
        hypotheses.append(hypothesis if not updates else hypothesis.model_copy(update=updates))
    if not restored:
        return interpretation, []
    return interpretation.model_copy(update={"outcome_hypotheses": hypotheses}), restored
