"""Semantic → evidence → registry → intent routing pipeline."""

from __future__ import annotations

from dataclasses import replace

from ..contracts import AgentState, LLMUsage, TaskDecision, _trace
from ..contracts.outcomes import CapabilityMatch
from ..interpretation.assembly import assemble_task_decision
from ..interpretation.hydration import hydrate_router_decision
from ..interpretation.outcome_validation import validate_outcome_hypotheses
from ..interpretation.provider_fallback import (
    deterministic_router_fallback,
    recover_ambiguous_input,
    recover_explicit_run,
    recover_registry_guidance,
)
from ..interpretation.semantic_goal import outcome_routing_state
from ..interpretation.unverified_evidence import UNVERIFIED_BASIS, bounded_match
from ..routing.capability import (
    apply_input_preflight_intent,
    has_direct_retrieval_request,
    reconcile_request_mode,
)
from ..routing.named_labels import named_registered_action
from ..routing.outcome_matching import match_semantic_request
from .context import _GraphContext, record_event
from .continuation_invocation import compare_workflows, continue_workflow
from .intent_invocation import _invoke_intent_router
from .invocation_types import RouterInvocation as _RouterInvocation
from .condition_recommender import invoke_condition_recommender
from .request_concerns import invoke_concern_matcher
from .hypothesis_bases import (
    ADVISORY_ROLES, explicit_research_choice, framing_yielded, invoke_hypothesis_matcher,
)
from .input_inspection import invoke_input_inspection
from ..routing.reading_selection import drop_input_only_readings, drop_unwitnessed_readings, matchable_readings
from ..routing.scale_relaxation import drop_unnamed_scale, note_unstated_scale, relax_unstated_scale
from ..string_download import continued_string_download_decision, string_download_decision
from .discriminator import invoke_semantic_discriminator as _invoke_semantic_discriminator
from .semantic_attempts import invoke_semantic_interpreter as _invoke_semantic_interpreter
# Re-exported for callers and tests that imported them from here before the
# attempt loop moved to `semantic_attempts` (Log 190).
from .discriminator import discriminator_context as _discriminator_context  # noqa: F401
from .semantic_attempts import MAX_SEMANTIC_ATTEMPTS  # noqa: F401
from .semantic_review_validation import _as_semantic_patch  # noqa: F401
from .structured_calls import _validation_issue_types  # noqa: F401

__all__: list[str] = []


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


def invoke_router(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
) -> _RouterInvocation:
    """Route, then keep an unstated scale out of the reply on every path (Log 281)."""
    result = _route_request(context, state, user_task)
    decision = note_unstated_scale(user_task, result.decision)
    if decision is result.decision:
        return result
    record_event(context, state, "routing.unstated_scale_noted", "classify", {
        "granularity": result.decision.requested_outcome.granularity,
        "candidate_actions": list(decision.matched_actions or decision.hypothesis_actions),
    })
    return replace(result, decision=decision, routing_state={
        **result.routing_state,
        "requested_outcome": decision.requested_outcome.model_dump(),
        "outcome_hypotheses": [item.model_dump() for item in decision.outcome_hypotheses],
    })


def _route_request(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
) -> _RouterInvocation:
    """Run the ordered semantic, validation, registry, and intent pipeline."""
    usage = _current_usage(context, state)
    if state.get("method_comparison") is not None and (
        compared := compare_workflows(context, state, user_task, usage)
    ) is not None:
        return compared
    if state.get("workflow_continuation") is not None:
        return continue_workflow(context, state, user_task, usage)
    if continued := continued_string_download_decision(user_task):
        return _RouterInvocation(
            decision=continued, routing_state=outcome_routing_state(continued),
            usage=usage, budget_warnings=[], reason_code="string_download_continuation",
        )
    # A question explicitly contrasting biological hypotheses is a comparison
    # first. Do not spend the outcome-repair budget collapsing it to one result.
    if explicit_research_choice(user_task):
        draft = TaskDecision(
            action="no_tool", in_scope=True, should_execute=False,
            intent_type="answer_question", confidence=0.0,
            reason="Compare the stated research hypotheses before choosing a workflow.",
        )
        draft, usage, warnings = invoke_hypothesis_matcher(
            context, state, user_task, draft, usage, [],
        )
        if draft.stated_hypotheses:
            actions = list(dict.fromkeys(h.basis for h in draft.stated_hypotheses
                                         if h.basis != "unsupported"))
            comparison = len(actions) >= 2
            record_event(context, state, ("routing.research_choices_accepted" if comparison
                                          else "routing.research_guidance_accepted"), "classify", {
                "hypotheses": [h.model_dump() for h in draft.stated_hypotheses],
                "actions": actions,
            })
            return _RouterInvocation(
                decision=draft, routing_state=outcome_routing_state(draft, request_mode="guidance"),
                usage=usage, budget_warnings=warnings, reason_code=("research_choices" if comparison else "research_guidance"),
            )
        if (not any(c.role == "hypothesis_bases" for c in usage.calls)
                or usage.budget_exhausted or draft.match_basis == "unverified_evidence"
                or any(c.role == "hypothesis_bases" and c.status == "failed" for c in usage.calls)):
            # Failed interpretation must not silently revert to selecting one
            # tool for a question that explicitly asks to compare hypotheses.
            draft = draft.model_copy(update={
                "match_basis": "provider_unavailable",
                "reason": "The research comparison could not be validated; no workflow was selected.",
            })
            return _RouterInvocation(
                decision=draft, routing_state=outcome_routing_state(draft, request_mode="guidance"),
                usage=usage, budget_warnings=warnings, reason_code="research_choices_unavailable",
            )
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

    if string_decision := string_download_decision(user_task, interpretation):
        record_event(context, state, "routing.string_acquisition_selected", "classify", {
            "species": string_decision.taxon,
            "network_type": string_decision.string_network_type,
        })
        return _RouterInvocation(
            decision=string_decision,
            routing_state=outcome_routing_state(string_decision, interpretation.semantic_goal, interpretation.request_mode),
            usage=usage, budget_warnings=budget_warnings,
            reason_code="string_acquisition",
        )

    _trace(
        "reasoning",
        "Checking registered workflow capabilities",
        {"kind": "registry_activity", "status": "started"},
    )
    interpretation, dropped = drop_input_only_readings(user_task, interpretation)
    if dropped:
        record_event(context, state, "routing.input_only_readings_dropped", "classify", {"artifact_types": dropped})
    interpretation, unwitnessed = drop_unwitnessed_readings(user_task, interpretation)
    if unwitnessed:
        record_event(context, state, "routing.unwitnessed_readings_dropped", "classify", {"artifact_types": unwitnessed})
    interpretation, unnamed = drop_unnamed_scale(user_task, interpretation)
    if unnamed:
        record_event(context, state, "routing.unnamed_scale_dropped", "classify", {"readings": unnamed})
    capability_match = match_semantic_request(
        user_task,
        matchable_readings(user_task, interpretation.outcome_hypotheses),
        request_mode=interpretation.request_mode,
        ignore_tags=restored_tags,
    )
    relaxed, capability_match = relax_unstated_scale(
        user_task, interpretation, capability_match, scale_dropped=bool(unnamed),
    )
    if relaxed is not interpretation:
        record_event(context, state, "routing.unstated_scale_relaxed", "classify", {
            "granularity": interpretation.outcome_hypotheses[0].outcome.granularity,
            "candidate_actions": list(capability_match.hypothesis_actions),
        })
        interpretation = relaxed
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
        and not validate_outcome_hypotheses(
            user_task, interpretation.outcome_hypotheses, interpretation.request_mode,
        ).valid
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
    # Preserve research alternatives before ranking methods by study facts.
    # The goal review (hypotheses) and the method stage (conditions) resolve
    # different ambiguities: a review that validated no comparison yields to
    # the conditions call (Log 257). Practical-concern extraction shares the
    # review's call. A comparison suppresses file-driven selection; clear-goal
    # input inspection and execution gates remain intact.
    decision, usage, budget_warnings = invoke_hypothesis_matcher(
        context, state, user_task, decision, usage, budget_warnings,
    )
    if framing_yielded(decision, usage) and not any(
        call.role in ADVISORY_ROLES - {"hypothesis_bases"} for call in usage.calls
    ):
        decision, usage, budget_warnings = invoke_condition_recommender(
            context, state, user_task, decision, usage, budget_warnings,
        )
    if not decision.stated_hypotheses:
        decision = invoke_input_inspection(context, state, user_task, decision)
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
    decision, usage, budget_warnings = invoke_concern_matcher(
        context, state, user_task, decision, usage, budget_warnings,
    )
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
