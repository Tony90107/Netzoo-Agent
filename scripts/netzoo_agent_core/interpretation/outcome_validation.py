"""Generic validation for LLM-produced scientific outcome evidence."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import re
import unicodedata

from ..contracts import OutcomeHypothesis, RequestedOutcome
from ..contracts.outcomes import OutcomeEvidence
from ..contracts.artifact_semantics import (
    ARTIFACT_SEMANTICS,
    is_outcome_not_applicable as _is_not_applicable,
    outcome_consistency_issues,
)
from ..contracts.repair_scope import (
    FIELD_BY_DIMENSION, NO_OUTCOME_FIELDS, OUTCOME_FIELDS, Issue,
)
from .request_integrity import (
    canonical_input_artifacts_in_text,
    confirmed_current_inputs,
    granularity_left_open,
    request_integrity_issues,
)
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


def _hard_wrap_normalized(value: str) -> str:
    """Normalize terminal wrapping inside an ASCII token without joining words.

    Interactive terminals can insert a newline in the middle of identifiers or
    English words (``s\nample-specific``). Ordinary spaces and newlines between
    complete words remain separators, so this does not turn paraphrases into
    apparent verbatim quotes.
    """
    text = unicodedata.normalize("NFKC", value).casefold()
    text = re.sub(r"(?<=[a-z0-9])[\t ]*\r?\n[\t ]*(?=[a-z0-9])", "", text)
    return _normalized(text)


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


def explicit_evidence_grounded(user_task: str, evidence: OutcomeEvidence) -> bool:
    """Whether an explicit evidence quote occurs in the typed terminal request."""
    if evidence.source != "explicit":
        return False
    span = _normalized(evidence.text_span or "")
    if not span:
        return False
    variants = tuple(dict.fromkeys((_normalized(user_task), _hard_wrap_normalized(user_task))))
    return any(_grounded_span(span, task) for task in variants)


def grounded_selection_tags(
    user_task: str,
    evidence: Sequence[OutcomeEvidence],
) -> frozenset[str]:
    """Return registry tags backed by explicit, grounded request evidence."""
    return frozenset(
        item.value
        for item in evidence
        if item.dimension == "selection_tag"
        and explicit_evidence_grounded(user_task, item)
    )


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
    }


def _entailed_by_artifact(
    outcome: RequestedOutcome,
) -> tuple[frozenset[str], str | None, str | None]:
    """Return the entity set, granularity and producing operation the artifact fixes.

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
    produced_by = (
        next(iter(rule.produced_by))
        if rule is not None and rule.produced_by is not None and len(rule.produced_by) == 1
        else None
    )
    return entities, granularity, produced_by


def _axis_entailed_entities(outcome: RequestedOutcome) -> frozenset[str]:
    """Entities that need no quote of their own once `sample` is read as an axis.

    In a sample-specific outcome, `sample` names the granularity -- one result
    per sample -- which the granularity evidence already quotes (the same
    reading as Log 136's `_supported_entities`). And for an artifact that can
    exist per sample, `sample` in its ontology is that axis, so if exactly one
    other entity remains it is the only node type: a co-expression network is a
    network of genes. Neither is a real choice, so neither needs a second quote
    (Log 143). An aggregate-only matrix such as pathway-by-sample scores keeps
    `sample` as a genuine dimension, and its entities stay a choice.
    """
    entailed = set()
    if outcome.granularity == "sample_specific":
        entailed.add("sample")
    rule = ARTIFACT_SEMANTICS.get(outcome.artifact_type)
    if (
        rule is not None
        and rule.entities is not None
        and "sample" in rule.entities
        and rule.granularities is not None
        and "sample_specific" in rule.granularities
    ):
        node_types = rule.entities - {"sample"}
        if len(node_types) == 1:
            entailed.update(node_types)
    return frozenset(entailed)


def _required_evidence(
    outcome: RequestedOutcome,
    confirmed_inputs: frozenset[str] = frozenset(),
    request_mode: str = "unknown",
) -> list[tuple[str, str]]:
    required: list[tuple[str, str]] = []
    entailed_entities, entailed_granularity, producing_operation = _entailed_by_artifact(
        outcome
    )
    entailed_entities = entailed_entities | _axis_entailed_entities(outcome)
    # Only the operation that builds this artifact is entailed. Asking to
    # explain or analyze the same artifact is a real choice and still needs a
    # quote, which is why produced_by is read here and operations is not.
    # A guidance request's operation cannot select anything: the matcher sets
    # it to unknown before matching (`_match_semantic_request`), so a quote for
    # it would justify a value that is never read (Log 145). Kept when the
    # artifact is unknown too, where it is the only evidenced field and
    # dropping it would turn a repairable reading into an unusable one.
    operation_is_read = not (
        request_mode == "guidance" and outcome.artifact_type != "unknown"
    )
    if outcome.operation not in {"unknown", producing_operation} and operation_is_read:
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


# Operations that do not themselves ask for a scientific result.  `explain`
# belongs beside `unknown` here: explaining a method produces no artifact, so
# pairing it with an unknown `artifact_type` and `not_applicable` granularity
# is the coherent reading, not a contradiction.
#
# Requiring `operation == "unknown"` made the only passing shape for a
# conceptual question one where the interpreter claimed to have understood
# nothing. The contract asks for the opposite — `operation` is documented as
# "Required scientific operation, even for guidance requests" — and the
# matcher already erases `operation` for guidance before selecting anything,
# so the strict reading rejected a hypothesis whose extra field could not have
# influenced the outcome.
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


_LIST_FIELD_BY_DIMENSION = {
    "input_artifact": "input_artifacts",
    "entity_type": "entity_types",
    "regulator_type": "regulator_types",
    "target_type": "target_types",
    "selection_tag": "selection_tags",
}
_SCALAR_FIELD_BY_DIMENSION = {
    "operation": "operation",
    "artifact_type": "artifact_type",
    "granularity": "granularity",
}


def reconcile_outcome_with_grounded_evidence(
    user_task: str,
    hypothesis: OutcomeHypothesis,
) -> None:
    """Carry a quoted fact the evidence establishes into the outcome itself.

    The contract asks for the same fact twice: once as an outcome field and
    once as an evidence entry. Providers routinely write one and omit the
    other, and the omission is reported as the entry contradicting the
    outcome -- which reads as disagreement where there is none, and sends the
    repair call chasing a conflict that does not exist.

    Only a gap is closed, never a disagreement. The value must come from an
    entry marked explicit whose quote was verified against the request, and
    the outcome side must be genuinely absent: an empty list, or the scalar
    "unknown". A field that already holds a different value is a real
    contradiction and is left for validation to report.
    """
    outcome = hypothesis.outcome
    for item in hypothesis.evidence:
        value = str(item.value)
        if (
            value == "unknown"
            or item.source != "explicit"
            or not explicit_evidence_grounded(user_task, item)
        ):
            continue
        list_field = _LIST_FIELD_BY_DIMENSION.get(item.dimension)
        if list_field is not None:
            current = list(getattr(outcome, list_field) or [])
            if current:
                continue
            _assign_if_valid(outcome, list_field, [value])
            continue
        scalar_field = _SCALAR_FIELD_BY_DIMENSION.get(item.dimension)
        if scalar_field is not None and getattr(outcome, scalar_field) == "unknown":
            _assign_if_valid(outcome, scalar_field, value)


def _assign_if_valid(outcome: RequestedOutcome, field: str, value: object) -> None:
    """Assign only a value the outcome schema itself accepts."""
    try:
        RequestedOutcome.model_validate({**outcome.model_dump(), field: value})
    except Exception:
        return
    setattr(outcome, field, value)


def validate_outcome_hypotheses(
    user_task: str,
    hypotheses: Sequence[OutcomeHypothesis],
    request_mode: str = "unknown",
) -> OutcomeValidation:
    """Validate evidence without selecting or naming a workflow."""
    if not hypotheses:
        return OutcomeValidation(False, ("missing_hypotheses",))

    issues: list[str] = []
    evidence_shapes: list[dict[str, str | int]] = []
    confirmed_inputs = frozenset(confirmed_current_inputs(user_task))
    for hypothesis in hypotheses:
        # Deliberately before judging, and deliberately in place: every caller
        # goes on to use the hypothesis it passed in, so an outcome completed
        # from its own grounded evidence has to reach them too.
        reconcile_outcome_with_grounded_evidence(user_task, hypothesis)
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
        outcome_values = _outcome_values(hypothesis.outcome)
        required_evidence = _required_evidence(
            hypothesis.outcome, confirmed_inputs, request_mode,
        )
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
            # "unknown" is how this vocabulary declines to commit, and
            # `_required_evidence` already reads it that way on the outcome
            # side. Treating it as a claim here made an entry that commits to
            # nothing contradict an outcome it never disagreed with.
            if normalized_value == "unknown":
                continue
            if normalized_value not in valid_values:
                # The entry contradicts one field. Either that field is wrong
                # or the entry is; both fixes live inside this scope.
                issues.append(Issue(
                    f"hypothesis[{index}].conflicting_evidence:"
                    f"{item.dimension}={item.value}",
                    {FIELD_BY_DIMENSION[item.dimension]}
                    if item.dimension in FIELD_BY_DIMENSION else NO_OUTCOME_FIELDS,
                ))
            if item.source == "explicit":
                span = _normalized(item.text_span or "")
                if item.dimension == "input_artifact" and item.text_span:
                    quoted_inputs = canonical_input_artifacts_in_text(item.text_span)
                    if quoted_inputs and str(item.value) not in quoted_inputs:
                        # A verbatim quote proves only that the words occurred;
                        # it does not prove the provider mapped those words to
                        # the right canonical artifact. Keep that ontology
                        # authority in deterministic code for known inputs.
                        issues.append(Issue(
                            f"hypothesis[{index}].conflicting_evidence:"
                            f"{item.dimension}={item.value}",
                            {FIELD_BY_DIMENSION[item.dimension]},
                        ))
                if not explicit_evidence_grounded(user_task, item):
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

    committed = {item.outcome.granularity for item in hypotheses}
    if (
        len(committed) == 1
        and committed <= {"aggregate", "sample_specific"}
        and granularity_left_open(user_task)
    ):
        # Judged over the interpretation, not per hypothesis: keeping
        # `[unknown, sample_specific]` side by side is how an open choice is
        # expressed, and it passed. Only a reading where every hypothesis picked
        # the same side decided what the request left open -- and once a stated
        # aggregate selects PUMA, that became an exact answer to it.
        issues.extend(
            Issue(f"hypothesis[{index}].undecided_granularity", {"granularity"})
            for index in range(len(hypotheses))
        )
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
