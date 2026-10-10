"""Trusted response rendering and response-model graph node."""

from __future__ import annotations

import time
from workflow_registry import LOCAL_EXECUTION_ACTIONS
from ..contracts import (
    AIMessage,
    AgentState,
    EvaluationResult,
    LLMUsage,
    PlanEvaluationResult,
    TaskDecision,
    ToolExecutionResult,
    WorkflowPlan,
    _trace,
)
from ..evaluation import (
    render_execution_response,
    render_needs_input_response,
    render_plan_rejection_response,
    render_input_confirmation_response,
    render_preference_confirmation_response,
)
from ..evaluation.rendering import render_authority_search_response, render_retrieval_failure_response
from ..interpretation import _is_fatal_exception
from ..interpretation.concept_answers import (
    render_cobra_expression_boundary,
    render_capability_gap,
    render_outcome_clarification,
    render_registered_workflow_contract_answer,
    render_sample_specific_coexpression_handoff_boundary,
    render_registered_handoff_script_guidance,
    render_workflow_composition_guidance,
    render_unsupported_algorithm_boundary,
)
from ..interpretation.hypothesis_routes import render_hypothesis_routes
from ..interpretation.research_choices import render_research_choices
from ..interpretation.scientific_guidance import render_scientific_guidance
from ..interpretation.input_alternatives import with_input_alternative_reply
from ..interpretation.outside_steps import with_outside_steps_reply
from ..interpretation.study_purpose_notes import with_study_purpose_reply
from ..interpretation.registry_guidance import should_expand_guidance_catalog
from ..llm import append_llm_usage, build_response_messages, latest_user_task
from ..presentation import strip_cli_owned_guidance_tail
from .context import _GraphContext, preflight_budget, record_event
from .response_context import validated_workflow_context
from .response_payload import trusted_response_context
from ..interpretation.verified_guidance import render_verified_guidance
from ..interpretation.data_plan import with_data_plan_reply
from ..interpretation.capability_check import full_gap_result, unconfirmed_result, with_capability_check_reply
from ..interpretation.unresolved_router_fallback import (
    render_unresolved_router_fallback as _render_unresolved_router_fallback,
)

__all__: list[str] = []


def _is_unresolved_router_fallback(decision: TaskDecision) -> bool:
    """Identify a fail-closed router result before any response-model guessing."""
    reason = decision.reason.casefold()
    return (
        decision.action == "no_tool"
        and decision.confidence <= 0.0
        and not decision.matched_actions
        and not decision.recommended_actions
        and (decision.match_basis in {"semantic_validation_recovery", "provider_unavailable"}
             or "no workflow was selected" in reason
             and ("router" in reason or "semantic routing output failed validation" in reason))
    )


def _reply(content: str, kind: str) -> dict:
    """One deterministic reply, tagged with the renderer that wrote it.

    The tag is what a reply card is built from (``reply_cards``); the text is
    exactly the renderer's, so the conversation, the next turn's context and
    every pinned reply are unchanged.
    """
    return {"messages": [AIMessage(content=content)], "reply_kind": kind}


def respond(context: _GraphContext, state: AgentState) -> dict:
    if (gap := full_gap_result(state, _reply)) is not None:  # Log 387: no renderer may offer a workflow
        return gap
    result = unconfirmed_result(context, state, _reply) or _respond(context, state)  # Log 403: none as the answer
    result = with_input_alternative_reply(result, state, getattr(context, "project_policy", None), _reply)
    result = with_study_purpose_reply(with_outside_steps_reply(result, state, _reply), state, _reply)
    # Logs 383, 387: the data-needs plan, then what was understood to be asked for.
    return with_capability_check_reply(with_data_plan_reply(result, state, _reply), state, _reply)


def _respond(context: _GraphContext, state: AgentState) -> dict:
    decision = TaskDecision.model_validate(state["decision"])
    task = latest_user_task(state["messages"])
    if not decision.stated_hypotheses:
        cobra_boundary = render_cobra_expression_boundary(task)
        if cobra_boundary is not None:
            return _reply(cobra_boundary, "cobra_boundary")
        algorithm_boundary = render_unsupported_algorithm_boundary(task)
        if algorithm_boundary is not None:
            return _reply(algorithm_boundary, "algorithm_boundary")
    workflow_context = validated_workflow_context(
        decision, context.project_policy,
        include_all=should_expand_guidance_catalog(decision, task), task=task,
    )
    verified_guidance = render_verified_guidance(decision, workflow_context)
    plan = WorkflowPlan.model_validate(state["plan"])
    plan_evaluation = (
        PlanEvaluationResult.model_validate(state["plan_evaluation"])
        if state.get("plan_evaluation")
        else None
    )
    structured_results = [
        ToolExecutionResult.model_validate(item)
        for item in state.get("tool_results", [])
    ]
    evaluation = (
        EvaluationResult.model_validate(state["evaluation"])
        if state.get("evaluation")
        else None
    )
    if plan.status == "needs_input":
        return _reply(render_needs_input_response(plan), "needs_input")
    if plan.status == "needs_confirmation":
        if not plan.preference_proposals:
            return _reply(render_input_confirmation_response(plan), "input_confirmation")
        return _reply(render_preference_confirmation_response(plan), "preference_confirmation")
    if plan_evaluation and plan_evaluation.status == "rejected":
        _trace("done", "The Plan Evaluator blocked execution")
        return _reply(render_plan_rejection_response(plan_evaluation), "plan_rejected")
    if decision.action == "download_string" and structured_results:
        return {"messages": [AIMessage(content=structured_results[-1].raw_output)]}
    # Log 248: readings that would collapse into one workflow, or leave one
    # reading without any, are answered one reading at a time.
    hypothesis_routes = (
        None if structured_results
        else render_hypothesis_routes(decision, context.project_policy, task=task)
    )
    if hypothesis_routes is not None:
        return _reply(hypothesis_routes, "hypothesis_routes")
    scientific_explanation = (render_scientific_guidance(decision, context.project_policy, task=task)
                              if not structured_results else None)
    if scientific_explanation is not None:
        return _reply(scientific_explanation, "scientific_guidance")
    # The established clarification renderer already lists all methods for a
    # known goal. Override it only for an unknown goal: a recommendation from
    # quoted study facts on a single-goal tie is that renderer's answer, and
    # replacing it hid every one of them (Log 273).
    needs_choices = bool(decision.requested_outcome is not None
                         and decision.requested_outcome.artifact_type == "unknown")
    choices = (render_research_choices(decision, context.project_policy, task=task)
               if not structured_results and needs_choices else None)
    if choices is not None:
        return _reply(choices, "research_choices")
    sample_handoff_boundary = render_sample_specific_coexpression_handoff_boundary(
        task, context.project_policy,
    )
    if sample_handoff_boundary is not None and not structured_results:
        return _reply(sample_handoff_boundary, "handoff_boundary")
    if decision.requested_outcome is not None:
        capability_gap = render_capability_gap(decision, context.project_policy)
        if capability_gap is not None:
            return _reply(capability_gap, "capability_gap")
    if _is_unresolved_router_fallback(decision):
        _trace(
            "done",
            "The response model was skipped because router validation failed",
        )
        return _reply(_render_unresolved_router_fallback(decision, task), "unresolved")
    # Plan gates have priority. Rejections/fallback provenance must then precede
    # conceptual or script renderers, without retaining contradictory free prose.
    if (workflow_context["rejected_methods"] or decision.capability_match_status == "fallback") and verified_guidance is not None and not structured_results:
        return _reply(verified_guidance, "verified_guidance")
    handoff_script = render_registered_handoff_script_guidance(task, decision, context.project_policy)
    if handoff_script is not None:
        return _reply(handoff_script, "handoff_script")
    workflow_contract_answer = render_registered_workflow_contract_answer(
        task, decision, context.project_policy,
    )
    if workflow_contract_answer is not None:
        return _reply(workflow_contract_answer, "workflow_contract")
    outcome_clarification = render_outcome_clarification(
        decision, context.project_policy, task=task,
        semantic_goal=state.get("semantic_goal"),
    )
    if outcome_clarification is not None:
        return _reply(outcome_clarification, "outcome_clarification")
    composition_guidance = render_workflow_composition_guidance(
        decision,
        context.project_policy,
        state.get("semantic_goal"), task=task,
    )
    if composition_guidance is not None:
        return _reply(composition_guidance, "composition")
    if verified_guidance is not None and not structured_results:
        return _reply(verified_guidance, "verified_guidance")
    retrieval_failure = render_retrieval_failure_response(
        decision, structured_results
    )
    if retrieval_failure is not None:
        _trace("done", "A retrieval failure was rendered without response-model guessing")
        return _reply(retrieval_failure, "retrieval_failure")
    authority_report = None
    if decision.action == "web_search":
        authority_report = render_authority_search_response(task, decision, structured_results)
    if authority_report is not None:
        _trace("done", "An authority search report was rendered deterministically")
        return _reply(authority_report, "authority_report")
    if decision.action in LOCAL_EXECUTION_ACTIONS and structured_results:
        _trace("done", "This workflow turn has finished")
        return _reply(render_execution_response(plan, structured_results, evaluation), "execution")
    combined_results = (
        "\n\n".join(
            f"[{item.action}] status={item.status}\n{item.raw_output}"
            for item in structured_results
        )
        or "(none)"
    )
    trusted_results = [
        item.model_dump(exclude={"raw_output"}) for item in structured_results
    ]
    trusted_context = trusted_response_context(
        decision, workflow_context, state, plan_evaluation, trusted_results,
    )
    response_messages = build_response_messages(
        context.response_prompt,
        trusted_context,
        latest_user_task(state["messages"]),
        combined_results if structured_results else None,
    )
    response_input_text = "\n".join(
        str(message.content) for message in response_messages
    )
    current_usage = state.get("token_usage")
    budget_decision, budget_warnings = preflight_budget(
        context,
        state,
        role="response",
        model=context.response_model_name,
        input_text=response_input_text,
        reserved_output_tokens=context.response_max_tokens,
        allow_reserve=True,
    )
    if budget_decision.status == "blocked":
        usage = LLMUsage.model_validate(
            current_usage or {"budget_tokens": context.task_token_budget}
        )
        usage.budget_exhausted = True
        fallback = (
            "No additional response-model call was made because the configured "
            "task token budget was reached.\n\n"
            f"Router decision: {decision.action}\nReason: {decision.reason}"
        )
        response = AIMessage(content=fallback)
        _trace("evaluate", "Response model skipped at the task token budget")
    else:
        usage = None
    call_started_ns = time.monotonic_ns()
    try:
        if usage is None:
            response = context.response_llm.invoke(response_messages)
            usage = append_llm_usage(
                current_usage,
                role="response",
                model=context.response_model_name,
                response=response,
                input_text=response_input_text,
                output_text=str(response.content),
                budget_tokens=context.task_token_budget,
                duration_ms=max(
                    0,
                    (time.monotonic_ns() - call_started_ns) // 1_000_000,
                ),
                price_catalog=context.price_catalog,
            )
            record_event(
                context,
                state,
                "llm.completed",
                "respond",
                usage.calls[-1].model_dump(mode="json"),
            )
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        _trace(
            "evaluate",
            "The response model failed; using the deterministic fallback",
            type(error).__name__,
        )
        fallback = (
            "The tool workflow finished, but the response model could not produce a summary.\n\n"
            + (
                render_execution_response(plan, structured_results, evaluation)
                if structured_results
                else f"Router decision: {decision.action}\nReason: {decision.reason}"
            )
        )
        response = AIMessage(content=fallback)
        usage = append_llm_usage(
            current_usage,
            role="response",
            model=context.response_model_name,
            input_text=response_input_text,
            output_text="",
            budget_tokens=context.task_token_budget,
            duration_ms=max(
                0,
                (time.monotonic_ns() - call_started_ns) // 1_000_000,
            ),
            status="failed",
            price_catalog=context.price_catalog,
        )
        record_event(
            context,
            state,
            "llm.completed",
            "respond",
            usage.calls[-1].model_dump(mode="json"),
        )
    cleaned_response = strip_cli_owned_guidance_tail(str(response.content))
    if decision.action == "no_tool" and not structured_results:
        status_footer = "No files were inspected and no analysis ran."
        if status_footer.casefold() not in cleaned_response.casefold():
            cleaned_response = (
                f"{cleaned_response.rstrip()}\n\n{status_footer}"
                if cleaned_response.strip()
                else status_footer
            )
    if cleaned_response != str(response.content):
        response = AIMessage(content=cleaned_response)
    if plan.status != "needs_input":
        _trace("done", "This workflow turn has finished")
    return {
        "messages": [response],
        "token_usage": usage.model_dump(),
        "budget_warnings": budget_warnings,
        "reply_kind": "response_model",
    }
