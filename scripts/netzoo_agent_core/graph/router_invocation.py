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
from .fact_check_call import apply_fact_check, fact_model
from .goal_read_call import apply_goal_read
from .required_check_budget import required_fact_check_reserve
from ..interpretation.ruled_out import without_ruled_out, without_unbuilt_network
from .continuation_invocation import compare_workflows, continue_workflow
from .intent_invocation import _invoke_intent_router
from .invocation_types import RouterInvocation as _RouterInvocation
from .condition_recommender import invoke_condition_recommender, unrecommended_question
from .request_concerns import invoke_concern_matcher
from .study_purpose_call import invoke_study_purpose
from .capability_check_call import (
    has_check_model, request_capability_check, request_capability_reread, request_condition_check,
    request_second_opinion,
)
from ..capability_sheet import entry
from ..contracts.capability_check import CapabilityCheck, reread_as_proposal
from ..interpretation.checked_match import _USER_CHOSEN, checked_match, credited_workflows
from ..routing.capability import validate_task_text
from workflow_registry import ACTION_DEFINITIONS, RUN_ACTIONS
from ..interpretation.reread import merge_reread, reread_passages
from ..interpretation.unmapped_routes import is_unmapped, without_unmapped_candidates
from ..interpretation.capability_check import (
    apply_condition_answers, apply_redirect_answers, apply_second_opinion, blank_requirement_pairs,
    build_capability_check, condition_pairs, implied_actions, redirect_pairs, second_opinion_pairs, stated_requirements,
    wait_on_asked, workflow_description,
)
from ..interpretation.method_conditions import unbound_settings, verified_controls
from ..interpretation.input_bindings import bound_expression_samples
from ..interpretation.request_facts import run_fact_bindings
from ..interpretation.requirement_split import apply_own_sentence_answers
from .data_facts_call import invoke_data_facts
from ..interpretation.run_check import run_check_verdict, run_verdict
from ..interpretation.run_hold import hold_run
from ..contracts.capability_check import APPROVING_RUN_VERDICTS
from ..routing.named_labels import named_workflow_action
from ..interpretation.needed_facts import waiting_decision
from ..interpretation.applicability import assess_applicability, merge_inputs, needs_data_facts
from ..interpretation.data_plan import KIND_FIELDS, build_data_plan, plan_for_verdict, plan_needs, plan_with_unknowns
from ..interpretation.request_requirements import stated_in_text
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
    """Route, then keep an unstated scale out of the reply on every path (Log 281).

    Log 355: a new request's study purpose is read once, after routing; a
    follow-up turn (a continuation, a method comparison, a choice) is not a
    new purpose, so it carries none and the reply reads its own words.
    """
    continuation = state.get("workflow_continuation")
    # M2: a continuation the user changed is read as a new run request is -- checked, then planned or held.
    follow_up = (state.get("method_comparison") is not None
                 or (continuation is not None and not continuation.get("recheck")))
    result = _route_request(context, state, user_task)
    if follow_up or result.reason_code == "string_download_continuation":
        result = replace(result, routing_state={**result.routing_state, "study_purpose": None})
    else:
        proposal, check_status = None, "no_model"
        if result.decision.action != "download_string":
            # Log 387: the safety check is asked before the advisory reads; verdict layer step 1: a run too.
            proposal, usage, warnings, check_status = request_capability_check(
                context, state, user_task, result.usage, result.budget_warnings)
            result = replace(result, usage=usage, budget_warnings=warnings)
        advisory_state = dict(state, required_check_reserve=required_fact_check_reserve(
            context, user_task, result.decision, proposal, fact_llm=fact_model(context)[1]))
        purpose, usage, warnings = invoke_study_purpose(
            context, advisory_state, user_task, result.usage, result.budget_warnings,
        )
        result = replace(result, usage=usage, budget_warnings=warnings,
                         routing_state={**result.routing_state, "study_purpose": purpose})
        result = _with_applicability(context, advisory_state, user_task, result)
        result = _with_capability_check(context, state, user_task, result, proposal,
                                        provisional=check_status == "fallback")
        result = _with_run_check(context, state, user_task, result, proposal, check_status)
        if check_status in ("blocked", "failed") and result.decision.action == "no_tool":
            # Log 394: a turn the check could not read says so, rather than answering as if it had.
            result = replace(result, decision=result.decision.model_copy(
                update={"capability_check": CapabilityCheck(unavailable=True)}))
        if not _held(result.decision) and (
                unmapped := without_unmapped_candidates(result.decision)) is not result.decision:
            # Log 403 part D: an `unknown` reading tied every workflow; it claims none of them.
            record_event(context, state, "routing.unmapped_candidates_cleared", "classify", {
                "cleared": list(dict.fromkeys([*result.decision.matched_actions, *result.decision.hypothesis_actions,
                                               *result.decision.recommended_actions]))})
            result = replace(result, decision=unmapped)
        result = _with_checked_match(context, state, result)
        result = _with_requested_run(context, state, user_task, result)
        result = _with_verdict_plan(context, state, result)
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


def _with_applicability(context, state, user_task: str, result: _RouterInvocation) -> _RouterInvocation:
    """Plan items 4-5 (Logs 380, 383): the turn's data-needs plan, and each listed workflow judged by it.

    What the question needs is read from the question (`plan_needs`), not
    inferred from the workflows routing listed; the data-facts call reads what
    the request has whenever the question or a listed workflow needs TF priors
    or miRNA data the request does not bind as files. The plan and the
    per-workflow judgement go on the decision for every renderer; no workflow is
    selected, ranked or removed here.
    """
    decision = result.decision
    if decision.action != "no_tool":
        return result
    listed = [*decision.matched_actions, *decision.hypothesis_actions, *decision.recommended_actions]
    claims = (result.routing_state.get("study_purpose") or {}).get("claims") or ()
    answerable, _basis, kinds = plan_needs(claims, decision, user_task)
    bound = set(stated_in_text(user_task))
    question_reads = answerable and any(not set(KIND_FIELDS[kind]) <= bound for kind in kinds)
    facts, usage, warnings = None, result.usage, result.budget_warnings
    if question_reads or needs_data_facts(listed, bound):
        facts, usage, warnings = invoke_data_facts(context, state, user_task, usage, warnings)
    words = _stated_artifacts(user_task, decision)
    plan = build_data_plan(claims, decision, facts, words, user_task, bound)
    update = {"data_plan": plan}
    dropped = None
    if facts is not None:
        present = merge_inputs(words, facts)
        advice = decision.advisory_recommendation
        listed_with_advice = [*listed, *([advice.action] if advice is not None else [])]
        update["data_facts"] = {key: str(value) for key, value in facts.items()}
        update["applicability"] = assess_applicability(listed_with_advice, present, user_task)
        status = {item.action: item.status for item in update["applicability"]}
        if advice is not None and status.get(advice.action) == "not_applicable":
            # A recommendation needing data the request rules out is not one (plan item 4);
            # the tie keeps a question of its own, never the dropped one's.
            dropped = advice.action
    decision = decision.model_copy(update=update)
    if dropped is not None:
        decision = decision.model_copy(update={
            "advisory_recommendation": None, "clarification_question": unrecommended_question(decision)})
    record_event(context, state, "routing.data_plan_built", "classify", {
        "data_plan": plan.model_dump(),
        "data_facts": decision.data_facts,
        "applicability": [item.model_dump() for item in decision.applicability],
        "recommendation_dropped": dropped,
    })
    return replace(result, decision=decision, usage=usage, budget_warnings=warnings,
                   routing_state={**result.routing_state, "data_facts": decision.data_facts})


def _with_checked_match(context, state, result: _RouterInvocation) -> _RouterInvocation:
    """Logs 405, 409: the confirmed check credited one workflow for every result a workflow gives, and routing
    made no claim or claimed only other workflows -- that workflow is the match, so the reply, the card and
    the next step read the same verdict."""
    policy = getattr(context, "project_policy", None)
    if (policy is None or _held(result.decision)
            or (matched := checked_match(result.decision, policy.workflows)) is result.decision):
        return result
    record_event(context, state, "routing.check_match_adopted", "classify", {
        "action": matched.matched_actions[0], "routing_status": result.decision.capability_match_status,
        "routing_basis": result.decision.match_basis,
        "routing_actions": list(dict.fromkeys([*result.decision.matched_actions, *result.decision.recommended_actions]))})
    goal = outcome_routing_state(matched)["semantic_goal"]
    return replace(result, decision=matched, routing_state={
        **result.routing_state,
        "semantic_goal": {**(result.routing_state.get("semantic_goal") or {}),
                          **{key: goal[key] for key in ("candidates", "relationship", "match_status", "match_basis")}}})


def _with_verdict_plan(context, state, result: _RouterInvocation) -> _RouterInvocation:
    """Verdict layer: the data-needs plan, when read from routing's reading, follows the final verdict (F46)."""
    decision = result.decision
    plan = plan_with_unknowns(plan_for_verdict(decision.data_plan, decision), decision)
    if plan is decision.data_plan:
        return result
    before = decision.data_plan.needs if decision.data_plan is not None else []
    record_event(context, state, "routing.data_plan_followed_verdict", "classify", {
        "dropped": [need.kind for need in before if need not in plan.needs],
        "added": [need.kind for need in plan.needs if need not in before]})
    return replace(result, decision=decision.model_copy(update={"data_plan": plan}))


def _with_requested_run(context, state, user_task: str, result: _RouterInvocation) -> _RouterInvocation:
    """Verdict layer step 1: a run both routing readings asked for, of the one workflow the final verdict credits.

    The run was decided before the capability check, from routing's match and the task text alone. r17 (run17, 32
    sessions of supported run commands): 23 were answered as guidance -- the text gate wanted the workflow's name or
    a verb from its list ("Compute now: ... produce ..." -> BONOBO, DRAGON, SAMBAR), or routing fell back and the check
    credited one workflow only afterwards (PI1 PUMA, PL5 LIONESS-DRAGON, PL7 COBRA).

    Three readings must agree: the intent router and the semantic interpreter asked for execution
    (`execution_requested`), and the confirmed check read every result as asked to be produced (`asked_as`
    request, not a question about which method gives it) and credits this one workflow, which routing matched or
    the check adopted. Every result must be one the workflow gives directly: a result nothing registered gives, or one
    needing a step outside NetZoo, keeps the turn a reply that says so (r17 MX1: an upload beside the networks; NM14:
    a significance test of differential co-expression after LIONESS-COEXPRESSION). The request's own operation bans still veto it afterwards (`graph.operation_authority`).
    """
    decision = result.decision
    check = decision.capability_check
    if (decision.action != "no_tool" or not decision.execution_requested or _held(decision)
            or check is None or check.unconfirmed() or check.full_gap or check.unchecked
            or not check.results() or any(item.asked_as != "request" or item.status != "available"
                                          for item in check.results())):
        return result
    credited = credited_workflows(check) or []
    if len(credited) != 1 or credited[0] not in RUN_ACTIONS or decision.matched_actions != credited:
        return result
    action = credited[0]
    if validate_task_text(user_task, action, matched_actions=decision.matched_actions,
                          model_execution=True) is not None:
        return result
    run = hydrate_router_decision(decision.model_copy(update={
        "action": action, "should_execute": True, "intent_type": "run_analysis",
        "reason": "Run requested; the capability check credited this workflow for what the request asks for."}),
        user_task)
    # ROUND-06 (h3 L15; C40 p1/p2): this path planned the run without the check's settings -- ".csv" read, ".h5" run.
    bound, controls, set_by_request = _bind_run_settings(context, state, run, action, check)
    verdict = run_verdict(bound, action, named=named_workflow_action(user_task) == action)
    approved = verdict.verdict in APPROVING_RUN_VERDICTS
    _record_run_bindings(context, state, bound, action, set_by_request, approved, controls)
    if not approved:  # a setting the run cannot carry: held and offered, as `_on_run_verdict` does
        held = hold_run(decision.model_copy(update={"capability_check": bound, "run_verdict": verdict}), verdict)
        record_event(context, state, "routing.run_held", "classify", {
            "action": action, "verdict": verdict.verdict, "named": verdict.named,
            "offered": held.recommended_actions, "check_status": "ok"})
        return replace(result, decision=held, routing_state={**result.routing_state, **outcome_routing_state(held)})
    record_event(context, state, "routing.requested_run_adopted", "classify", {"action": action})
    return replace(result, decision=run.model_copy(update={"capability_check": bound, "run_verdict": verdict, **controls}))


def _with_run_check(context, state, user_task: str, result: _RouterInvocation, proposal,
                    check_status: str) -> _RouterInvocation:
    """Verdict layer step 1: the guidance turn's whole check (re-read, condition check, second opinion) on the run
    routing selected. Its verdict is recorded; a confirmed full gap -- nothing registered gives any result the run
    asks for -- is answered as one, and the run is not planned. Every other verdict leaves the run as it was.

    r17/r17b (run17): the live run path planned 8 runs nothing registered gives (causal direction -> GIRAFFE,
    methylation subtypes -> SAMBAR, gene embeddings -> PANDA); the check found all 8 a gap and, with the second
    opinion, judged none of 9 correct runs one (r17 PQ3-2 had been, on the first reading alone).
    """
    if result.decision.action in ("no_tool", "download_string"):
        return result
    if proposal is None:
        _record_shadow(context, state, result.decision, None, check_status)
        return _on_run_verdict(context, state, user_task, result, None, check_status)
    return _with_capability_check(context, state, user_task, result, proposal,
                                  provisional=check_status == "fallback", shadow_status=check_status)


def _control_default(action: str, name: str):
    return next((control.default for control in ACTION_DEFINITIONS[action].controls if control.name == name), None)


def _bind_run_settings(context, state, decision, action: str, check):
    """ROUND-06: the one binding of the check's settings to a run, for every path that plans one.

    Returns the check with each stated setting the run cannot carry left unread (so the verdict holds the run), the
    controls the check verified, and which controls the request already set as name=value. Until ROUND-06 only
    `_on_run_verdict` bound them; a run adopted on a guidance turn (`_with_requested_run`) went ahead with defaults.
    """
    set_by_request = lambda name: getattr(decision, name, None) not in (  # noqa: E731
        None, _control_default(action, name))
    unbound = unbound_settings(check, action, set_by_request)
    if unbound:
        # M3 review: a setting the run cannot carry is not verified for it; the run waits, as for an unread sentence.
        record_event(context, state, "routing.run_settings_unbound", "classify", {"quotes": unbound})
        check = check.model_copy(update={"unchecked": list(dict.fromkeys([*check.unchecked, *unbound]))})
    # M2: the settings the check verified are the run's, unless the request set the control as name=value.
    controls = {name: value for name, value in verified_controls(check, action).items() if not set_by_request(name)}
    return check, controls, set_by_request


def _record_run_bindings(context, state, check, action: str, set_by_request, approved: bool, controls: dict) -> None:
    if bindings := run_fact_bindings(check, action, set_by_request, approved=approved):
        # ROUND-03: where each stated setting of the run's workflow went, by the fact it was read as.
        record_event(context, state, "routing.run_fact_bindings", "classify", {"bindings": bindings})
    if approved and controls:
        record_event(context, state, "routing.run_controls_bound", "classify", {"controls": controls})


def _held(decision) -> bool:
    return decision.run_verdict is not None and decision.run_verdict.held


def _on_run_verdict(context, state, user_task: str, result: _RouterInvocation, check,
                    check_status: str) -> _RouterInvocation:
    """Items 1-2 (2026-10-14): a run goes ahead only under a verdict that approves it.

    Since 3578b00 every verdict but a full gap left the run as routing chose it, so a run of a workflow the check
    credited nothing to (`other_workflow`), or of one giving only part of what was asked (`partial_gap`), was planned
    as if it gave everything (engineering review of 923e493). Now:
    - an approving verdict keeps the run and travels with it (`RunVerdict`, required by the Plan Evaluator);
    - when the check credits another workflow than one the user did not name, routing's claim is dropped and the
      guidance turn's own rules adopt the credited workflow and plan it as asked (`checked_match`,
      `_with_requested_run`), the same as for the same words asked on a guidance turn;
    - any other verdict, or a re-plan those rules do not make, holds the run: nothing is planned, the reply says why,
      and the run is offered for the user to confirm (`interpretation.run_hold`).
    """
    decision = result.decision
    named = decision.match_basis in _USER_CHOSEN or named_workflow_action(user_task) == decision.action
    if check is not None:
        check, controls, set_by_request = _bind_run_settings(context, state, decision, decision.action, check)
    else:
        controls, set_by_request = {}, (lambda name: False)
    verdict = run_verdict(check, decision.action, check_status=check_status, named=named)
    approved = verdict.verdict in APPROVING_RUN_VERDICTS
    _record_run_bindings(context, state, check, decision.action, set_by_request, approved, controls)
    if approved:
        return replace(result, decision=decision.model_copy(update={"capability_check": check, "run_verdict": verdict, **controls}))
    guidance = decision.model_copy(update={
        "action": "no_tool", "should_execute": False, "intent_type": "answer_question", "execution_requested": True,
        "capability_check": check if check is not None else CapabilityCheck(unavailable=True), "run_verdict": verdict,
    })
    policy = getattr(context, "project_policy", None)
    if verdict.verdict == "other_workflow" and not named and policy is not None:
        cleared = guidance.model_copy(update={
            "matched_actions": [], "hypothesis_actions": [], "recommended_actions": [], "alternative_actions": [],
            "advisory_recommendation": None, "clarification_question": None})
        replanned = _with_requested_run(context, state, user_task, replace(
            result, decision=checked_match(cleared, policy.workflows)))
        if replanned.decision.action != "no_tool":
            record_event(context, state, "routing.run_replanned", "classify", {
                "from": decision.action, "to": replanned.decision.action, "credited": verdict.credited})
            return replanned
    held = hold_run(guidance, verdict)
    record_event(context, state, "routing.run_held", "classify", {
        "action": decision.action, "verdict": verdict.verdict, "named": named,
        "offered": held.recommended_actions, "check_status": check_status})
    return replace(result, decision=held,
                   routing_state={**result.routing_state, **outcome_routing_state(held)})


def _record_shadow(context, state, decision, check, check_status: str) -> None:
    record_event(context, state, "routing.run_check_shadow", "classify", {
        "check_status": check_status, **run_check_verdict(check, decision.action),
        "match_status": decision.capability_match_status, "match_basis": decision.match_basis})


def _not_checked(check: CapabilityCheck, pairs) -> CapabilityCheck:
    """Review of 474a83c: a stated requirement the condition check could not answer (budget, provider) was never
    checked, and a run of SAMBAR beside "the clustering has to be k-means" kept `agrees`. Its words are now unread, as
    a sentence the check did not read: said as not checked, never a full gap, and a run is held (`unread`)."""
    quotes = [quote for _index, _action, _keys, quote in pairs]
    return check.model_copy(update={"unchecked": list(dict.fromkeys([*check.unchecked, *quotes])), "full_gap": False})


def _condition_shown(check, pairs) -> list[tuple[str, str, str, str]]:
    """(asked result, stated requirement, workflow, what it produces and needs) per condition-check pair."""
    return [(check.requirements[index].quote, quote, entry(keys[0]).workflow, workflow_description(keys))
            for index, _action, keys, quote in pairs]


def _with_capability_check(context, state, user_task: str, result: _RouterInvocation, proposal, *,
                           provisional: bool = False, shadow_status: str | None = None) -> _RouterInvocation:
    """Log 387: each thing a guidance request asks for, checked against the capability sheet.

    When every result it asks for is one no registered workflow produces, and
    every sentence was read, no workflow is offered as the answer: the routing
    candidates are cleared and the turn is marked unsupported, so no renderer,
    card or next step can present one (Log 385: 25 of 45 such requests were
    given a workflow). Otherwise the check only adds what was understood.
    """
    decision = result.decision
    # Verdict layer step 1: a run is checked only in shadow (`shadow_status`), and its decision is left as it is.
    if proposal is None or (decision.action != "no_tool") != (shadow_status is not None):
        return result
    # ROUND-20: with their words, so a registry-wide reason is said only for a result the claim's sentence holds.
    claims = {claim: quote for claim, quote in (result.routing_state.get("study_purpose") or {}).get("claims") or ()}
    counted = bound_expression_samples(user_task)  # ROUND-07 (G3): a sample-count doubt the named file answers
    check, rejected = build_capability_check(user_task, proposal, claims, counted)
    record_event(context, state, "routing.capability_checked", "classify", {
        "proposal": proposal.model_dump(), "rejected": rejected, "check": check.model_dump(),
    })
    usage, warnings = result.usage, result.budget_warnings
    passages = [] if provisional else reread_passages(user_task, decision.model_copy(update={"capability_check": check}))
    if passages:
        # Log 406: words the check left unread -- no result in the whole request while routing offered
        # workflows, or a long unquoted stretch beside a quoted result -- are read once more, asks only.
        reread, usage, warnings = request_capability_reread(context, state, user_task, passages, usage, warnings)
        if reread is not None:
            reread_check, unplaced = build_capability_check(
                user_task, reread_as_proposal(reread, getattr(proposal, "conditions", None)), claims, counted)
            check = merge_reread(user_task, check, reread_check, passages, unplaced)
        record_event(context, state, "routing.capability_reread", "classify", {
            "passages": passages, "reread": reread.model_dump() if reread is not None else None,
            "check": check.model_dump()})
    stated = [] if provisional else stated_requirements(user_task, proposal, check)
    own = [] if provisional else stated_requirements(user_task, proposal, check, own_sentence=True)
    pairs_to_check = condition_pairs(check, stated)
    own_pairs = condition_pairs(check, own)
    if pairs_to_check or own_pairs:
        # Log 414: a requirement the request states outside the asked result, of no typed kind, is checked against
        # each credited workflow; only a workflow found unable to meet it is removed -- nothing turns unconfirmed.
        # M2: one in the asking sentence is checked in the same call and, unmet, becomes a result of its own.
        answers, usage, warnings = request_condition_check(
            context, state, _condition_shown(check, pairs_to_check + own_pairs), usage, warnings)
        own_answers = answers[len(pairs_to_check):] if answers is not None else None
        answers = answers[:len(pairs_to_check)] if answers is not None else None
        check = (apply_condition_answers(check, pairs_to_check, answers) if answers is not None
                 else _not_checked(check, pairs_to_check))
        if own_answers is not None:
            check = apply_own_sentence_answers(check, own_pairs, own_answers)
        else:
            check = _not_checked(check, own_pairs)
        offered = [*decision.matched_actions, *decision.hypothesis_actions, *decision.recommended_actions]
        redirect = redirect_pairs(check, list(dict.fromkeys(offered))[:4]) if answers is not None else []
        redirected = None
        if redirect:
            redirected, usage, warnings = request_condition_check(
                context, state, _condition_shown(check, redirect), usage, warnings, redirect=True)
            if redirected is not None:
                check = apply_redirect_answers(check, redirect, redirected)
        record_event(context, state, "routing.capability_condition_check", "classify", {
            "stated": stated, "pairs": [[index, action, keys, quote] for index, action, keys, quote in pairs_to_check],
            "own_sentence": [[index, action, keys, quote] for index, action, keys, quote in own_pairs],
            "own_answers": own_answers,
            "answers": answers, "redirect": [[index, action, keys, quote] for index, action, keys, quote in redirect],
            "redirected": redirected, "full_gap": check.full_gap})
    exact = list(decision.matched_actions) if decision.capability_match_status == "exact" else []
    # Log 403: a routing tie is a claim too -- methods questions are now checked, and "which method
    # gives X" usually ties -- so a gap that would clear it asks about up to four of its workflows.
    # A reading routing left `unknown` ties every workflow and claims none (part D): nothing to ask.
    tied = [] if exact or is_unmapped(decision) else list(dict.fromkeys(decision.hypothesis_actions))[:4]
    cited = [entry(key).action for item in check.results() for key in item.not_by if entry(key).action]
    implied = [action for item in check.results() for action in implied_actions(item)]
    asked = list(dict.fromkeys([*exact, *tied, *cited, *implied]))
    # Log 404: a blank verdict beside results the check did find is asked about the workflows its
    # own attributes point to, as Log 397 asks for a whole-request gap (heldout11 VC4s-2).
    blank_pairs = [] if provisional or check.full_gap else blank_requirement_pairs(check)
    if (check.full_gap and asked) or blank_pairs:
        # Log 390: the two readers disagree -- routing matched a workflow exactly, the check found
        # nothing -- so the check is asked once more, pair by pair, about that workflow's results.
        # Log 396: also about every workflow whose near miss the check cited, so a gap stands
        # only after the workflows it weighed were asked as a whole (TEST_PROMPTS r12 test9:
        # routing failed and "infer a network" was refused over OTTER's convexity near miss).
        # Log 397: and about the workflows a blank verdict's own typed attributes point to.
        pairs = second_opinion_pairs(check, asked) if check.full_gap else blank_pairs
        shown = [(check.requirements[index].quote, entry(keys[0]).workflow, " ".join(entry(k).text for k in keys))
                 for index, _action, keys in pairs]
        answers = None
        if pairs:  # typed attributes may leave nothing to ask
            situation = (user_task,)  # A second opinion sees all context and constraints, not only the short result quote.
            answers, usage, warnings = request_second_opinion(context, state, shown, usage, warnings, situation)
        if answers is not None:
            # Verdict layer step 2: what the user said they do not know can decide among the workflows weighed here.
            check = wait_on_asked(apply_second_opinion(check, pairs, answers, user_task), pairs)
            late = [pair for pair in condition_pairs(check, stated) if check.requirements[pair[0]].second_opinion]
            late_own = [pair for pair in condition_pairs(check, own) if check.requirements[pair[0]].second_opinion]
            if late or late_own:
                # Items 4-5 c3 (heldout19 UN3): the first reading credited nothing, the second opinion credited SAMBAR,
                # and "the clustering has to be k-means" was never checked -- the condition check ran before it. A
                # workflow the second opinion credits is held to the stated requirements like any other (Log 414).
                late_answers, usage, warnings = request_condition_check(
                    context, state, _condition_shown(check, late + late_own), usage, warnings)
                check = (apply_condition_answers(check, late, late_answers[:len(late)]) if late_answers is not None
                         else _not_checked(check, late))
                check = (apply_own_sentence_answers(check, late_own, late_answers[len(late):]) if late_answers is not None
                         else _not_checked(check, late_own))
                record_event(context, state, "routing.capability_condition_check", "classify", {
                    "stated": stated, "pairs": [[index, action, keys, quote] for index, action, keys, quote in late],
                    "answers": late_answers, "own_sentence": late_own,
                    "after_second_opinion": True, "full_gap": check.full_gap})
        elif pairs and check.full_gap and has_check_model(context):
            # Log 403: the second opinion was owed and could not answer (budget, provider), so the
            # gap is unconfirmed: said as such, and routing's offer stays (as for Log 401's backup).
            check = check.model_copy(update={"full_gap": False, "gap_unconfirmed": True})
        record_event(context, state, "routing.capability_second_opinion", "classify", {
            "pairs": [[index, action, keys] for index, action, keys in pairs], "answers": answers,
            "full_gap": check.full_gap, "gap_unconfirmed": check.gap_unconfirmed,
        })
    result = replace(result, usage=usage, budget_warnings=warnings)
    if provisional:
        # Log 401: the backup model's reading is reported, never acted on; a gap it finds leaves
        # routing's offer in place (Log 400: its three false gaps on heldout9 cleared real workflows).
        record_event(context, state, "routing.capability_check_provisional", "classify", {"full_gap": check.full_gap})
        check = check.model_copy(update={"full_gap": False, "provisional": True})
    # Core decision phase 4b: credits the user's ruled-out inputs make impossible come off, after every other step.
    stated = frozenset(value for item in decision.outcome_hypotheses for value in item.outcome.input_artifacts
                       if value != "unknown") | frozenset(decision.guidance_input_artifacts)
    if (lifted := without_ruled_out(check, stated)) is not check:
        record_event(context, state, "core.ruled_out_applied", "classify", {
            "ruled_out": check.ruled_out, "limits": [row.limits for row in lifted.results()]})
        check = lifted
    if (built := without_unbuilt_network(check, user_task)) is not check:  # ROUND-22: a named CONDOR with no network
        record_event(context, state, "core.unbuilt_network_held", "classify", {
            "limits": [row.limits for row in built.results()]})
        check = built
    # ROUND-17 (user decision): a result resting only on a workflow another row shows cannot run as asked is held too.
    from ..interpretation.same_run import same_run_holds

    if (held := same_run_holds(check)) is not check:
        record_event(context, state, "core.same_run_held", "classify", {
            "held": [row.quote for row, before in zip(held.requirements, check.requirements)
                     if row.status != before.status]})
        check = held
    # Core decision phase 2: the fact agent asks; the fixed dimensions below stand only when it did not run.
    result, decision, check = apply_fact_check(context, state, user_task, result, decision, check)
    if check.needed_facts():
        # Verdict layer step 2: a result waits on a fact the user said they do not know -- on a guidance turn or a
        # run, nothing is selected, refused or run before it is known.
        if shadow_status is not None:
            _record_shadow(context, state, decision, check, shadow_status)
        waiting = waiting_decision(decision, check)
        record_event(context, state, "routing.waiting_on_facts", "classify", {
            "facts": [[item.quote, item.depends_on] for item in check.needed_facts()],
            "cleared": list(dict.fromkeys([decision.action, *decision.matched_actions, *decision.recommended_actions]))})
        return replace(result, decision=waiting,
                       routing_state={**result.routing_state, **outcome_routing_state(waiting)})
    if shadow_status is not None:
        _record_shadow(context, state, decision, check, shadow_status)
        if not check.full_gap:
            return _on_run_verdict(context, state, user_task, result, check, shadow_status)
        decision = decision.model_copy(update={
            "action": "no_tool", "should_execute": False, "intent_type": "answer_question",
            "reason": "No registered workflow produces what the run asks for; it is not planned."})
    # ROUND-21 (R21-A): a full gap no reason can be given for is read once more; no result named -> CLARIFY.
    check, usage, warnings = apply_goal_read(context, state, user_task, decision, check, result.usage,
                                             result.budget_warnings)
    result = replace(result, usage=usage, budget_warnings=warnings)
    if check.full_gap:
        check = check.model_copy(update={"cleared": list(dict.fromkeys(
            [*decision.matched_actions, *decision.hypothesis_actions, *decision.recommended_actions]))})
    update: dict = {"capability_check": check}
    if check.full_gap:
        update.update({
            "matched_actions": [], "hypothesis_actions": [], "recommended_actions": [],
            "alternative_actions": [], "advisory_recommendation": None, "clarification_question": None,
            "capability_match_status": "unsupported",
        })
        record_event(context, state, "routing.capability_full_gap", "classify", {
            "cleared": [*decision.matched_actions, *decision.hypothesis_actions, *decision.recommended_actions],
        })
    decision = decision.model_copy(update=update)
    return replace(result, decision=decision,
                   routing_state={**result.routing_state, **outcome_routing_state(decision)}
                   if check.full_gap else result.routing_state)


def _stated_artifacts(user_task: str, decision: TaskDecision) -> set[str]:
    from ..routing.capability_compatibility import input_availability

    present = set(input_availability(user_task).present)
    for item in decision.outcome_hypotheses:
        present.update(value for value in item.outcome.input_artifacts if value != "unknown")
    return present


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
                or usage.budget_exhausted
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
        if draft.match_basis == "unverified_evidence":
            # ROUND-21 (C31): the reader answered -- the request states no hypotheses to compare ("not sure" opened this
            # path: C31 is unsure which result her supervisor wants). That is a reading, not a failure: no workflow is
            # selected here, and the capability check and the fact agent decide the turn (C31 x4, L14 asked; M33 was
            # clarified -- all labelled a routing failure before).
            draft = draft.model_copy(update={
                "clarification_question": None,
                "reason": "The request states no research hypotheses to compare; no workflow was selected here.",
            })
            return _RouterInvocation(
                decision=draft, routing_state=outcome_routing_state(draft, request_mode="guidance"),
                usage=usage, budget_warnings=warnings, reason_code="research_choices_unread",
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
            "should_execute": False, "action": "no_tool", "execution_requested": False,
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
