"""Compatibility predicates for matching typed requests to workflow capabilities."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re

from workflow_registry import OutputCapabilityDefinition

from ..contracts import OutcomeHypothesis, RequestedOutcome
from ..contracts.artifact_semantics import (
    ARTIFACT_COMPONENTS,
    ARTIFACT_SEMANTICS,
    outcome_consistency_issues,
)
from ..interpretation.request_integrity import input_mentions
from .candidate_ranking import _UNKNOWN


def _produced_artifacts(capability: OutputCapabilityDefinition) -> frozenset[str]:
    """Return every artifact a workflow can deliberately expose to the user."""
    return capability.produced_artifacts or frozenset({capability.artifact_type})


def _supported_artifacts(capability: OutputCapabilityDefinition) -> frozenset[str]:
    """Return concrete outputs plus every fully satisfied ontology bundle."""
    produced = _produced_artifacts(capability)
    bundles = {
        artifact
        for artifact, components in ARTIFACT_COMPONENTS.items()
        if components.issubset(produced)
    }
    return produced | {capability.artifact_type} | bundles


def _supported_entities(
    artifact_type: str,
    capability: OutputCapabilityDefinition,
) -> frozenset[str]:
    """Return entity support for the particular artifact being requested."""
    if artifact_type == capability.artifact_type or artifact_type == _UNKNOWN:
        return capability.entity_types
    semantics = ARTIFACT_SEMANTICS.get(artifact_type)
    if artifact_type in _supported_artifacts(capability) and semantics is not None:
        return semantics.entities or capability.entity_types
    return capability.entity_types


def _accepts_inputs(
    outcome: RequestedOutcome,
    capability: OutputCapabilityDefinition,
    available_inputs: Sequence[str] = (),
) -> bool:
    requested = set(outcome.input_artifacts) - {_UNKNOWN}
    # A requested artifact is not evidence that the user actually has it. The
    # separate lexical scope is the only negative evidence used to eliminate a
    # capability whose executor requires an additional prior.
    observed = set(available_inputs) - {_UNKNOWN}
    missing_required = set(capability.required_input_artifacts) - observed
    # A stated miRNA regulator role is itself evidence that the miRNA prior is
    # available. This preserves guidance requests that describe the biological
    # role but omit the file noun; an explicitly TF-only request, however, must
    # not keep PUMA alive when its required miRNA prior is absent.
    if observed and missing_required and not (
        missing_required == {"mirna_prior"}
        and "mirna" in set(outcome.regulator_types)
    ):
        return False
    return (
        requested.issubset(capability.input_artifacts)
        and not requested.intersection(capability.incompatible_input_artifacts)
    )


def explicit_input_artifacts(task: str) -> frozenset[str]:
    """Share the validator's current-input scope, including on fallback paths."""
    artifacts = {
        mention.artifact
        for mention in input_mentions(task)
        if mention.status == "current"
    }
    # Comma-separated bundles such as "miRNA, motif and PPI priors" are split
    # into separate lexical clauses by the temporal scoper. Preserve the
    # bounded bundle witness here, while avoiding a bare "miRNA regulators"
    # phrase that does not establish a prior file.
    if re.search(
        r"\bmi[- ]?RNA\b.{0,80}\b(?:prior|priors|data|matrix|file)\b|"
        r"mi[- ]?RNA.{0,80}(?:先驗|資料|矩陣|檔案)",
        task,
        re.IGNORECASE,
    ):
        artifacts.add("mirna_prior")
    return frozenset(artifacts)


def _is_not_applicable(outcome: RequestedOutcome) -> bool:
    return (
        outcome.operation == _UNKNOWN
        and outcome.artifact_type == _UNKNOWN
        and outcome.granularity == "not_applicable"
        and not outcome.input_artifacts
        and not outcome.entity_types
        and not outcome.regulator_types
        and not outcome.target_types
        and not outcome.unresolved_dimensions
    )


def _has_unknown(outcome: RequestedOutcome) -> bool:
    return bool(
        outcome.unresolved_dimensions
        or _UNKNOWN in {outcome.operation, outcome.artifact_type, outcome.granularity}
        or _UNKNOWN in outcome.entity_types
        or _UNKNOWN in outcome.input_artifacts
        or _UNKNOWN in outcome.regulator_types
        or _UNKNOWN in outcome.target_types
    )


def _matches(
    outcome: RequestedOutcome,
    capability: OutputCapabilityDefinition,
    available_inputs: Sequence[str] = (),
) -> bool:
    if _has_unknown(outcome) or outcome_consistency_issues(outcome):
        return False
    return (
        outcome.operation == capability.operation
        and _accepts_inputs(outcome, capability, available_inputs)
        and outcome.artifact_type in _supported_artifacts(capability)
        and outcome.granularity in capability.granularities
        and set(outcome.entity_types).issubset(
            _supported_entities(outcome.artifact_type, capability)
        )
        and set(outcome.regulator_types).issubset(capability.regulator_types)
        and set(outcome.target_types).issubset(capability.target_types)
    )


def _known_scalar_matches(requested: str, supported: str) -> bool:
    return requested == _UNKNOWN or requested == supported


def _known_set_matches(requested: Sequence[str], supported: frozenset[str]) -> bool:
    known = set(requested) - {_UNKNOWN}
    return known.issubset(supported)


def _partially_compatible(
    outcome: RequestedOutcome,
    capability: OutputCapabilityDefinition,
    available_inputs: Sequence[str] = (),
) -> bool:
    return (
        _known_scalar_matches(outcome.operation, capability.operation)
        and _accepts_inputs(outcome, capability, available_inputs)
        and (
            outcome.artifact_type == _UNKNOWN
            or outcome.artifact_type in _supported_artifacts(capability)
        )
        and (
            outcome.granularity == _UNKNOWN
            or outcome.granularity in capability.granularities
        )
        and _known_set_matches(
            outcome.entity_types,
            _supported_entities(outcome.artifact_type, capability),
        )
        and _known_set_matches(outcome.regulator_types, capability.regulator_types)
        and _known_set_matches(outcome.target_types, capability.target_types)
    )


def _complete_guidance_match(outcome, capability) -> bool:
    """Only explanatory operation may be omitted for an exact guidance match."""
    return _matches(
        outcome.model_copy(update={
            "operation": capability.operation,
            "unresolved_dimensions": [
                value for value in outcome.unresolved_dimensions if value != "operation"
            ],
        }),
        capability,
    )


def _explicit_evidence_values(
    hypothesis: OutcomeHypothesis,
) -> dict[str, set[str]]:
    """Group user-quoted semantic constraints independently of model inferences."""
    grouped: dict[str, set[str]] = {}
    for item in hypothesis.evidence:
        if item.source != "explicit" or item.value == _UNKNOWN:
            continue
        grouped.setdefault(item.dimension, set()).add(item.value)
    return grouped


def _matches_explicit_evidence(
    evidence: Mapping[str, set[str]],
    capability: OutputCapabilityDefinition,
) -> bool:
    """Treat explicit user evidence as hard constraints on registry capabilities."""
    requested_artifacts = evidence.get("artifact_type", set())
    evidence_artifact = (
        next(iter(requested_artifacts))
        if len(requested_artifacts) == 1
        else _UNKNOWN
    )
    scalar_constraints = (
        ("operation", {capability.operation}),
        ("input_artifact", set(capability.input_artifacts) - set(capability.incompatible_input_artifacts)),
        ("artifact_type", set(_supported_artifacts(capability))),
        ("granularity", set(capability.granularities)),
        ("entity_type", set(_supported_entities(evidence_artifact, capability))),
        ("regulator_type", set(capability.regulator_types)),
        ("target_type", set(capability.target_types)),
    )
    return all(
        not evidence.get(dimension)
        or evidence[dimension].issubset(supported)
        for dimension, supported in scalar_constraints
    )


__all__ = [
    "_accepts_inputs",
    "_complete_guidance_match",
    "_has_unknown",
    "_is_not_applicable",
    "_known_scalar_matches",
    "_known_set_matches",
    "_matches",
    "_matches_explicit_evidence",
    "_explicit_evidence_values",
    "_partially_compatible",
    "_produced_artifacts",
    "_supported_artifacts",
    "_supported_entities",
    "explicit_input_artifacts",
]
