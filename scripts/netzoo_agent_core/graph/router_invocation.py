"""Semantic → evidence → registry → intent routing pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from typing import get_args
from dataclasses import dataclass
import json
import re
import time

from pydantic import ValidationError
from workflow_registry import OUTPUT_CAPABILITIES

from ..contracts import AgentState, IntentDecision, LLMUsage, TaskDecision, _trace
from ..contracts.interaction import WorkflowContinuation
from ..contracts.outcomes import (
    CapabilityMatch,
    EvidenceDimension,
    RequestedOutcome,
    SemanticInterpretation,
    SemanticPatch,
    SemanticReview,
)
from ..interpretation.assembly import assemble_task_decision
from ..interpretation.hydration import hydrate_router_decision
from ..interpretation.stated_field_restoration import restore_stated_fields
from ..interpretation.outcome_validation import evidence_census, validate_outcome_hypotheses
from ..interpretation.provider_fallback import (
    _is_fatal_exception,
    deterministic_router_fallback,
    recover_registry_guidance,
)
from ..interpretation.outcome_downgrade import interpretation_downgrades
from ..interpretation.semantic_goal import outcome_routing_state
from ..interpretation.semantic_patch import (
    apply_semantic_patch, evidence_only_repair, patched_hypothesis_index,
)
from ..interpretation.semantic_repair import semantic_payload
from ..interpretation.unverified_evidence import (
    UNVERIFIED_BASIS, bounded_match, with_reduced_confidence,
)
from ..llm import (
    append_llm_usage,
    build_intent_router_messages,
    build_semantic_interpreter_messages,
    build_semantic_patch_messages,
    build_semantic_reviewer_messages,
    structured_result_payload,
)
from ..routing.outcome_matching import match_semantic_request
from .context import _GraphContext, preflight_budget, record_event
from .intent_invocation import _invoke_intent_router
from .structured_calls import _serialized_structured_input, _validation_issue_types

__all__: list[str] = []


@dataclass(frozen=True, slots=True)
class _RouterInvocation:
    decision: TaskDecision
    routing_state: dict
    usage: LLMUsage
    budget_warnings: list[str]
    reason_code: str


# A third, progress-gated attempt was tried and reverted. It fired twice in nine
# live trials and made the outcome worse both times: the extra review dropped an
# input it had already recovered and added ungrounded evidence, while the error
# it was meant to fix survived. Overall passes were unchanged, so it bought an
# extra call and nothing else. See tests/test_semantic_attempt_bound.py.
MAX_SEMANTIC_ATTEMPTS = 2


def _current_usage(context: _GraphContext, state: AgentState) -> LLMUsage:
    current = state.get("token_usage")
    return (
        LLMUsage.model_validate(current)
        if current
        else LLMUsage(budget_tokens=context.task_token_budget)
    )


def _semantic_failure(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
    usage: LLMUsage,
    budget_warnings: list[str],
    *,
    error: BaseException | None = None,
    reason_code: str,
) -> _RouterInvocation:
    decision = deterministic_router_fallback(user_task, error)
    recovered = recover_registry_guidance(
        user_task,
        context.project_policy.workflows,
        error,
    )
    if recovered is not None:
        decision = recovered
        record_event(
            context,
            state,
            "routing.semantic_guidance_recovered",
            "classify",
            {
                "matched_actions": decision.matched_actions,
                "reason_code": decision.match_basis,
                "match_status": decision.capability_match_status,
            },
        )
    return _RouterInvocation(
        decision=decision,
        routing_state=outcome_routing_state(decision),
        usage=usage,
        budget_warnings=budget_warnings,
        reason_code=reason_code,
    )


#: The closed vocabulary a removal instruction must name to mean anything.
_EVIDENCE_DIMENSIONS = frozenset(get_args(EvidenceDimension))


def _honourable_removals(payload) -> tuple[object, list[dict]]:
    """Set aside evidence-list instructions that cannot be carried out.

    Two shapes cost the whole repair -- including the well-formed additions that
    were the repair -- for the sake of one instruction that could never have had
    an effect. Both were the entire residual of a matched-control round: 5 trials
    of the first and 6 of the second, out of 14 failures in 36.

    A removal names one (dimension, value) to withdraw. When its `dimension` is
    outside the closed vocabulary it names nothing that can exist in the evidence
    list, so honouring it and ignoring it are the same act -- while rejecting the
    patch over it is not. Only removals are treated this way: a malformed
    *addition* is the repair itself failing, and stays strict.

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
                ignored.append({"reason": "removal_names_no_dimension",
                                "field": "evidence_removals"})
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

def _invoke_semantic_interpreter(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
    usage: LLMUsage,
) -> tuple[SemanticInterpretation | None, LLMUsage, list[str], BaseException | None]:
    if getattr(context, "semantic_claims", False):
        from .claim_invocation import invoke_claim_interpreter
        return invoke_claim_interpreter(context, state, user_task, usage,
            serialize=_serialized_structured_input, schema_errors=_validation_issue_types)
    validation_issues: tuple[str, ...] = ()
    budget_warnings = list(state.get("budget_warnings", []))
    last_error: BaseException | None = None
    proposal = None
    # The reviewer is a second opinion, not a precondition. An interpretation
    # that already satisfied every check is kept if the review that follows does
    # not, because discarding both leaves a registry guess naming no workflow.
    validated: SemanticInterpretation | None = None
    # Tags this function moved into the outcome, kept out of capability
    # selection: a harness repair must never be what picks a tool.
    restored_tags: frozenset[str] = frozenset()
    # Measurement only, read at acceptance. The first pass's own grounding
    # result per (dimension, value), and the hypothesis a patch was merged onto,
    # are both gone by the time the accepted interpretation exists -- and
    # without them a dimension that ends up `unknown` cannot be told apart from
    # one that was never committed to. Neither influences any decision below.
    first_pass_shapes: tuple[dict, ...] = ()
    patched_index: int | None = None
    for attempt in range(MAX_SEMANTIC_ATTEMPTS):
        role = "semantic_interpreter" if attempt == 0 else "semantic_reviewer"
        # A patch can only be merged onto a structurally valid proposal. When the
        # first pass did not parse, there is nothing to carry forward and the
        # review still owns the whole structure.
        patching = (
            attempt == 1
            and getattr(context, "semantic_patcher", None) is not None
            and isinstance(proposal, SemanticInterpretation)
        )
        adapter = (
            context.semantic_interpreter if attempt == 0
            else context.semantic_patcher if patching
            else context.semantic_reviewer
        )
        messages = (
            (build_semantic_patch_messages if patching else build_semantic_reviewer_messages)(
                context.semantic_prompt,
                user_task,
                proposal,
                validation_issues,
            )
            if attempt == 1
            else build_semantic_interpreter_messages(
                context.semantic_prompt,
                user_task,
                validation_issues,
            )
        )
        schema_model = (
            SemanticInterpretation if attempt == 0
            else SemanticPatch if patching
            else SemanticReview
        )
        input_text = _serialized_structured_input(messages, schema_model)
        semantic_state = dict(state)
        semantic_state["token_usage"] = usage.model_dump()
        semantic_state["budget_warnings"] = budget_warnings
        budget, budget_warnings = preflight_budget(
            context,
            semantic_state,
            role=role,
            model=context.semantic_model_name,
            input_text=input_text,
            reserved_output_tokens=context.router_max_tokens,
            allow_reserve=False,
        )
        if budget.status == "blocked":
            usage.budget_exhausted = True
            return None, usage, budget_warnings, last_error, restored_tags

        started_ns = time.monotonic_ns()
        raw = None
        output_text = ""
        try:
            _trace(
                "router",
                "Semantic interpretation started",
                {
                    "kind": "router_activity",
                    "operation": "semantic_interpreter",
                    "status": "started",
                    "attempt": attempt + 1,
                },
            )
            structured = adapter.invoke(messages)
            payload, raw = semantic_payload(structured)
            if attempt == 0:
                proposal = payload
            # `patching` is only ever true on the second attempt, so this reads
            # the reply as a patch exactly when one was asked for.
            patch, ignored_instructions = (
                _as_semantic_patch(payload) if patching else (None, [])
            )
            if attempt == 0:
                interpretation = SemanticInterpretation.model_validate(payload)
                output_text = interpretation.model_dump_json()
            elif patch is not None:
                output_text = patch.model_dump_json()
                citations_only = evidence_only_repair(validation_issues)
                interpretation, retired_evidence = apply_semantic_patch(
                    proposal, patch, evidence_only=citations_only,
                )
                patched_index = patched_hypothesis_index(proposal, patch)
                record_event(
                    context,
                    state,
                    "routing.semantic_patch_applied",
                    "classify",
                    {
                        "attempt": attempt + 1,
                        "hypothesis_index": patched_hypothesis_index(proposal, patch),
                        "changed_fields": sorted(
                            name for name, value in patch.outcome.model_dump().items()
                            if value is not None
                        ),
                        "evidence_removed": [
                            {"dimension": item.dimension, "value": item.value}
                            for item in patch.evidence_removals
                        ],
                        "evidence_added": len(patch.evidence_additions),
                        # Entries the patch itself made stale by changing their
                        # dimension. Recorded, never silently dropped.
                        "evidence_retired_as_stale": retired_evidence,
                        # True when the rejection named only missing citations,
                        # so the patch's outcome overrides were dropped.
                        "evidence_only": citations_only,
                        # Instructions that could not be carried out, set aside
                        # rather than costing the repair. Never silent.
                        "ignored_instructions": ignored_instructions,
                    },
                )
            else:
                review = _validated_review(payload, patching=patching)
                output_text = review.model_dump_json()
                # A whole review carries one hypothesis and no index, so it
                # cannot say which of several it replaces -- and rebuilding the
                # interpretation from it alone deletes the rest. A first pass
                # that offered two granularities was collapsed that way into a
                # confident single answer, losing an ambiguity the validator had
                # correctly identified. Where the proposal really was ambiguous,
                # this reply does not answer the contract that was asked for, so
                # the validated first pass is kept instead (the exception
                # authorized for a failed review) rather than inventing a merge.
                if (
                    isinstance(proposal, SemanticInterpretation)
                    and len(proposal.outcome_hypotheses) > 1
                    and validated is not None
                ):
                    # The call happened and is billed, so it is accounted for
                    # before returning. An early return that skipped this would
                    # hide a paid call from the token budget.
                    usage = append_llm_usage(
                        usage,
                        role=role,
                        model=context.semantic_model_name,
                        response=raw,
                        input_text=input_text,
                        output_text=output_text,
                        budget_tokens=context.task_token_budget,
                        duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
                        status="failed",
                        price_catalog=context.price_catalog,
                    )
                    record_event(
                        context,
                        state,
                        "routing.semantic_review_discarded",
                        "classify",
                        {
                            "attempt": attempt + 1,
                            "issues": [
                                "whole_review_cannot_represent_multiple_hypotheses:"
                                f"{len(proposal.outcome_hypotheses)}"
                            ],
                        },
                    )
                    return validated, usage, budget_warnings, None, restored_tags
                interpretation = SemanticInterpretation(
                    request_mode=review.request_mode,
                    semantic_goal=review.semantic_goal,
                    outcome_hypotheses=[review.outcome_hypothesis],
                )
            if attempt == 0:
                proposal = interpretation
        except BaseException as error:
            if _is_fatal_exception(error):
                raise
            duration_ms = max(0, (time.monotonic_ns() - started_ns) // 1_000_000)
            schema_issues = _validation_issue_types(error)
            usage = append_llm_usage(
                usage,
                role=role,
                model=context.semantic_model_name,
                response=raw,
                input_text=input_text,
                output_text=output_text,
                budget_tokens=context.task_token_budget,
                duration_ms=duration_ms,
                status="failed",
                price_catalog=context.price_catalog,
            )
            if attempt == 0 and schema_issues:
                validation_issues = tuple(
                    "schema_validation:"
                    + ".".join(issue["location"])
                    + ":"
                    + str(issue["type"])
                    for issue in schema_issues
                )
                last_error = error
                record_event(
                    context,
                    state,
                    "routing.semantic_interpretation_rejected",
                    "classify",
                    # Keep the located shapes beside the flattened issue strings:
                    # the first attempt is where a rejected value is otherwise lost.
                    {"attempt": 1, "issues": list(validation_issues), "shapes": schema_issues},
                )
                record_event(
                    context,
                    state,
                    "routing.semantic_interpretation_retried",
                    "classify",
                    {"issues": list(validation_issues)},
                )
                continue
            record_event(
                context,
                state,
                "routing.semantic_interpreter_failed",
                "classify",
                {
                    "attempt": attempt + 1,
                    "error_type": type(error).__name__,
                    "validation_issues": schema_issues,
                },
            )
            # A review that does not parse is still only a second opinion. The
            # branch below already keeps a validated first pass when the review
            # parses and fails validation; a review that breaks the wire contract
            # is no better an argument for discarding it. Six of the losses in the
            # live record are this branch: a first pass that passed every check,
            # replaced by a registry guess naming no workflow. Nothing is filled
            # in -- what is returned is the first pass the validator accepted.
            if validated is not None:
                record_event(
                    context,
                    state,
                    "routing.semantic_review_discarded",
                    "classify",
                    {
                        "attempt": attempt + 1,
                        "issues": [
                            "schema_validation:"
                            + ".".join(issue["location"])
                            + ":"
                            + str(issue["type"])
                            for issue in schema_issues
                        ],
                    },
                )
                return validated, usage, budget_warnings, None, restored_tags
            if recover_registry_guidance(
                user_task,
                context.project_policy.workflows,
                error,
            ) is None:
                _trace(
                    "router",
                    "Semantic interpretation failed",
                    {
                        "kind": "router_activity",
                        "operation": "semantic_interpreter",
                        "status": "failed",
                        "error_type": type(error).__name__,
                    },
                )
            return None, usage, budget_warnings, error, restored_tags

        # The one authorized place the deterministic layer writes an outcome
        # field. It moves a value this hypothesis already stated in its own
        # evidence into the field that carries it, and never invents one.
        # Validation below is unchanged.
        interpretation, restored_inputs = restore_stated_fields(
            user_task, interpretation,
        )
        restored_tags = frozenset(
            str(item["value"]) for item in restored_inputs
            if item["field"] == "selection_tags"
        )
        if restored_inputs:
            record_event(
                context,
                state,
                "routing.outcome_input_restored",
                "classify",
                {"attempt": attempt + 1, "restored": restored_inputs},
            )
        validation = validate_outcome_hypotheses(
            user_task,
            interpretation.outcome_hypotheses,
        )
        duration_ms = max(0, (time.monotonic_ns() - started_ns) // 1_000_000)
        if not validation.valid:
            usage = append_llm_usage(
                usage,
                role=role,
                model=context.semantic_model_name,
                response=raw,
                input_text=input_text,
                output_text=output_text,
                budget_tokens=context.task_token_budget,
                duration_ms=duration_ms,
                status="failed",
                price_catalog=context.price_catalog,
            )
            record_event(
                context,
                state,
                "routing.semantic_interpretation_rejected",
                "classify",
                {
                    "attempt": attempt + 1,
                    "issues": list(validation.issues),
                    # Why each rejected quote failed, in closed vocabulary. The
                    # issue strings the next attempt sees are unchanged.
                    "evidence_shapes": [dict(item) for item in validation.evidence_shapes],
                    "evidence_census": [
                        dict(item) for item in evidence_census(interpretation.outcome_hypotheses)
                    ],
                },
            )
            last_error = ValueError(
                "semantic interpretation failed evidence validation"
            )
            if attempt == 0:
                first_pass_shapes = tuple(dict(item) for item in validation.evidence_shapes)
            if attempt + 1 < MAX_SEMANTIC_ATTEMPTS:
                validation_issues = validation.issues
                record_event(
                    context,
                    state,
                    "routing.semantic_interpretation_retried",
                    "classify",
                    {"issues": list(validation_issues)},
                )
                continue
            record_event(
                context,
                state,
                "routing.semantic_interpreter_failed",
                "classify",
                {
                    "attempt": attempt + 1,
                    "error_type": type(last_error).__name__,
                    "validation_issues": list(validation.issues),
                    "evidence_shapes": [dict(item) for item in validation.evidence_shapes],
                    "evidence_census": [
                        dict(item) for item in evidence_census(interpretation.outcome_hypotheses)
                    ],
                },
            )
            if validated is not None:
                record_event(
                    context,
                    state,
                    "routing.semantic_review_discarded",
                    "classify",
                    {"attempt": attempt + 1, "issues": list(validation.issues)},
                )
                return validated, usage, budget_warnings, None, restored_tags
            if validation.recoverable:
                # Every remaining issue is a quote the request does not contain,
                # and nothing else. Discarding the whole interpretation for that
                # is what cost 148 of 188 such entries their entire run, while
                # the reading itself was often right -- a misspelled request
                # makes a matching quote impossible, not the meaning unclear.
                # The reading is kept, its confidence reduced, and `invoke_router`
                # holds it below `exact` and away from execution. The issues are
                # still raised, still recorded, and still shown to the user; only
                # the disposition changes. `recoverable` was computed here since
                # the validator was written and read by nothing until now.
                record_event(
                    context,
                    state,
                    "routing.semantic_evidence_unverified",
                    "classify",
                    {
                        "attempt": attempt + 1,
                        "issues": list(validation.issues),
                        "evidence_shapes": [dict(item) for item in validation.evidence_shapes],
                    },
                )
                return (
                    with_reduced_confidence(interpretation),
                    usage, budget_warnings, None, restored_tags,
                )
            return None, usage, budget_warnings, last_error, restored_tags

        usage = append_llm_usage(
            usage,
            role=role,
            model=context.semantic_model_name,
            response=raw,
            input_text=input_text,
            output_text=output_text,
            budget_tokens=context.task_token_budget,
            duration_ms=duration_ms,
            price_catalog=context.price_catalog,
        )
        validated = interpretation
        if attempt == 0:
            preliminary_match = match_semantic_request(
                user_task,
                interpretation.outcome_hypotheses,
                request_mode=interpretation.request_mode,
                ignore_tags=restored_tags,
            )
            if (
                getattr(context, "review_policy", "always") == "when_needed"
                and preliminary_match.status in {"exact", "not_applicable"}
                and interpretation.request_mode != "unknown"
                and len(interpretation.outcome_hypotheses) == 1
                and not interpretation.outcome_hypotheses[0].outcome.unresolved_dimensions
                and (preliminary_match.status == "not_applicable" or (
                    len(preliminary_match.matched_actions) == 1
                    and interpretation.outcome_hypotheses[0].outcome.operation != "unknown"
                ))
            ):
                record_event(context, state, "routing.semantic_interpretation_accepted", "classify", {
                    "attempt": 1, "hypothesis_count": 1,
                    "registry_match_status": preliminary_match.status,
                    "review_skipped": "validated_complete_match",
                    "evidence_census": list(evidence_census(interpretation.outcome_hypotheses)),
                })
                _trace("router", "Semantic interpretation completed", {
                    "kind": "router_activity", "operation": "semantic_interpreter",
                    "status": "completed", "duration_ms": duration_ms, "attempt": 1,
                })
                return interpretation, usage, budget_warnings, None, restored_tags
            if preliminary_match.status == "ambiguous":
                validation_issues = (
                    "registry_ambiguity:the structured outcome does not uniquely "
                    "identify a capability; re-check the original request for explicit "
                    "biological entity, regulator, target, and granularity roles",
                )
            record_event(
                context,
                state,
                "routing.semantic_interpretation_proposed",
                "classify",
                {
                    "hypothesis_count": len(interpretation.outcome_hypotheses),
                    "evidence_dimensions": [
                        sorted({item.dimension for item in hypothesis.evidence})
                        for hypothesis in interpretation.outcome_hypotheses
                    ],
                    "evidence_census": [
                        dict(item) for item in evidence_census(interpretation.outcome_hypotheses)
                    ],
                    "registry_match_status": preliminary_match.status,
                },
            )
            continue

        # Measurement only. An accepted outcome saying `unknown` is recorded as
        # one fact today, and two opposite situations reach it: the first pass
        # said nothing either, or it named a value that is now gone. Only the
        # second is meaning the system had and discarded, and `unknown` is
        # exactly the value that needs no evidence -- so dropping a value always
        # dissolves an `ungrounded_evidence` issue about it. Nothing here
        # changes the interpretation, and the accepted event is emitted either way.
        downgrade = interpretation_downgrades(
            proposal, interpretation, first_pass_shapes,
            hypothesis_index=patched_index,
        )
        record_event(
            context,
            state,
            "routing.outcome_downgraded",
            "classify",
            {
                "attempt": attempt + 1,
                # False means the two interpretations could not be put in
                # correspondence, and the empty list below says nothing at all.
                "comparable": downgrade.comparable,
                "reason": downgrade.reason,
                "hypothesis": downgrade.hypothesis_index,
                "downgrades": [dict(item) for item in downgrade.downgrades],
            },
        )
        record_event(
            context,
            state,
            "routing.semantic_interpretation_accepted",
            "classify",
            {
                "attempt": attempt + 1,
                "hypothesis_count": len(interpretation.outcome_hypotheses),
                "evidence_dimensions": [
                    sorted({item.dimension for item in hypothesis.evidence})
                    for hypothesis in interpretation.outcome_hypotheses
                ],
                "evidence_census": [
                    dict(item) for item in evidence_census(interpretation.outcome_hypotheses)
                ],
            },
        )
        _trace(
            "router",
            "Semantic interpretation completed",
            {
                "kind": "router_activity",
                "operation": "semantic_interpreter",
                "status": "completed",
                "duration_ms": duration_ms,
                "attempt": attempt + 1,
            },
        )
        return interpretation, usage, budget_warnings, None, restored_tags

    return None, usage, budget_warnings, last_error, restored_tags


def invoke_router(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
) -> _RouterInvocation:
    """Run the ordered semantic, validation, registry, and intent pipeline."""
    usage = _current_usage(context, state)
    if state.get("workflow_continuation") is not None:
        return _continue_workflow(context, state, user_task, usage)
    interpretation, usage, budget_warnings, semantic_error, restored_tags = (
        _invoke_semantic_interpreter(context, state, user_task, usage)
    )
    if interpretation is None:
        return _semantic_failure(
            context,
            state,
            user_task,
            usage,
            budget_warnings,
            error=semantic_error,
            reason_code=("budget_fallback" if semantic_error is None else "semantic_fallback"),
        )

    _trace(
        "reasoning",
        "Checking registered workflow capabilities",
        {"kind": "registry_activity", "status": "started"},
    )
    capability_match = match_semantic_request(
        user_task,
        interpretation.outcome_hypotheses,
        request_mode=interpretation.request_mode,
        ignore_tags=restored_tags,
    )
    # An interpretation reaches the registry either fully grounded or explicitly
    # marked. Re-deriving that here from the same validator, rather than trusting
    # a flag passed down, is what makes the bound checkable at the one place it
    # has to hold: nothing whose quotes the request does not contain may present
    # itself as an exact match or authorize an action.
    if not validate_outcome_hypotheses(user_task, interpretation.outcome_hypotheses).valid:
        capability_match = bounded_match(capability_match)
        record_event(
            context,
            state,
            "routing.unverified_evidence_bounded",
            "classify",
            {
                "status": capability_match.status,
                "matched_actions": capability_match.matched_actions,
            },
        )
    record_event(
        context,
        state,
        "routing.registry_match_completed",
        "classify",
        {
            "status": capability_match.status,
            "match_basis": capability_match.match_basis,
            "rejected_methods": [item.model_dump() for item in capability_match.rejected_methods],
            "matched_actions": capability_match.matched_actions,
            "hypothesis_actions": capability_match.hypothesis_actions,
            "mismatch_dimensions": capability_match.mismatch_dimensions,
        },
    )

    intent, usage, budget_warnings, intent_fallback = _invoke_intent_router(
        context,
        state,
        user_task,
        interpretation,
        capability_match,
        usage,
        budget_warnings,
    )
    decision = assemble_task_decision(
        interpretation,
        capability_match,
        intent,
        task=user_task,
    )
    decision = hydrate_router_decision(decision, user_task)
    if capability_match.match_basis == UNVERIFIED_BASIS:
        # The second half of the bound. A reading whose quotes were not found is
        # something to show the user, never something to act on, whatever the
        # intent router concluded about the request's mood.
        decision = decision.model_copy(update={
            "should_execute": False, "action": "no_tool",
        })
    return _RouterInvocation(
        decision=decision,
        routing_state=outcome_routing_state(
            decision,
            interpretation.semantic_goal,
            interpretation.request_mode,
        ),
        usage=usage,
        budget_warnings=budget_warnings,
        reason_code=("intent_fallback" if intent_fallback else
                     "registry_guidance_fallback" if capability_match.status == "fallback" else
                     "semantic_registry_intent"),
    )


def _continue_workflow(
    context: _GraphContext,
    state: AgentState,
    task: str,
    usage: LLMUsage,
) -> _RouterInvocation:
    """Plan a CLI-validated selection without asking models to select it again."""
    try:
        continuation = WorkflowContinuation.model_validate(state["workflow_continuation"])
        if (
            continuation.task != task
            or continuation.action not in context.project_policy.workflows
        ):
            raise ValueError("The continuation does not match the current task and policy.")
    except (ValidationError, ValueError):
        decision = TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            confidence=0.0,
            intent_type="answer_question",
            reason="The workflow continuation is invalid or stale; select the workflow again.",
        )
        reason_code = "invalid_workflow_continuation"
    else:
        action = continuation.action
        capability = OUTPUT_CAPABILITIES[action]
        granularity = (
            next(iter(capability.granularities))
            if len(capability.granularities) == 1
            else "unknown"
        )
        decision = hydrate_router_decision(
            TaskDecision(
                action=action,
                in_scope=True,
                should_execute=True,
                confidence=1.0,
                intent_type="run_analysis",
                reason="Preparing the workflow selected in the current CLI continuation.",
                candidate_actions=[action, "no_tool"],
                matched_actions=[action],
                recommended_actions=[action],
                capability_match_status="exact",
                requested_outcome=RequestedOutcome(
                    operation=capability.operation,
                    artifact_type=capability.artifact_type,
                    entity_types=sorted(capability.entity_types),
                    regulator_types=sorted(capability.regulator_types),
                    target_types=sorted(capability.target_types),
                    granularity=granularity,
                    unresolved_dimensions=(
                        ["granularity"] if granularity == "unknown" else []
                    ),
                ),
            ),
            task,
        )
        reason_code = "workflow_continuation"
    record_event(
        context, state, "routing.workflow_continuation", "classify",
        {
            "action": decision.action,
            "reason_code": reason_code,
            "purpose": "planning",
            "execution_authorized": False,
        },
    )
    return _RouterInvocation(
        decision=decision,
        routing_state=outcome_routing_state(
            decision,
            decision.reason,
            "execute" if decision.action != "no_tool" else "unknown",
        ),
        usage=usage,
        budget_warnings=list(state.get("budget_warnings", [])),
        reason_code=reason_code,
    )
