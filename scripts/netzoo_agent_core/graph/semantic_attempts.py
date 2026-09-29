"""The bounded semantic interpretation attempts: first pass, then one review.

Moved verbatim out of `router_invocation` (Log 190) when that module reached
the 1000-line review limit; `router_invocation` re-exports every name it used
to define here, so callers and tests are unchanged.
"""

from __future__ import annotations

import time

from ..contracts import AgentState, LLMUsage, _trace
from ..contracts.outcomes import (
    SemanticInterpretation,
    SemanticPatch,
    SemanticReview,
)
from ..contracts.repair_scope import permitted_fields
from ..interpretation.outcome_consistency import (
    complete_open_granularity_alternatives,
)
from ..interpretation.stated_field_restoration import restore_stated_fields
from ..interpretation.outcome_validation import evidence_census, validate_outcome_hypotheses
from ..interpretation.provider_fallback import (
    _is_fatal_exception,
    recover_registry_guidance,
)
from ..interpretation.outcome_downgrade import interpretation_downgrades
from ..interpretation.semantic_patch import (
    apply_semantic_patch, patched_hypothesis_index,
)
from ..interpretation.semantic_repair import semantic_payload
from ..interpretation.unverified_evidence import with_reduced_confidence
from ..interpretation.guidance_subject import (
    GuidanceSubjectReview, guidance_subject_review_issues,
    restore_guidance_subject, subject_review_prompt,
)
from ..llm import (
    append_llm_usage,
    build_semantic_interpreter_messages,
    build_semantic_patch_messages,
    build_semantic_reviewer_messages,
)
from ..routing.outcome_matching import match_semantic_request
from .context import _GraphContext, preflight_budget, record_event
from .semantic_review_validation import (
    _as_semantic_patch,
    _validated_review,
    normalize_advice_operation_evidence,
    normalize_role_entailed_artifact_evidence,
)
from .structured_calls import _serialized_structured_input, _validation_issue_types
from .partial_validity import issue_indices, keep_valid_hypotheses, retain_valid_first_pass, valid_first_pass_subset
from .sibling_repair import repair_sibling_hypotheses
from .discriminator import (
    discriminator_context as _discriminator_context,
    _fill_inferred_role_evidence,
)
from .evidence_supply import evidence_supply_schema, supplied_pairs, supply_as_patch
from .first_pass_salvage import validate_first_pass
from .semantic_shape import nest_unresolved_dimensions

__all__ = ["MAX_SEMANTIC_ATTEMPTS", "invoke_semantic_interpreter"]


# A third, progress-gated attempt was tried and reverted. It fired twice in nine
# live trials and made the outcome worse both times: the extra review dropped an
# input it had already recovered and added ungrounded evidence, while the error
# it was meant to fix survived. Overall passes were unchanged, so it bought an
# extra call and nothing else. See tests/test_semantic_attempt_bound.py.
MAX_SEMANTIC_ATTEMPTS = 2


def invoke_semantic_interpreter(
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
    partial_first: SemanticInterpretation | None = None
    for attempt in range(MAX_SEMANTIC_ATTEMPTS):
        role = "semantic_interpreter" if attempt == 0 else "semantic_reviewer"
        subject_recovery = (
            attempt == 1 and validated is not None and isinstance(proposal, SemanticInterpretation)
            and all(item.outcome.artifact_type == "unknown" for item in proposal.outcome_hypotheses)
            and any("unresolved_guidance_subject:" in issue for issue in validation_issues)
        )
        # A patch can only be merged onto a structurally valid proposal. When the
        # first pass did not parse, there is nothing to carry forward and the
        # review still owns the whole structure.
        patching = (
            attempt == 1
            and not subject_recovery
            and getattr(context, "semantic_patcher", None) is not None
            and isinstance(proposal, SemanticInterpretation)
            and not any(
                "inconsistent_not_applicable_outcome" in issue
                for issue in validation_issues
            )
        )
        # Log 198: when every first-pass issue is evidence the proposal did not
        # give, the same patch messages are answered in a strict schema holding
        # exactly those entries. The raw semantic provider binds it per call.
        supply = (
            supplied_pairs(validation_issues, proposal)
            if patching and getattr(context, "selection_condition_llm", None) is not None
            else None
        )
        supply_schema = evidence_supply_schema(supply) if supply else None
        adapter = (
            context.semantic_interpreter if attempt == 0
            else context.selection_condition_llm.with_structured_output(
                supply_schema, method="function_calling", include_raw=True, strict=True,
            ) if supply
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
            else supply_schema if supply
            else SemanticPatch if patching
            else SemanticReview
        )
        compact_subject = subject_recovery and getattr(context, "selection_condition_llm", None) is not None
        if compact_subject:
            schema_model = GuidanceSubjectReview
            adapter = context.selection_condition_llm.with_structured_output(
                GuidanceSubjectReview, method="function_calling", include_raw=True, strict=True,
            )
        if subject_recovery:
            messages[0] = messages[0].model_copy(update={"content": subject_review_prompt(schema_model.__name__)})
            if subject_recovery:
                # There is no grounded scientific subject to carry forward. An
                # independent reading avoids anchoring on an empty draft.
                messages = messages[:2]
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
            payload, nesting = nest_unresolved_dimensions(payload)
            if nesting:
                record_event(context, state, "routing.semantic_shape_normalized", "classify", {"attempt": attempt + 1, "moved": nesting})
            if attempt == 0:
                proposal = payload
            patch_evidence_normalizations = []
            if supply:
                payload = supply_as_patch(payload, supply)
                record_event(context, state, "routing.semantic_evidence_supplied", "classify", {
                    "attempt": attempt + 1,
                    "requested": [f"hypothesis[{i}].{d}={v}" for i, d, v in supply],
                    "sources": [item.get("source") for item in payload["evidence_additions"]],
                })
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
            if compact_subject:
                review = GuidanceSubjectReview.model_validate(payload)
                output_text = review.model_dump_json()
                interpretation = restore_guidance_subject(proposal, review)
                record_event(context, state, "routing.guidance_subject_reviewed", "classify", review.model_dump())
            elif attempt == 0:
                # Logs 213, 215: faulty evidence entries or root-level
                # assumptions alone do not discard the draft.
                interpretation, salvage = validate_first_pass(payload)
                if salvage:
                    record_event(context, state, "routing.semantic_first_pass_salvaged", "classify", {
                        "attempt": 1, **salvage,
                    })
                output_text = interpretation.model_dump_json()
            elif patch is not None:
                output_text = patch.model_dump_json()
                licensed = permitted_fields(validation_issues)
                interpretation, retired_evidence = apply_semantic_patch(
                    proposal, patch, permitted_fields=licensed, user_task=user_task,
                    hold_validated=(validated is not None
                                    and not guidance_subject_review_issues(validated)),
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
                        # Entries made stale, additions dropped, withdrawals ignored (Log 164).
                        "evidence_retired_as_stale": [i for i in retired_evidence if "reason" not in i],
                        "evidence_additions_dropped": [
                            i for i in retired_evidence
                            if i.get("reason") == "addition_does_not_match_merged_outcome"
                        ],
                        "evidence_withdrawals_ignored": [
                            i for i in retired_evidence
                            if i.get("reason") == "withdrawal_of_asserted_value"
                        ],
                        "overrides_held": [
                            i for i in retired_evidence
                            if i.get("reason") == "override_of_validated_value_without_quote"
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
                    and not subject_recovery
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
            validated = retain_valid_first_pass(context, state, validated, partial_first, attempt)
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
            align_artifact_constraints=patch is not None or compact_subject,
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
                user_task, completed_hypotheses, interpretation.request_mode,
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
            interpretation.request_mode,
        )
        invalid_before_sibling_repair = frozenset(issue_indices(validation.issues))
        if patch is not None:
            interpretation, validation, usage, budget_warnings = repair_sibling_hypotheses(
                context, state, user_task, interpretation, validation,
                patched_index=patched_index, usage=usage, budget_warnings=budget_warnings,
                discriminator_context=discriminator_context,
            )
        if attempt + 1 >= MAX_SEMANTIC_ATTEMPTS:
            interpretation, validation = keep_valid_hypotheses(
                context, state, user_task, interpretation, validation, attempt,
                primary=patched_index if patch is not None else None,
                invalid_before_sibling_repair=(invalid_before_sibling_repair if patch is not None else frozenset()))
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
                partial_first = valid_first_pass_subset(user_task, interpretation)
            if attempt + 1 < MAX_SEMANTIC_ATTEMPTS:
                validation_issues = (*validation.issues, *guidance_subject_review_issues(interpretation))
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
            validated = retain_valid_first_pass(context, state, validated, partial_first, attempt)
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
            subject_issues = guidance_subject_review_issues(interpretation)
            if subject_issues:
                validation_issues = subject_issues
                record_event(context, state, "routing.guidance_subject_review_requested", "classify", {
                    "issues": list(subject_issues), "attempt": 1,
                })
                continue
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
