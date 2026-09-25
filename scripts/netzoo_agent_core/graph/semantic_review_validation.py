"""Strict decoding helpers for semantic review and patch payloads."""

from __future__ import annotations

from collections.abc import Mapping
from typing import get_args

from pydantic import ValidationError

from ..contracts.artifact_semantics import artifacts_supporting_regulatory_roles
from ..contracts.outcomes import (
    OutcomeEvidence,
    EvidenceDimension,
    SemanticPatch,
    SemanticReview,
)
from ..interpretation.outcome_validation import explicit_evidence_grounded
from ..interpretation.request_integrity import (
    has_explicit_advice_intent,
    regulatory_role_mentions,
)


#: The closed vocabulary a removal instruction must name to mean anything.
_EVIDENCE_DIMENSIONS = frozenset(get_args(EvidenceDimension))


def normalize_role_entailed_artifact_evidence(
    payload,
    user_task: str,
) -> tuple[object, list[dict]]:
    """Downgrade unquoted artifact claims entailed by explicit role witnesses.

    Reviewers sometimes label ``regulatory_network`` evidence explicit without
    supplying a quote for that artifact label. The role phrase can entail the
    artifact through the output ontology, but it does not make the artifact
    label a verbatim user statement. Preserve the supported value as inferred
    evidence so the normal strict outcome validation can decide whether the
    complete patch is coherent.
    """
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump()
    if not isinstance(payload, Mapping):
        return payload, []
    role_mentions = regulatory_role_mentions(user_task)
    supported_artifacts = artifacts_supporting_regulatory_roles(
        (item.regulator_type, item.target_type) for item in role_mentions
    )
    role_entity_quotes = {
        entity_type: item.text_span
        for item in role_mentions
        for entity_type in item.entity_types
    }
    if not supported_artifacts and not role_entity_quotes:
        return payload, []

    normalized = dict(payload)
    notes: list[dict] = []

    def normalize_additions(container: dict) -> None:
        additions = container.get("evidence_additions")
        if not isinstance(additions, list):
            return
        repaired = []
        changed = False
        for item in additions:
            if not isinstance(item, Mapping):
                repaired.append(item)
                continue
            entry = dict(item)
            text_span = entry.get("text_span")
            if (
                entry.get("dimension") == "entity_type"
                and entry.get("value") in role_entity_quotes
                and entry.get("source") == "explicit"
                and (
                    not isinstance(text_span, str)
                    or not text_span.strip()
                )
            ):
                entry["text_span"] = role_entity_quotes[entry["value"]]
                notes.append({
                    "dimension": "entity_type",
                    "value": entry["value"],
                    "from": "explicit_without_span",
                    "to": "explicit_with_role_quote",
                    "reason": "entailed_by_explicit_regulatory_role",
                })
                changed = True
            elif (
                entry.get("dimension") == "artifact_type"
                and entry.get("value") in supported_artifacts
                and entry.get("source") == "explicit"
            ):
                grounded = False
                try:
                    evidence = OutcomeEvidence.model_validate(entry)
                    grounded = explicit_evidence_grounded(user_task, evidence)
                except ValidationError:
                    pass
                if not grounded:
                    entry["source"] = "inferred"
                    entry["text_span"] = None
                    entry["rationale"] = (
                        "The artifact is inferred from explicit regulator-to-target "
                        "roles under the output ontology."
                    )
                    notes.append({
                        "dimension": "artifact_type",
                        "value": entry["value"],
                        "from": "explicit",
                        "to": "inferred",
                        "reason": "entailed_by_explicit_regulatory_roles",
                    })
                    changed = True
            repaired.append(entry)
        if changed:
            container["evidence_additions"] = repaired

    normalize_additions(normalized)
    nested = normalized.get("outcome")
    if isinstance(nested, Mapping):
        nested_copy = dict(nested)
        normalize_additions(nested_copy)
        normalized["outcome"] = nested_copy
    return normalized, notes


def normalize_advice_operation_evidence(
    payload,
    user_task: str,
    *,
    proposal_request_mode: str,
) -> tuple[object, list[dict]]:
    """Treat unquoted ``explain`` as inferred only for explicit advice guidance.

    The request must contain advice/recommendation language, and the first-pass
    or patch request mode must be guidance. This leaves explicit-evidence quote
    validation unchanged for every other field and every other request.
    """
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump()
    if not isinstance(payload, Mapping) or not has_explicit_advice_intent(user_task):
        return payload, []
    normalized = dict(payload)
    request_mode = normalized.get("request_mode") or proposal_request_mode
    outcome = normalized.get("outcome")
    if request_mode != "guidance":
        return payload, []

    notes: list[dict] = []

    def normalize_claim(operation_claim, hypothesis_index=None):
        if not isinstance(operation_claim, Mapping):
            return operation_claim
        if operation_claim.get("value") != "explain":
            return operation_claim
        support = operation_claim.get("support")
        if not isinstance(support, Mapping) or support.get("source") != "explicit":
            return operation_claim
        repaired_claim = dict(operation_claim)
        repaired_support = dict(support)
        repaired_support["source"] = "inferred"
        repaired_support["text_span"] = None
        repaired_support["rationale"] = (
            "The request explicitly asks for advice, so explain is inferred "
            "as the operation for this guidance request."
        )
        repaired_claim["support"] = repaired_support
        notes.append({
            "dimension": "operation",
            "value": "explain",
            "from": "explicit",
            "to": "inferred",
            "reason": "explicit_advice_intent_in_guidance_mode",
            **({"hypothesis": hypothesis_index} if hypothesis_index is not None else {}),
        })
        return repaired_claim

    def normalize_additions(container: dict) -> None:
        additions = container.get("evidence_additions")
        if not isinstance(additions, list):
            return
        repaired = []
        changed = False
        for item in additions:
            if not isinstance(item, Mapping):
                repaired.append(item)
                continue
            entry = dict(item)
            text_span = entry.get("text_span")
            if (
                entry.get("dimension") == "operation"
                and entry.get("value") == "explain"
                and entry.get("source") == "explicit"
                and (
                    not isinstance(text_span, str)
                    or not text_span.strip()
                )
            ):
                entry["source"] = "inferred"
                entry["text_span"] = None
                entry["rationale"] = (
                    "The request explicitly asks for advice, so explain is inferred "
                    "as the operation for this guidance request."
                )
                notes.append({
                    "dimension": "operation",
                    "value": "explain",
                    "from": "explicit_without_span",
                    "to": "inferred",
                    "reason": "explicit_advice_intent_in_guidance_mode",
                })
                changed = True
            repaired.append(entry)
        if changed:
            container["evidence_additions"] = repaired

    if isinstance(outcome, Mapping) and outcome.get("operation") == "explain":
        normalize_additions(normalized)
        nested_copy = dict(outcome)
        normalize_additions(nested_copy)
        normalized["outcome"] = nested_copy
    elif isinstance(outcome, Mapping):
        nested_copy = dict(outcome)
        nested_copy["operation"] = normalize_claim(nested_copy.get("operation"))
        normalized["outcome"] = nested_copy

    hypotheses = normalized.get("outcome_hypotheses")
    if isinstance(hypotheses, list):
        repaired_hypotheses = []
        for index, item in enumerate(hypotheses):
            if not isinstance(item, Mapping) or not isinstance(item.get("outcome"), Mapping):
                repaired_hypotheses.append(item)
                continue
            hypothesis = dict(item)
            hypothesis_outcome = dict(item["outcome"])
            hypothesis_outcome["operation"] = normalize_claim(
                hypothesis_outcome.get("operation"), index,
            )
            hypothesis["outcome"] = hypothesis_outcome
            repaired_hypotheses.append(hypothesis)
        normalized["outcome_hypotheses"] = repaired_hypotheses
    return normalized, notes


def _honourable_removals(payload) -> tuple[object, list[dict]]:
    """Set aside evidence-list instructions that cannot be carried out.

    Two shapes cost the whole repair -- including the well-formed additions that
    were the repair -- for the sake of one instruction that could never have had
    an effect. Both were the entire residual of a matched-control round: 5 trials
    of the first and 6 of the second, out of 14 failures in 36.

    A removal names one (dimension, value) to withdraw. When its `dimension` is
    outside the closed vocabulary, or its string value is blank, it names nothing
    that can exist in the evidence list. Honouring it and ignoring it are therefore
    the same act -- while rejecting the patch over it is not. Only removals are
    treated this way: a malformed *addition* is the repair itself failing, and
    stays strict.

    The second shape is the same list at the root and nested inside `outcome`
    with different contents. The nesting is an accommodation for a provider that
    puts it there, not a second source of truth, so when the two disagree the
    field the contract declares is the one it meant. `SemanticPatch` still
    raises on anything this has not set aside.

    Nothing is dropped silently: what was set aside is returned for the caller
    to record beside the patch it applied.
    """
    if not isinstance(payload, Mapping):
        return payload, []
    normalized, ignored = dict(payload), []
    nested = normalized.get("outcome")
    if isinstance(nested, Mapping):
        nested = dict(nested)
        for field in ("evidence_additions", "evidence_removals"):
            if field in nested and field in normalized and normalized[field] != nested[field]:
                ignored.append({"reason": "nested_list_disagreed", "field": field})
                nested.pop(field)
        normalized["outcome"] = nested
    removals = normalized.get("evidence_removals")
    if isinstance(removals, list):
        kept = []
        for item in removals:
            dimension = item.get("dimension") if isinstance(item, Mapping) else None
            if isinstance(item, Mapping) and dimension not in _EVIDENCE_DIMENSIONS:
                ignored.append(
                    {
                        "reason": "removal_names_no_dimension",
                        "field": "evidence_removals",
                    }
                )
                continue
            value = item.get("value") if isinstance(item, Mapping) else None
            if isinstance(value, str) and not value.strip():
                ignored.append(
                    {
                        "reason": "removal_names_no_value",
                        "field": "evidence_removals",
                    }
                )
                continue
            kept.append(item)
        normalized["evidence_removals"] = kept
    return normalized, ignored


def _as_semantic_patch(payload) -> tuple[SemanticPatch | None, list[dict]]:
    """Return the payload as a patch, or None when it is a whole review.

    `SemanticPatch` and `SemanticReview` are structurally disjoint: a review must
    carry `outcome_hypothesis`, which the patch forbids, and a patch's root
    `outcome` is not a review field. Accepting whichever arrived relaxes nothing
    -- both go through the identical `validate_outcome_hypotheses` afterwards --
    and it keeps a provider that answers with a complete structure working
    instead of turning its reply into a decoding failure.
    """
    prepared, ignored = _honourable_removals(payload)
    try:
        return SemanticPatch.model_validate(prepared), ignored
    except ValidationError:
        return None, ignored


def _validated_review(payload, *, patching: bool) -> SemanticReview:
    """Parse a whole-review reply, reporting against the contract we asked for.

    A reply that is neither shape must not be described by the review's missing
    fields when the call requested a patch: the diagnostics would name a contract
    this attempt never used, and a live round observed exactly that -- a patch
    reply reported as `outcome_hypothesis:missing`.
    """
    try:
        return SemanticReview.model_validate(payload)
    except ValidationError:
        if patching:
            SemanticPatch.model_validate(payload)
        raise
