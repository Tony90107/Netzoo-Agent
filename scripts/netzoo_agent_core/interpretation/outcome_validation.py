"""Generic validation for LLM-produced scientific outcome evidence."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import re
import unicodedata

from ..contracts import OutcomeHypothesis, RequestedOutcome
from ..contracts.artifact_semantics import ARTIFACT_SEMANTICS, outcome_consistency_issues
from ..contracts.repair_scope import (
    FIELD_BY_DIMENSION, NO_OUTCOME_FIELDS, OUTCOME_FIELDS, Issue,
)
from workflow_registry import ACTION_BY_METHOD_LABEL, OUTPUT_CAPABILITIES
from .request_integrity import confirmed_current_inputs, request_integrity_issues
from .span_alignment import aligned_span

__all__: list[str] = []


@dataclass(frozen=True, slots=True)
class OutcomeValidation:
    """Deterministic acceptance result for semantic hypotheses."""

    valid: bool
    issues: tuple[str, ...]
    recoverable: bool = False
    #: One entry per explicit evidence item that failed grounding, classifying
    #: *why* without carrying the provider's own words. `ungrounded_evidence`
    #: is the largest issue family in the live record and the two shapes below
    #: call for opposite responses, yet nothing recorded so far distinguishes
    #: them. Only the closed-vocabulary dimension and value appear here.
    evidence_shapes: tuple[dict[str, str | int], ...] = ()


def _normalized(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    # CJK words can be wrapped without a word separator. This is typography
    # normalization, not translation or synonym inference.
    text = re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", text)
    return re.sub(r"[\W_]+", " ", text).strip()


def _grounded_span(span: str, task: str) -> bool:
    """Whether the request contains this quote, verbatim or misspelled.

    The verbatim test comes first and is unchanged, so word alignment can only
    ever add a grounding. That ordering is not a micro-optimization: scripts
    without word delimiters normalize to a single token, and alignment cannot
    read them at all -- a Chinese quote that grounds today grounds through this
    branch. `aligned_span` refuses every non-ASCII word for the same reason.
    """
    if not span:
        return False
    left = r"(?<![a-z0-9])" if span[0].isascii() and span[0].isalnum() else ""
    right = r"(?![a-z0-9])" if span[-1].isascii() and span[-1].isalnum() else ""
    if re.search(left + re.escape(span) + right, task) is not None:
        return True
    return aligned_span(span, task)


def _outcome_values(outcome: RequestedOutcome) -> dict[str, set[str]]:
    return {
        "operation": {outcome.operation},
        "input_artifact": set(outcome.input_artifacts),
        "artifact_type": {outcome.artifact_type},
        "entity_type": set(outcome.entity_types),
        "regulator_type": set(outcome.regulator_types),
        "target_type": set(outcome.target_types),
        "granularity": {outcome.granularity},
        "selection_tag": set(outcome.selection_tags),
        "named_method": set(outcome.named_methods),
    }


def _entailed_by_artifact(outcome: RequestedOutcome) -> tuple[frozenset[str], str | None]:
    """Return the entity set and granularity the chosen artifact alone fixes.

    Where the ontology permits exactly one value, `outcome_consistency_issues`
    already rejects every other, so a separate evidence entry for it repeats
    what choosing the artifact_type has established. Artifacts that permit
    several values are excluded: there the value is a real choice.
    """
    rule = ARTIFACT_SEMANTICS.get(outcome.artifact_type)
    entities = (
        rule.entities
        if rule is not None and rule.entities is not None and len(rule.entities) == 1
        else frozenset()
    )
    granularity = (
        next(iter(rule.granularities))
        if rule is not None and rule.granularities is not None and len(rule.granularities) == 1
        else None
    )
    return entities, granularity


#: Which outcome field each capability attribute answers for. Read from the
#: registry's own capability shape rather than restated, so a capability that
#: gains an attribute does not silently stop being checked.
_CAPABILITY_FIELDS = (
    ("operation", "operation", False),
    ("artifact_type", "artifact_type", False),
    ("granularities", "granularity", False),
    ("entity_types", "entity_types", True),
    ("regulator_types", "regulator_types", True),
    ("target_types", "target_types", True),
)


def _named_method_conflicts(outcome: RequestedOutcome) -> list[Issue]:
    """Where the outcome asserts something the method it names cannot produce.

    The requester wrote the method down and the quote was checked, so the name is
    a fact about the request. A dimension that contradicts it is a guess the
    model made around that fact -- PANDA produces an aggregate network, and a
    reading that names PANDA and asserts `sample_specific` has guessed. Only the
    contradicting field is opened for repair: the name is quoted, so it is not
    the part in doubt.

    Nothing is filled in from the capability. An unknown dimension stays unknown
    and the registry answers for it at match time.
    """
    conflicts: list[Issue] = []
    for label in outcome.named_methods:
        action = ACTION_BY_METHOD_LABEL.get(label)
        capability = OUTPUT_CAPABILITIES.get(action) if action else None
        if capability is None:
            continue
        for attribute, field, is_set in _CAPABILITY_FIELDS:
            allowed = getattr(capability, attribute, None)
            if allowed is None:
                continue
            stated = getattr(outcome, field)
            values = (set(stated) if is_set else {stated}) - {"unknown"}
            permitted = set(allowed) if not isinstance(allowed, str) else {allowed}
            if values and not values.issubset(permitted):
                conflicts.append(Issue(
                    f"named_method_conflict:{label}.{field}", {field},
                ))
    return conflicts


def _label_quoted(label: str, span: str) -> bool:
    """Whether the quoted span actually contains the method label it supports.

    The span is separately checked against the request, so the pair means the
    label really is in the request and really is what this entry cites. Matching
    is on word boundaries and ignores case and the separators a requester may
    type, so `LIONESS-PANDA`, `lioness panda` and `LIONESS_PANDA` all count.
    """
    words = re.split(r"[-_\s]+", label.casefold())
    pattern = (
        r"(?<![a-z0-9])" + r"[\s_-]*".join(re.escape(word) for word in words)
        + r"(?![a-z0-9])"
    )
    return re.search(pattern, span.casefold()) is not None


def _required_evidence(
    outcome: RequestedOutcome,
    confirmed_inputs: frozenset[str] = frozenset(),
) -> list[tuple[str, str]]:
    required: list[tuple[str, str]] = []
    entailed_entities, entailed_granularity = _entailed_by_artifact(outcome)
    # A named method is a claim about the request's own words, so it always
    # needs its entry; there is no ontology that could entail it.
    required.extend(("named_method", value) for value in outcome.named_methods)
    if outcome.operation != "unknown":
        required.append(("operation", outcome.operation))
    if outcome.artifact_type != "unknown":
        required.append(("artifact_type", outcome.artifact_type))
    required.extend(
        ("input_artifact", value) for value in outcome.input_artifacts
        if value != "unknown" and value not in confirmed_inputs
    )
    if outcome.granularity not in {"unknown", "not_applicable", entailed_granularity}:
        required.append(("granularity", outcome.granularity))
    required.extend(
        ("regulator_type", value)
        for value in outcome.regulator_types
        if value != "unknown"
    )
    required.extend(
        ("target_type", value)
        for value in outcome.target_types
        if value != "unknown"
    )
    role_entities = set(outcome.regulator_types) | set(outcome.target_types)
    required.extend(
        ("entity_type", value)
        for value in outcome.entity_types
        if value != "unknown"
        and value not in role_entities
        and value not in entailed_entities
    )
    return required


def _is_not_applicable(outcome: RequestedOutcome) -> bool:
    return (
        outcome.operation == "unknown"
        and outcome.artifact_type == "unknown"
        and outcome.granularity == "not_applicable"
        and not outcome.input_artifacts
        and not outcome.entity_types
        and not outcome.regulator_types
        and not outcome.target_types
        and not outcome.unresolved_dimensions
    )


def evidence_census(
    hypotheses: Sequence[OutcomeHypothesis],
) -> tuple[dict[str, str | int], ...]:
    """Count how each hypothesis sourced its evidence, before any grounding check.

    The rejection record says only which explicit quotes failed, so it cannot
    say how often an explicit entry carries a quote at all. That base rate is
    what separates "tighten the contract and a few violations surface earlier"
    from "tighten the contract and most hypotheses become schema failures".
    Counts only; no provider text and no effect on validation.
    """
    return tuple(
        {
            "hypothesis": index,
            "explicit_with_span": sum(
                1 for item in hypothesis.evidence
                if item.source == "explicit" and (item.text_span or "").strip()
            ),
            "explicit_without_span": sum(
                1 for item in hypothesis.evidence
                if item.source == "explicit" and not (item.text_span or "").strip()
            ),
            "inferred": sum(
                1 for item in hypothesis.evidence if item.source == "inferred"
            ),
        }
        for index, hypothesis in enumerate(hypotheses)
    )


def validate_outcome_hypotheses(
    user_task: str,
    hypotheses: Sequence[OutcomeHypothesis],
) -> OutcomeValidation:
    """Validate evidence without selecting or naming a workflow."""
    if not hypotheses:
        return OutcomeValidation(False, ("missing_hypotheses",))

    issues: list[str] = []
    evidence_shapes: list[dict[str, str | int]] = []
    normalized_task = _normalized(user_task)
    confirmed_inputs = frozenset(confirmed_current_inputs(user_task))
    for index, hypothesis in enumerate(hypotheses):
        # `prefixed` rather than an f-string: plain formatting would return a
        # bare `str` and drop the field scope each rule declared.
        issues.extend(
            issue.prefixed(f"hypothesis[{index}].")
            for issue in request_integrity_issues(user_task, hypothesis.outcome)
        )
        issues.extend(
            issue.prefixed(f"hypothesis[{index}].")
            for issue in outcome_consistency_issues(hypothesis.outcome)
        )
        issues.extend(
            issue.prefixed(f"hypothesis[{index}].")
            for issue in _named_method_conflicts(hypothesis.outcome)
        )
        outcome_values = _outcome_values(hypothesis.outcome)
        required_evidence = _required_evidence(hypothesis.outcome, confirmed_inputs)
        if (
            hypothesis.outcome.granularity == "not_applicable"
            and hypothesis.outcome.artifact_type == "unknown"
            and not _is_not_applicable(hypothesis.outcome)
        ):
            # This rule reads the outcome as a whole, so the whole outcome is
            # open to correction.
            issues.append(Issue(
                f"hypothesis[{index}].inconsistent_not_applicable_outcome",
                OUTCOME_FIELDS,
            ))
        if (
            not required_evidence
            and not hypothesis.evidence
            and not _is_not_applicable(hypothesis.outcome)
        ):
            issues.append(Issue(
                f"hypothesis[{index}].unusable_outcome", OUTCOME_FIELDS,
            ))
        evidence_pairs: set[tuple[str, str]] = set()
        for item in hypothesis.evidence:
            normalized_value = _normalized(item.value)
            evidence_pairs.add((item.dimension, normalized_value))
            valid_values = {
                _normalized(value) for value in outcome_values[item.dimension]
            }
            if normalized_value not in valid_values:
                # The entry contradicts one field. Either that field is wrong
                # or the entry is; both fixes live inside this scope.
                issues.append(Issue(
                    f"hypothesis[{index}].conflicting_evidence:"
                    f"{item.dimension}={item.value}",
                    {FIELD_BY_DIMENSION[item.dimension]}
                    if item.dimension in FIELD_BY_DIMENSION else NO_OUTCOME_FIELDS,
                ))
            if item.dimension == "named_method":
                # Reporting what the user wrote is not something that can be
                # inferred, and a quote that does not contain the label does not
                # support the claim -- both would let an unmentioned method in.
                span = item.text_span or ""
                if item.source != "explicit" or not _label_quoted(item.value, span):
                    issues.append(Issue(
                        f"hypothesis[{index}].unquoted_named_method:{item.value}",
                        {"named_methods"},
                    ))
            if item.source == "explicit":
                span = _normalized(item.text_span or "")
                if not _grounded_span(span, normalized_task):
                    # About the quote, not about the value. Nothing in the
                    # outcome was questioned, so nothing in it may be rewritten.
                    issues.append(Issue(
                        f"hypothesis[{index}].ungrounded_evidence:"
                        f"{item.dimension}={item.value}",
                        NO_OUTCOME_FIELDS,
                    ))
                    evidence_shapes.append({
                        "hypothesis": index,
                        "dimension": item.dimension,
                        "value": item.value,
                        # "absent": the entry claimed an explicit quote and
                        # supplied none. "unmatched": it supplied one the
                        # request does not contain.
                        "span": "absent" if not span else "unmatched",
                    })

        for dimension, value in required_evidence:
            normalized_value = _normalized(value)
            if (dimension, normalized_value) not in evidence_pairs:
                issues.append(Issue(
                    f"hypothesis[{index}].missing_evidence:{dimension}={value}",
                    NO_OUTCOME_FIELDS,
                ))

    unique_issues = tuple(dict.fromkeys(issues))
    recoverable = bool(unique_issues) and all(
        ".ungrounded_evidence:" in issue for issue in unique_issues
    )
    return OutcomeValidation(
        not unique_issues,
        unique_issues,
        recoverable,
        tuple(evidence_shapes),
    )
