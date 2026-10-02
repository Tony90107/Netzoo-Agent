"""Resume a validated workflow continuation without re-routing it through an LLM."""

from __future__ import annotations

from pydantic import ValidationError
from workflow_registry import OUTPUT_CAPABILITIES

from ..contracts import AgentState, LLMUsage, TaskDecision
from ..contracts.interaction import MethodComparison, WorkflowContinuation
from ..contracts.outcomes import OutcomeHypothesis, RequestedOutcome
from ..interpretation.hydration import hydrate_router_decision
from ..interpretation.semantic_goal import outcome_routing_state
from ..routing.capability_compatibility import _supported_artifacts
from ..settings import ROUTER_CONTEXT_MAX_CHARS
from .condition_recommender import invoke_condition_recommender
from .context import _GraphContext, record_event
from .invocation_types import RouterInvocation


def continue_workflow(
    context: _GraphContext,
    state: AgentState,
    task: str,
    usage: LLMUsage,
):
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
                **continuation.parameters,
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
    return RouterInvocation(
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


def _shared_outcome(actions: list[str]) -> RequestedOutcome | None:
    """The result every compared workflow produces, from the registry alone."""
    capabilities = [OUTPUT_CAPABILITIES[action] for action in actions]
    artifacts = frozenset.intersection(*(_supported_artifacts(cap) for cap in capabilities))
    own = [cap.artifact_type for cap in capabilities if cap.artifact_type in artifacts]
    if len(set(own)) != 1:
        return None
    scales = frozenset.intersection(*(frozenset(cap.granularities) for cap in capabilities))
    regulators = frozenset.intersection(*(frozenset(cap.regulator_types) for cap in capabilities))
    return RequestedOutcome(
        operation=capabilities[0].operation if len({cap.operation for cap in capabilities}) == 1 else "unknown",
        artifact_type=own[0],
        entity_types=sorted(frozenset.intersection(*(frozenset(cap.entity_types) for cap in capabilities))),
        regulator_types=sorted(regulators),
        target_types=sorted(frozenset.intersection(*(frozenset(cap.target_types) for cap in capabilities))),
        granularity=next(iter(scales)) if len(scales) == 1 else "unknown",
        unresolved_dimensions=[] if len(scales) == 1 else ["granularity"],
    )


def compare_workflows(context: _GraphContext, state: AgentState, task: str, usage: LLMUsage):
    """The tie a picked Compare option names, without re-reading the request (Log 302).

    Returns None when the comparison does not match this task and policy; the
    turn is then routed as an ordinary follow-up.
    """
    try:
        comparison = MethodComparison.model_validate(state["method_comparison"])
        if (comparison.task != task[-ROUTER_CONTEXT_MAX_CHARS:]
                or set(comparison.actions) - set(context.project_policy.workflows)):
            raise ValueError("The comparison does not match the current task and policy.")
    except (ValidationError, ValueError):
        record_event(context, state, "routing.method_comparison", "classify", {"reason_code": "invalid_method_comparison"})
        return None
    actions = list(comparison.actions)
    outcome = _shared_outcome(actions)
    decision = TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, confidence=1.0,
        intent_type="answer_question",
        reason="Comparing the registered workflows the user asked to compare.",
        candidate_actions=[*actions[:5], "no_tool"], hypothesis_actions=actions,
        capability_match_status="ambiguous", match_basis="confirmed_context",
        requested_outcome=outcome,
        outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=1.0)] if outcome else [],
        clarification_question="Which method fits your study?",
    )
    record_event(context, state, "routing.method_comparison", "classify",
                 {"reason_code": "method_comparison", "actions": actions})
    # Study facts stated in the previous goal may still ground a recommendation.
    decision, usage, budget_warnings = invoke_condition_recommender(
        context, state, task, decision, usage, list(state.get("budget_warnings", [])),
    )
    return RouterInvocation(
        decision=decision,
        routing_state=outcome_routing_state(decision, decision.reason, "guidance"),
        usage=usage, budget_warnings=budget_warnings, reason_code="method_comparison",
    )
