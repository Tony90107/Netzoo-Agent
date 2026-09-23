"""Bounded semantic inference with atomic claims and conditional repair."""

import time
from ..contracts import _trace
from ..contracts.semantic_claims import SemanticClaims, SemanticClaimRepair
from ..interpretation.claim_prompt import claim_messages
from ..interpretation.outcome_validation import (
    validate_outcome_hypotheses,
    evidence_census,
)
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..interpretation.stated_field_restoration import restore_stated_fields
from ..llm import append_llm_usage
from ..routing.outcome_matching import match_semantic_request
from .context import preflight_budget, record_event
from .discriminator import _recover_explicit_selection_tag


class _NoOpClaimRepair(ValueError):
    """A reviewer returned a valid patch that changed none of the proposal."""


def invoke_claim_interpreter(
    context, state, user_task, usage, *, serialize, schema_errors
):
    warnings = list(state.get("budget_warnings", []))
    proposal = None
    valid = None
    issues = ()
    error = None
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
            if attempt == 0:
                proposal = payload
            decoded = schema.model_validate(payload)
            output = decoded.model_dump_json()
            if patching:
                claims = decoded.apply(proposal)
                if claims == proposal:
                    raise _NoOpClaimRepair(
                        "semantic_repair:no_changes"
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
                                    decoded.outcome.model_dump(exclude_none=True)
                                ),
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
        complete = (
            match.status in {"exact", "not_applicable"}
            and interpretation.request_mode != "unknown"
            and len(interpretation.outcome_hypotheses) == 1
            and not interpretation.outcome_hypotheses[0].outcome.unresolved_dimensions
            and (
                match.status == "not_applicable"
                or (
                    len(match.matched_actions) == 1
                    and interpretation.outcome_hypotheses[0].outcome.operation
                    != "unknown"
                )
            )
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
