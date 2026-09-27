"""Compatibility predicates for matching typed requests to workflow capabilities."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import re

from workflow_registry import OutputCapabilityDefinition

from ..contracts import OutcomeHypothesis, RequestedOutcome
from ..contracts.artifact_semantics import (
    is_outcome_not_applicable as _is_not_applicable,
    ARTIFACT_COMPONENTS,
    ARTIFACT_SEMANTICS,
    outcome_consistency_issues,
)
from ..interpretation.request_integrity import (
    _CURRENT,
    _HISTORY,
    _scoped_clauses,
    input_mentions,
)
from .candidate_ranking import _UNKNOWN


_MIRNA_PRIOR = re.compile(
    r"\bmi[- ]?RNA\b(?:\s+(?:prior|priors|list|file)\b|"
    r"\s*(?:先驗|清單|列表|檔案)|"
    r"[^。！？!?;；\n]{0,48}(?:\b(?:motif|PPI)\b"
    r"[^。！？!?;；\n]{0,24}\bpriors?\b|先驗))",
    re.IGNORECASE,
)
_NEGATED_INPUT = re.compile(
    r"\b(?:no|not|without|don't|do not|doesn't|does not|never)\b|"
    r"沒有|不需要|無|非",
    re.IGNORECASE,
)
_PRIOR_PATTERNS = {
    "mirna_prior": _MIRNA_PRIOR,
    "motif_prior": re.compile(
        r"\b(?:TF[- ]?)?motifs?\b(?:\s+(?:priors?|data|file|matrix)\b|"
        r"[^。！？!?;；\n]{0,40}\bPPI\b[^。！？!?;；\n]{0,24}\bpriors?\b)|"
        r"(?:TF[- ]?)?motif[^。！？!?;；\n]{0,12}先驗",
        re.IGNORECASE,
    ),
    "ppi_prior": re.compile(
        r"\bPPI\b(?:\s+(?:priors?|data|network|matrix|file)\b)?|"
        r"\bprotein[- ]protein interaction(?:s|\s+(?:priors?|data|network|matrix))?\b|"
        r"(?:蛋白質交互作用|蛋白質互作)[^。！？!?;；\n]{0,12}(?:先驗|網路|資料|矩陣)?",
        re.IGNORECASE,
    ),
}
_MIRNA_SHARED_PRIOR_BUNDLE = re.compile(
    r"\bmi[- ]?RNA\b\s*[,，][^。！？!?;；\n]{0,64}\b(?:motif|PPI)\b"
    r"[^。！？!?;；\n]{0,32}\bpriors?\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class InputAvailability:
    """Three-state input evidence: present, absent, or unmentioned/unknown."""

    present: frozenset[str] = frozenset()
    absent: frozenset[str] = frozenset()

    def status(self, artifact: str) -> str:
        if artifact in self.present:
            return "present"
        if artifact in self.absent:
            return "absent"
        return "unknown"


InputAvailabilityLike = InputAvailability | Sequence[str]


def _as_input_availability(value: InputAvailabilityLike) -> InputAvailability:
    if isinstance(value, InputAvailability):
        return value
    return InputAvailability(present=frozenset(value) - {_UNKNOWN})


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
    granularity: str = _UNKNOWN,
) -> frozenset[str]:
    """Return entity support for the particular artifact being requested.

    In a sample-specific request, ``sample`` names the granularity axis -- one
    result per sample -- not a node type of the result. A capability that
    declares ``sample_specific`` already supports that axis, so it supports the
    entity for that request (Log 136). The capability declaration itself is
    unchanged, which keeps the ranking terms of Log 133/135 untouched.
    """
    if artifact_type == capability.artifact_type or artifact_type == _UNKNOWN:
        supported = capability.entity_types
    else:
        semantics = ARTIFACT_SEMANTICS.get(artifact_type)
        if artifact_type in _supported_artifacts(capability) and semantics is not None:
            supported = semantics.entities or capability.entity_types
        else:
            supported = capability.entity_types
    if artifact_type == "community_assignment" and "regulatory_network" in capability.input_artifacts:
        # Log 202: the communities partition the nodes of the network analyzed,
        # and a regulator-gene network's nodes are its regulators and genes.
        # A reading naming both sides ("groups of regulators that jointly
        # control groups of genes") had no candidate at all. The declaration
        # is unchanged, which keeps the ranking terms of Log 133/135 untouched.
        supported = supported | {"tf", "mirna", "gene"}
    if granularity == "sample_specific" and "sample_specific" in capability.granularities:
        return supported | {"sample"}
    # An artifact whose ontology lists `sample` and allows a per-sample form
    # has `sample` as its axis, never as a node: a co-expression network is a
    # network of genes at any granularity. The same predicate entails the
    # entity in evidence validation (Log 143); matching now agrees (Log 172).
    semantics = ARTIFACT_SEMANTICS.get(artifact_type)
    if (
        semantics is not None
        and semantics.entities is not None
        and "sample" in semantics.entities
        and semantics.granularities is not None
        and "sample_specific" in semantics.granularities
        and artifact_type in _supported_artifacts(capability)
    ):
        return supported | {"sample"}
    return supported


def _accepts_inputs(
    outcome: RequestedOutcome,
    capability: OutputCapabilityDefinition,
    available_inputs: InputAvailabilityLike = (),
) -> bool:
    requested = set(outcome.input_artifacts) - {_UNKNOWN}
    availability = _as_input_availability(available_inputs)
    # Open-world rule: an unmentioned prerequisite is unknown, not absent.
    # Only an explicit negative statement may eliminate a capability here.
    if set(capability.required_input_artifacts) & set(availability.absent):
        return False
    if requested & set(availability.absent):
        return False
    return (
        requested.issubset(capability.input_artifacts)
        and not requested.intersection(capability.incompatible_input_artifacts)
    )


def input_availability(task: str) -> InputAvailability:
    """Extract bounded present/absent evidence without closing the input world."""
    present = {
        mention.artifact
        for mention in input_mentions(task)
        if mention.status == "current"
    }
    absent = {
        mention.artifact
        for mention in input_mentions(task)
        if mention.status == "negated"
    }
    # Priors are executor prerequisites rather than public output-ontology
    # values, so they stay out of INPUT_PATTERNS while sharing its temporal
    # clause scope here.  This recognizes bundles such as "miRNA, motif and PPI
    # priors" without confusing measured miRNA expression with a miRNA prior.
    for clause, scope in _scoped_clauses(task):
        if scope != "current":
            continue
        for artifact, pattern in _PRIOR_PATTERNS.items():
            for match in pattern.finditer(clause):
                prefix = clause[:match.start()]
                negated = bool(
                    _NEGATED_INPUT.search(prefix[-40:])
                    or _NEGATED_INPUT.search(match.group())
                )
                (absent if negated else present).add(artifact)
    # The clause iterator intentionally splits commas, while English commonly
    # shares the final noun across a list: "miRNA, motif and PPI priors".  Keep
    # this narrow whole-sentence witness so the first list item is not lost.
    for match in _MIRNA_SHARED_PRIOR_BUNDLE.finditer(task):
        sentence_start = max(
            task.rfind(delimiter, 0, match.start())
            for delimiter in (".", "。", "！", "!", "？", "?", ";", "；", "\n")
        ) + 1
        scope_prefix = task[sentence_start:match.start()]
        history_at = max((item.start() for item in _HISTORY.finditer(scope_prefix)), default=-1)
        current_at = max((item.start() for item in _CURRENT.finditer(scope_prefix)), default=-1)
        if history_at > current_at:
            continue
        prefix = scope_prefix[-40:]
        if _NEGATED_INPUT.search(prefix) or _NEGATED_INPUT.search(match.group()):
            absent.add("mirna_prior")
        else:
            present.add("mirna_prior")
    absent.difference_update(present)
    return InputAvailability(
        present=frozenset(present),
        absent=frozenset(absent),
    )


def explicit_input_artifacts(task: str) -> frozenset[str]:
    """Backward-compatible view of inputs explicitly present in the request."""
    return input_availability(task).present




def _unknown_entity_is_role_placeholder(outcome: RequestedOutcome) -> bool:
    known_entities = set(outcome.entity_types) - {_UNKNOWN}
    role_entities = (
        set(outcome.regulator_types) | set(outcome.target_types)
    ) - {_UNKNOWN}
    return (
        outcome.artifact_type == "regulatory_network"
        and _UNKNOWN in outcome.entity_types
        and bool(role_entities)
        and known_entities == role_entities
    )


def _has_unknown(outcome: RequestedOutcome) -> bool:
    return bool(
        outcome.unresolved_dimensions
        or _UNKNOWN in {outcome.operation, outcome.artifact_type, outcome.granularity}
        or (
            _UNKNOWN in outcome.entity_types
            and not _unknown_entity_is_role_placeholder(outcome)
        )
        or _UNKNOWN in outcome.input_artifacts
        or _UNKNOWN in outcome.regulator_types
        or _UNKNOWN in outcome.target_types
    )


def _matches(
    outcome: RequestedOutcome,
    capability: OutputCapabilityDefinition,
    available_inputs: InputAvailabilityLike = (),
) -> bool:
    if _has_unknown(outcome) or outcome_consistency_issues(outcome):
        return False
    requested_entities = set(outcome.entity_types)
    if _unknown_entity_is_role_placeholder(outcome):
        requested_entities.discard(_UNKNOWN)
    return (
        outcome.operation == capability.operation
        and _accepts_inputs(outcome, capability, available_inputs)
        and outcome.artifact_type in _supported_artifacts(capability)
        and outcome.granularity in capability.granularities
        and requested_entities.issubset(
            _supported_entities(
                outcome.artifact_type, capability, outcome.granularity,
            )
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
    available_inputs: InputAvailabilityLike = (),
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
            _supported_entities(
                outcome.artifact_type, capability, outcome.granularity,
            ),
        )
        and _known_set_matches(outcome.regulator_types, capability.regulator_types)
        and _known_set_matches(outcome.target_types, capability.target_types)
    )


def _complete_guidance_match(outcome, capability) -> bool:
    """Only explanatory operation may be omitted for an exact guidance match."""
    if outcome.operation not in {_UNKNOWN, capability.operation}:
        return False
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
    "InputAvailability",
    "InputAvailabilityLike",
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
    "input_availability",
]
