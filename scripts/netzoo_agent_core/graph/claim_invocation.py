"""Bounded semantic inference with atomic claims and conditional repair."""

import re
import time
from workflow_registry import OUTPUT_CAPABILITIES
from ..contracts import _trace
from ..contracts.semantic_claims import SemanticClaims, SemanticClaimRepair
from ..contracts.repair_scope import FIELD_BY_DIMENSION, permitted_fields
from ..interpretation.claim_prompt import claim_messages
from ..interpretation.outcome_consistency import (
    complete_open_granularity_alternatives,
    has_complete_open_granularity_alternatives,
)
from ..interpretation.outcome_validation import (
    validate_outcome_hypotheses,
    evidence_census,
)
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.request_integrity import patient_clustering_goal
from ..interpretation.semantic_repair import semantic_payload
from ..interpretation.stated_field_restoration import restore_stated_fields
from ..llm import append_llm_usage
from ..routing.capability import reconcile_request_mode
from ..routing.capability_compatibility import _complete_guidance_match
from ..routing.outcome_matching import match_semantic_request
from .context import preflight_budget, record_event
from .discriminator import _recover_explicit_selection_tag
from .semantic_review_validation import normalize_advice_operation_evidence


class _NoOpClaimRepair(ValueError):
    """A reviewer returned a valid patch that changed none of the proposal."""


def _claim_repair_issues(issues, hypothesis_index: int):
    """Return only the validation issues relevant to one hypothesis.

    Validation issues retain their field declarations as well as their string
    codes. Keep indexed issues for other hypotheses out of this patch's scope;
    unindexed issues describe interpretation-wide constraints and still apply.
    """
    relevant = []
    for issue in issues:
        match = re.match(r"hypothesis\[(\d+)\]\.", str(issue))
        if match and int(match.group(1)) != hypothesis_index:
            continue
        relevant.append(issue)
    return relevant


def _support_repair_values(issues) -> dict[str, frozenset[str]]:
    """Map evidence-only issues to claim values whose support may be repaired."""
    values: dict[str, set[str]] = {}
    for issue in issues:
        code = re.sub(r"^hypothesis\[\d+\]\.", "", str(issue))
        kind, separator, evidence = code.partition(":")
        if not separator or kind not in {"ungrounded_evidence", "missing_evidence"}:
            continue
        dimension, separator, value = evidence.partition("=")
        field = FIELD_BY_DIMENSION.get(dimension)
        if separator and value and field:
            values.setdefault(field, set()).add(value)
    return {field: frozenset(items) for field, items in values.items()}


def invoke_claim_interpreter(
    context, state, user_task, usage, *, serialize, schema_errors
):
    warnings = list(state.get("budget_warnings", []))
    proposal = None
    valid = None
    issues = ()
    error = None
    # A stated patient-clustering terminal goal deterministically requires
    # sample_cluster_assignment. Only if that artifact is selected may its
    # single legal granularity be restored from ontology; a different artifact
    # (such as TF activity) is never aligned by this rule.
    artifact_alignment_targets = (
        frozenset({"sample_cluster_assignment"})
        if patient_clustering_goal(user_task)
        else frozenset()
    )
    tags = {
        tag
        for spec in context.project_policy.workflows.values()
        for tag in spec.output_capability.selection_tags
    }
    for attempt in range(2):
        patching = attempt == 1 and isinstance(proposal, SemanticClaims)
        schema = SemanticClaimRepair if patching else SemanticClaims
        adapter = (
            context.semantic_patcher
            if patching
            else (
                context.semantic_interpreter
                if attempt == 0
                else context.semantic_reviewer
            )
        )
        role = "semantic_interpreter" if attempt == 0 else "semantic_reviewer"
        messages = claim_messages(
            user_task, proposal, issues, patching=patching, selection_tags=tags
        )
        input_text = serialize(messages, schema)
        budget, warnings = preflight_budget(
            context,
            {**state, "token_usage": usage.model_dump(), "budget_warnings": warnings},
            role=role,
            model=context.semantic_model_name,
            input_text=input_text,
            reserved_output_tokens=context.router_max_tokens,
            allow_reserve=False,
        )
        if budget.status == "blocked":
            usage.budget_exhausted = True
            return valid, usage, warnings, error, frozenset()
        started = time.monotonic_ns()
        raw = None
        output = ""
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
        try:
            payload, raw = semantic_payload(adapter.invoke(messages))
            payload, advice_normalizations = normalize_advice_operation_evidence(
                payload,
                user_task,
                proposal_request_mode=(
                    proposal.request_mode
                    if isinstance(proposal, SemanticClaims)
                    else "unknown"
                ),
            )
            if advice_normalizations:
                record_event(
                    context,
                    state,
                    "routing.semantic_evidence_normalized",
                    "classify",
                    {
                        "attempt": attempt + 1,
                        "contract": "claims",
                        "normalizations": advice_normalizations,
                    },
                )
            if attempt == 0:
                proposal = payload
            decoded = schema.model_validate(payload)
            output = decoded.model_dump_json()
            if patching:
                repair_issues = _claim_repair_issues(
                    issues, decoded.hypothesis_index
                )
                licensed = permitted_fields(repair_issues)
                support_targets = _support_repair_values(repair_issues)
                claims = decoded.apply(
                    proposal,
                    permitted_fields=licensed,
                    support_repair_values=support_targets,
                )
                if claims == proposal:
                    raise _NoOpClaimRepair(
                        "semantic_repair:no_changes"
                    )
                requested_fields = set(
                    decoded.outcome.model_dump(exclude_none=True)
                )
                updated_outcome = claims.outcome_hypotheses[
                    decoded.hypothesis_index
                ].outcome
                original_outcome = proposal.outcome_hypotheses[
                    decoded.hypothesis_index
                ].outcome
                updated_support_fields = {
                    field for field in support_targets
                    if getattr(updated_outcome, field) != getattr(original_outcome, field)
                }
                ignored_fields = requested_fields - licensed - updated_support_fields
                ignored_fields.update(
                    field for field in ("request_mode", "semantic_goal")
                    if getattr(decoded, field) is not None
                )
                record_event(
                    context,
                    state,
                    "routing.semantic_patch_applied",
                    "classify",
                    {
                        "attempt": attempt + 1,
                        # Kept as a one-item list so reports written before
                        # the single-index shape still read the same way.
                        "repairs": [
                            {
                                "hypothesis_index": decoded.hypothesis_index,
                                "changed_fields": sorted(
                                    (requested_fields & licensed) | updated_support_fields
                                ),
                                "permitted_fields": sorted(licensed),
                                "support_fields": sorted(updated_support_fields),
                                "ignored_fields": sorted(ignored_fields),
                            }
                        ],
                    },
                )
            else:
                claims = decoded
            if attempt == 0:
                proposal = claims
            interpretation = claims.to_internal()
            interpretation, restorations = restore_stated_fields(
                user_task, interpretation,
                align_artifact_constraints_for=artifact_alignment_targets,
                restore_explicit_scalar_evidence=True,
            )
            if restorations:
                record_event(
                    context,
                    state,
                    "routing.outcome_input_restored",
                    "classify",
                    {"attempt": attempt + 1, "restored": restorations},
                )
            previous_mode = interpretation.request_mode
            reconciled_mode = reconcile_request_mode(user_task, previous_mode)
            if reconciled_mode != previous_mode:
                interpretation = interpretation.model_copy(
                    update={"request_mode": reconciled_mode}
                )
                record_event(
                    context,
                    state,
                    "routing.request_mode_reconciled",
                    "classify",
                    {
                        "previous_mode": previous_mode,
                        "request_mode": reconciled_mode,
                        "reason": "deterministic_request_mode_reconciliation",
                    },
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
                user_task, interpretation.outcome_hypotheses
            )
            if not validation.valid:
                issues = validation.issues
                record_event(
                    context,
                    state,
                    "routing.semantic_interpretation_rejected",
                    "classify",
                    {
                        "attempt": attempt + 1,
                        "issues": list(issues),
                        "evidence_shapes": list(validation.evidence_shapes),
                        "evidence_census": list(
                            evidence_census(interpretation.outcome_hypotheses)
                        ),
                    },
                )
                raise ValueError("Semantic claims failed evidence validation")
        except Exception as exc:
            if _is_fatal_exception(exc):
                raise
            error = exc
            schema_issues = schema_errors(exc)
            if schema_issues:
                issues = tuple(
                    "schema_validation:" + ".".join(x["location"]) + ":" + x["type"]
                    for x in schema_issues
                )
            elif not issues:
                issues = (
                    "semantic_structure:response could not be decoded or applied",
                )
            duration = max(0, (time.monotonic_ns() - started) // 1_000_000)
            usage = append_llm_usage(
                usage,
                role=role,
                model=context.semantic_model_name,
                response=raw,
                input_text=input_text,
                output_text=output,
                budget_tokens=context.task_token_budget,
                duration_ms=duration,
                status="failed",
                price_catalog=context.price_catalog,
            )
            record_event(
                context,
                state,
                "routing.semantic_interpreter_failed",
                "classify",
                {
                    "attempt": attempt + 1,
                    "error_type": type(exc).__name__,
                    "validation_issues": list(issues),
                },
            )
            if attempt == 0:
                # Even a decoding failure with no payload gets a schema repair call.
                if proposal is None:
                    proposal = {}
                record_event(
                    context,
                    state,
                    "routing.semantic_interpretation_retried",
                    "classify",
                    {"issues": list(issues)},
                )
                continue
            if valid is not None:
                record_event(
                    context,
                    state,
                    "routing.semantic_review_discarded",
                    "classify",
                    {
                        "attempt": 2,
                        "issues": list(issues),
                        "reason": (
                            "no_material_changes"
                            if isinstance(exc, _NoOpClaimRepair)
                            else "repair_failed_validation"
                        ),
                    },
                )
            return (
                valid,
                usage,
                warnings,
                None if valid is not None else error,
                frozenset(),
            )
        duration = max(0, (time.monotonic_ns() - started) // 1_000_000)
        usage = append_llm_usage(
            usage,
            role=role,
            model=context.semantic_model_name,
            response=raw,
            input_text=input_text,
            output_text=output,
            budget_tokens=context.task_token_budget,
            duration_ms=duration,
            price_catalog=context.price_catalog,
        )
        match = match_semantic_request(
            user_task,
            interpretation.outcome_hypotheses,
            request_mode=interpretation.request_mode,
        )
        if match.status == "ambiguous" and len(interpretation.outcome_hypotheses) == 1:
            candidate_tags = {
                tag
                for action in match.hypothesis_actions
                for tag in context.project_policy.workflows[action].output_capability.selection_tags
            }
            recovered = _recover_explicit_selection_tag(user_task, candidate_tags)
            if recovered is not None:
                recovered_tag, recovered_evidence = recovered
                hypothesis = interpretation.outcome_hypotheses[0]
                outcome = hypothesis.outcome.model_copy(update={
                    "selection_tags": sorted(
                        set(hypothesis.outcome.selection_tags) | {recovered_tag}
                    )
                })
                interpretation = interpretation.model_copy(update={
                    "outcome_hypotheses": [hypothesis.model_copy(update={
                        "outcome": outcome,
                        "evidence": [*hypothesis.evidence, recovered_evidence],
                    })]
                })
                match = match_semantic_request(
                    user_task,
                    interpretation.outcome_hypotheses,
                    request_mode=interpretation.request_mode,
                )
                record_event(
                    context,
                    state,
                    "routing.semantic_discriminator_recovered",
                    "classify",
                    {
                        "selection_tags": sorted(outcome.selection_tags),
                        "evidence": recovered_evidence.model_dump(mode="json"),
                        "candidate_actions": list(match.hypothesis_actions),
                        "contract": "claims",
                    },
                )
        valid = interpretation
        hypotheses = interpretation.outcome_hypotheses
        guided_complete = False
        if (
            interpretation.request_mode == "guidance"
            and match.status == "exact"
            and len(match.matched_actions) == 1
        ):
            capability = OUTPUT_CAPABILITIES[match.matched_actions[0]]
            guided_complete = all(
                _complete_guidance_match(hypothesis.outcome, capability)
                for hypothesis in hypotheses
            )
        granularity_clarification_complete = (
            interpretation.request_mode == "guidance"
            and match.status == "ambiguous"
            and bool(match.clarification_question)
            and len(match.hypothesis_actions) > 1
            and has_complete_open_granularity_alternatives(
                user_task, hypotheses
            )
        )
        semantic_complete = (
            match.status == "not_applicable"
            and len(hypotheses) == 1
        ) or (
            match.status == "exact"
            and len(match.matched_actions) == 1
            and (
                guided_complete
                if interpretation.request_mode == "guidance"
                else len(hypotheses) == 1
                and hypotheses[0].outcome.operation != "unknown"
            )
        ) or granularity_clarification_complete
        complete = (
            (
                match.status in {"exact", "not_applicable"}
                or granularity_clarification_complete
            )
            and interpretation.request_mode != "unknown"
            and bool(hypotheses)
            and all(not item.outcome.unresolved_dimensions for item in hypotheses)
            and semantic_complete
            and getattr(context, "review_policy", "when_needed") == "when_needed"
        )
        event = (
            "routing.semantic_interpretation_accepted"
            if complete or attempt == 1
            else "routing.semantic_interpretation_proposed"
        )
        record_event(
            context,
            state,
            event,
            "classify",
            {
                "attempt": attempt + 1,
                "hypothesis_count": len(interpretation.outcome_hypotheses),
                "registry_match_status": match.status,
                "evidence_census": list(
                    evidence_census(interpretation.outcome_hypotheses)
                ),
            },
        )
        if complete or attempt == 1:
            _trace(
                "router",
                "Semantic interpretation completed",
                {
                    "kind": "router_activity",
                    "operation": "semantic_interpreter",
                    "status": "completed",
                    "duration_ms": duration,
                    "attempt": attempt + 1,
                },
            )
            return valid, usage, warnings, None, frozenset()
        issues = (
            f"semantic_completeness:match={match.status}; recheck the original goal, "
            "current inputs, roles, and unresolved dimensions. Preserve real uncertainty; "
            "do not invent facts to fit a tool.",
        )
    return valid, usage, warnings, error, frozenset()
