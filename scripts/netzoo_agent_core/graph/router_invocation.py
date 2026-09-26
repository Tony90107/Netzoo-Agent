"""Semantic → evidence → registry → intent routing pipeline."""

from __future__ import annotations

import time

from ..contracts import AgentState, LLMUsage, _trace
from ..contracts.outcomes import (
    CapabilityMatch,
    SemanticInterpretation,
    SemanticPatch,
    SemanticReview,
)
from ..contracts.repair_scope import permitted_fields
from ..interpretation.assembly import assemble_task_decision
from ..interpretation.hydration import hydrate_router_decision
from ..interpretation.outcome_consistency import (
    complete_open_granularity_alternatives,
)
from ..interpretation.stated_field_restoration import restore_stated_fields
from ..interpretation.outcome_validation import evidence_census, validate_outcome_hypotheses
from ..interpretation.provider_fallback import (
    _is_fatal_exception,
    deterministic_router_fallback,
    recover_ambiguous_input,
    recover_explicit_run,
    recover_registry_guidance,
)
from ..interpretation.outcome_downgrade import interpretation_downgrades
from ..interpretation.semantic_goal import outcome_routing_state
from ..interpretation.semantic_patch import (
    apply_semantic_patch, patched_hypothesis_index,
)
from ..interpretation.semantic_repair import semantic_payload
from ..interpretation.unverified_evidence import (
    UNVERIFIED_BASIS, bounded_match, with_reduced_confidence,
)
from ..llm import (
    append_llm_usage,
    build_semantic_interpreter_messages,
    build_semantic_patch_messages,
    build_semantic_reviewer_messages,
)
from ..routing.capability import (
    apply_input_preflight_intent,
    has_direct_retrieval_request,
    reconcile_request_mode,
)
from ..routing.named_labels import named_registered_action
from ..routing.outcome_matching import match_semantic_request
from .context import _GraphContext, preflight_budget, record_event
from .continuation_invocation import continue_workflow
from .intent_invocation import _invoke_intent_router
from .invocation_types import RouterInvocation as _RouterInvocation
from .semantic_review_validation import (
    _as_semantic_patch,
    _validated_review,
    normalize_advice_operation_evidence,
    normalize_role_entailed_artifact_evidence,
)
from .structured_calls import _serialized_structured_input, _validation_issue_types
from .condition_recommender import invoke_condition_recommender
from .discriminator import (
    discriminator_context as _discriminator_context,
    invoke_semantic_discriminator as _invoke_semantic_discriminator,
    _fill_inferred_role_evidence,
)

__all__: list[str] = []


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
    recovered = recover_explicit_run(
        user_task,
        context.project_policy.workflows,
        error,
    ) or recover_registry_guidance(
        user_task,
        context.project_policy.workflows,
        error,
    ) or recover_ambiguous_input(
        user_task,
        error,
    )
    if recovered is not None:
        decision = hydrate_router_decision(recovered, user_task)
        record_event(
            context,
            state,
            "routing.explicit_run_recovered",
            "classify",
            {
                "matched_actions": decision.matched_actions,
                "reason_code": decision.match_basis,
                "match_status": decision.capability_match_status,
            },
        )
    else:
        # Even when semantic routing fails, an explicit input-preflight request
        # is safe to route deterministically because inspection does not infer a
        # scientific outcome or execute a workflow.  Hydrate first so concrete
        # file bindings are preserved for the downstream inspector.
        decision = hydrate_router_decision(decision, user_task)
    preflight_decision = apply_input_preflight_intent(decision, user_task)
    if preflight_decision is not decision:
        record_event(
            context,
            state,
            "routing.input_preflight_reconciled",
            "classify",
            {
                "action": "inspect_inputs",
                "missing_inputs": preflight_decision.missing_inputs,
                "fallback": True,
            },
        )
    decision = preflight_decision
    return _RouterInvocation(
        decision=decision,
        routing_state=outcome_routing_state(decision),
        usage=usage,
        budget_warnings=budget_warnings,
        reason_code=reason_code,
    )


def _invoke_semantic_interpreter(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
    usage: LLMUsage,
) -> tuple[
    SemanticInterpretation | None,
    LLMUsage,
    list[str],
    BaseException | None,
    frozenset[str],
]:
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
    discriminator_context = ""
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
            and not any(
                "inconsistent_not_applicable_outcome" in issue
                for issue in validation_issues
            )
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
                discriminator_context,
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
        payload = None
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
            patch_evidence_normalizations = []
            if patching:
                payload, patch_evidence_normalizations = (
                    normalize_role_entailed_artifact_evidence(payload, user_task)
                )
                payload, advice_evidence_normalizations = (
                    normalize_advice_operation_evidence(
                        payload,
                        user_task,
                        proposal_request_mode=proposal.request_mode,
                    )
                )
                patch_evidence_normalizations.extend(advice_evidence_normalizations)
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
                licensed = permitted_fields(validation_issues)
                interpretation, retired_evidence = apply_semantic_patch(
                    proposal, patch, permitted_fields=licensed,
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
                        "evidence_retired_as_stale": [
                            item for item in retired_evidence
                            if "reason" not in item
                        ],
                        "evidence_additions_dropped": [
                            item for item in retired_evidence
                            if "reason" in item
                        ],
                        # What the rules that fired declared they examined.
                        # Overrides outside this set were not applied; an empty
                        # set is the citation-only case.
                        "permitted_fields": sorted(licensed),
                        "evidence_normalizations": patch_evidence_normalizations,
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
                    {
                        "attempt": 1,
                        "issues": list(validation_issues),
                        "shapes": schema_issues,
                        "provider_payload": payload,
                    },
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
                    "provider_payload": payload,
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
        # field. It can move a value stated in the hypothesis's own evidence;
        # after a review patch it may also align an under-specified or impossible
        # scalar to the sole value entailed by the already selected artifact. It
        # never picks an artifact or workflow. Validation below is unchanged.
        interpretation, restorations = restore_stated_fields(
            user_task,
            interpretation,
            align_artifact_constraints=patch is not None,
            restore_explicit_scalar_evidence=True,
        )
        if patch is not None:
            interpretation = _fill_inferred_role_evidence(interpretation)
        restored_tags = frozenset(
            str(item["value"]) for item in restorations
            if item["field"] == "selection_tags"
        )
        artifact_alignments = [
            item for item in restorations if item["source"] == "artifact_ontology"
        ]
        stated_restorations = [
            item for item in restorations if item["source"] != "artifact_ontology"
        ]
        if artifact_alignments:
            record_event(
                context,
                state,
                "routing.outcome_artifact_constraints_applied",
                "classify",
                {"attempt": attempt + 1, "alignments": artifact_alignments},
            )
        if stated_restorations:
            record_event(
                context,
                state,
                "routing.outcome_input_restored",
                "classify",
                {"attempt": attempt + 1, "restored": stated_restorations},
            )
        before_alternatives = interpretation.outcome_hypotheses
        completed_hypotheses = complete_open_granularity_alternatives(
            user_task, before_alternatives
        )
        if completed_hypotheses != before_alternatives:
            completion_validation = validate_outcome_hypotheses(
                user_task, completed_hypotheses
            )
            if completion_validation.valid:
                interpretation = interpretation.model_copy(
                    update={"outcome_hypotheses": completed_hypotheses}
                )
                record_event(
                    context,
                    state,
                    "routing.granularity_alternatives_completed",
                    "classify",
                    {
                        "alternatives": [
                            item.outcome.granularity
                            for item in completed_hypotheses
                        ],
                        "source": "explicit_undecided_request_witnesses",
                    },
                )
            else:
                record_event(
                    context,
                    state,
                    "routing.granularity_alternative_completion_rejected",
                    "classify",
                    {"issues": list(completion_validation.issues)},
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
                    "rejected_interpretation": interpretation.model_dump(mode="json"),
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
                    {
                        "attempt": attempt + 1,
                        "issues": list(validation.issues),
                        "rejected_interpretation": interpretation.model_dump(mode="json"),
                    },
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
                # An interpretation that does not know what was requested has
                # settled nothing, whatever the registry then says about it. This
                # guard used to sit inside the `exact` arm alone, so a reading
                # with every dimension unknown -- the shape that encodes "out of
                # scope", and equally the shape produced whenever the request
                # states something the outcome vocabulary has no dimension for --
                # ended routing on the first attempt with no review at all. The
                # review is the only step that can tell those two apart. The cost
                # is one extra call on a request that really is out of scope.
                and interpretation.outcome_hypotheses[0].outcome.operation != "unknown"
                and (
                    preliminary_match.status == "not_applicable"
                    or len(preliminary_match.matched_actions) == 1
                )
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
                discriminator_context = _discriminator_context(
                    list(preliminary_match.hypothesis_actions)
                )
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
        return continue_workflow(context, state, user_task, usage)
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

    reconciled_request_mode = reconcile_request_mode(
        user_task,
        interpretation.request_mode,
    )
    if reconciled_request_mode != interpretation.request_mode:
        interpretation = interpretation.model_copy(
            update={"request_mode": reconciled_request_mode}
        )
        record_event(
            context,
            state,
            "routing.explicit_execution_reconciled",
            "classify",
            {"request_mode": reconciled_request_mode},
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
    (
        interpretation,
        capability_match,
        usage,
        budget_warnings,
    ) = _invoke_semantic_discriminator(
        context,
        state,
        user_task,
        interpretation,
        capability_match,
        usage,
        budget_warnings,
    )
    # A direct read-only retrieval request is already an explicit capability
    # selection. It must not be held behind the scientific-outcome evidence gate:
    # an empty/irrelevant semantic hypothesis can make the generic matcher
    # ``unverified`` even though WEB-SEARCH/CONTEXT7 is the exact requested tool.
    direct_retrieval_action = (
        named_registered_action(user_task)
        if has_direct_retrieval_request(user_task)
        else None
    )
    if direct_retrieval_action in {"web_search", "query_context7"}:
        capability_match = CapabilityMatch(
            status="exact",
            match_basis="workflow_name",
            matched_actions=[direct_retrieval_action],
        )
    # An interpretation reaches the registry either fully grounded or explicitly
    # marked. Re-deriving that here from the same validator, rather than trusting
    # a flag passed down, is what makes the bound checkable at the one place it
    # has to hold: nothing whose quotes the request does not contain may present
    # itself as an exact match or authorize an action.
    if (
        direct_retrieval_action is None
        and not validate_outcome_hypotheses(user_task, interpretation.outcome_hypotheses).valid
    ):
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
    reconciled_intent_mode = reconcile_request_mode(user_task, intent.mode)
    if reconciled_intent_mode != intent.mode:
        intent = intent.model_copy(
            update={
                "mode": "execute",
                "reason": (
                    "The request explicitly authorizes execution or direct read-only "
                    "retrieval; deterministic command-language routing selected execute."
                ),
            }
        )
        record_event(
            context,
            state,
            "routing.explicit_execution_reconciled",
            "classify",
            {"intent_mode": "execute"},
        )
    decision = assemble_task_decision(
        interpretation,
        capability_match,
        intent,
        task=user_task,
    )
    decision = hydrate_router_decision(decision, user_task)
    if direct_retrieval_action in {"web_search", "query_context7"}:
        decision = decision.model_copy(update={"intent_type": "answer_question"})
    if capability_match.match_basis == UNVERIFIED_BASIS:
        # The second half of the bound. A reading whose quotes were not found is
        # something to show the user, never something to act on, whatever the
        # intent router concluded about the request's mood.
        decision = decision.model_copy(update={
            "should_execute": False, "action": "no_tool",
        })
    # Log 139: after intent, so neither the intent router's input nor the
    # capability match changes; the stage only adds advice and a question.
    decision, usage, budget_warnings = invoke_condition_recommender(
        context, state, user_task, decision, usage, budget_warnings,
    )
    preflight_decision = apply_input_preflight_intent(decision, user_task)
    if preflight_decision is not decision:
        record_event(
            context,
            state,
            "routing.input_preflight_reconciled",
            "classify",
            {
                "action": "inspect_inputs",
                "missing_inputs": preflight_decision.missing_inputs,
            },
        )
    decision = preflight_decision
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
