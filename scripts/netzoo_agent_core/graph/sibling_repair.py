"""Repair each competing reading the patch left invalid (Log 242).

The patch repairs the one hypothesis it adjudicates as primary and keeps the
others as the first pass wrote them. A request that states two scientific
hypotheses therefore lost the second one in 8 of 18 traced trials (Log 241):
it still carried first-pass issues nothing had asked about, and
`keep_valid_hypotheses` dropped it without a word in the reply.

Each such reading gets one repair of its own, in the patch's strict schema with
`hypothesis_index` fixed to that reading. The merge, restoration and
validation are the patch's own; nothing is relaxed or filled in.
"""

from __future__ import annotations

import time
from typing import ClassVar, Literal

from pydantic import Field, create_model

from ..contracts.outcomes import SemanticInterpretation, SemanticPatch
from ..contracts.repair_scope import permitted_fields
from ..interpretation.outcome_validation import OutcomeValidation, validate_outcome_hypotheses
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_patch import apply_semantic_patch
from ..interpretation.semantic_repair import semantic_payload
from ..interpretation.stated_field_restoration import restore_stated_fields
from ..llm import append_llm_usage, build_semantic_patch_messages
from .context import preflight_budget, record_event
from .discriminator import _fill_inferred_role_evidence
from .partial_validity import _valid_subset
from .semantic_review_validation import (
    _as_semantic_patch,
    normalize_advice_operation_evidence,
    normalize_role_entailed_artifact_evidence,
)
from .structured_calls import _serialized_structured_input

__all__ = ["SIBLING_REPAIR_LIMIT", "SIBLING_REPAIR_ROLE", "repair_sibling_hypotheses", "sibling_patch_schema"]

SIBLING_REPAIR_ROLE = "semantic_sibling_repair"
# At most three hypotheses, one of which the patch already repaired.
SIBLING_REPAIR_LIMIT = 2

# The patch prompt's one sentence about choosing the index, and the sentence
# describing the fixed index that replaces it. Nothing else in the prompt moves.
_CHOOSE_INDEX = (
    "Use hypothesis_index to pick the one first-pass hypothesis that states the "
    "primary scientific outcome."
)


class _SiblingPatch(SemanticPatch):
    target: ClassVar[int] = 0

    @classmethod
    def model_json_schema(cls, *args, **kwargs):
        schema = super().model_json_schema(*args, **kwargs)
        schema["properties"]["hypothesis_index"] = {
            "type": "integer", "enum": [cls.target],
            "description": "The first-pass hypothesis this repair is for; fixed.",
        }
        return schema


def sibling_patch_schema(index: int) -> type[SemanticPatch]:
    """`SemanticPatch` with `hypothesis_index` fixed to one reading."""
    schema = create_model(
        "SiblingSemanticPatch", __base__=_SiblingPatch,
        hypothesis_index=(Literal[index], Field(default=index)),
    )
    schema.target = index
    return schema


def _messages(context, user_task, interpretation, index, issues, discriminator_context):
    messages = build_semantic_patch_messages(
        context.semantic_prompt, user_task, interpretation, issues, discriminator_context,
    )
    fixed = (
        f"hypothesis_index is fixed to {index}: repair only that first-pass hypothesis; "
        "the others are not part of this patch."
    )
    messages[0] = messages[0].model_copy(update={
        "content": messages[0].content.replace(_CHOOSE_INDEX, fixed),
    })
    return messages


def repair_sibling_hypotheses(
    context,
    state,
    user_task: str,
    interpretation: SemanticInterpretation,
    validation: OutcomeValidation,
    *,
    patched_index: int | None,
    usage,
    budget_warnings: list[str],
    discriminator_context: str = "",
):
    """Return the interpretation, its validation, usage and warnings after the repairs."""
    llm = getattr(context, "selection_condition_llm", None)
    hypotheses = interpretation.outcome_hypotheses
    if validation.valid or patched_index is None or len(hypotheses) < 2 or llm is None:
        return interpretation, validation, usage, budget_warnings
    _, dropped = _valid_subset(user_task, interpretation, with_siblings=True)
    targets = [item["hypothesis"] for item in dropped if item["hypothesis"] != patched_index]
    for index in targets[:SIBLING_REPAIR_LIMIT]:
        prefix = f"hypothesis[{index}]."
        issues = tuple(issue for issue in validation.issues if issue.startswith(prefix))
        if not issues:
            continue
        schema = sibling_patch_schema(index)
        messages = _messages(context, user_task, interpretation, index, issues, discriminator_context)
        input_text = _serialized_structured_input(messages, schema)
        semantic_state = dict(state)
        semantic_state["token_usage"] = usage.model_dump()
        semantic_state["budget_warnings"] = budget_warnings
        budget, budget_warnings = preflight_budget(
            context, semantic_state, role=SIBLING_REPAIR_ROLE, model=context.semantic_model_name,
            input_text=input_text, reserved_output_tokens=context.router_max_tokens,
            allow_reserve=False,
        )
        if budget.status == "blocked":
            break
        started_ns = time.monotonic_ns()
        raw, output_text, status = None, "", "failed"
        try:
            adapter = llm.with_structured_output(
                schema, method="function_calling", include_raw=True, strict=True,
            )
            payload, raw = semantic_payload(adapter.invoke(messages))
            payload, _ = normalize_role_entailed_artifact_evidence(payload, user_task)
            payload, _ = normalize_advice_operation_evidence(
                payload, user_task, proposal_request_mode=interpretation.request_mode,
            )
            patch, ignored = _as_semantic_patch(payload)
            if patch is None or patch.hypothesis_index != index:
                raise ValueError("sibling repair did not return a patch for its reading")
            # Interpretation-level fields belong to the primary patch.
            patch = patch.model_copy(update={"request_mode": None, "semantic_goal": None})
            output_text = patch.model_dump_json()
            merged, retired = apply_semantic_patch(
                interpretation, patch, permitted_fields=permitted_fields(issues),
                user_task=user_task,
            )
            merged, restorations = restore_stated_fields(
                user_task, merged, align_artifact_constraints=True,
                restore_explicit_scalar_evidence=True,
            )
            merged = _fill_inferred_role_evidence(merged)
        except BaseException as error:
            if _is_fatal_exception(error):
                raise
            record_event(context, state, "routing.sibling_hypothesis_repair_failed", "classify", {
                "hypothesis": index, "error_type": type(error).__name__,
            })
        else:
            status = "success"
            interpretation = merged
            alone = validate_outcome_hypotheses(
                user_task, [merged.outcome_hypotheses[index].model_copy(deep=True)],
                merged.request_mode,
                sibling_inputs=frozenset().union(*(
                    other.outcome.input_artifacts
                    for position, other in enumerate(merged.outcome_hypotheses) if position != index
                )),
            )
            record_event(context, state, "routing.sibling_hypothesis_repaired", "classify", {
                "hypothesis": index,
                "issues": list(issues),
                "changed_fields": sorted(
                    name for name, value in patch.outcome.model_dump().items() if value is not None
                ),
                "evidence_added": len(patch.evidence_additions),
                "evidence_retired": retired,
                "ignored_instructions": ignored,
                "restored": restorations,
                "valid_alone": alone.valid,
                "remaining_issues": list(alone.issues),
            })
        usage = append_llm_usage(
            usage, role=SIBLING_REPAIR_ROLE, model=context.semantic_model_name, response=raw,
            input_text=input_text, output_text=output_text,
            budget_tokens=context.task_token_budget,
            duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
            status=status, price_catalog=context.price_catalog,
        )
    validation = validate_outcome_hypotheses(
        user_task, interpretation.outcome_hypotheses, interpretation.request_mode,
    )
    return interpretation, validation, usage, budget_warnings
