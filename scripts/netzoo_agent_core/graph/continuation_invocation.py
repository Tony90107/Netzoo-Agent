"""Resume a validated workflow continuation without re-routing it through an LLM."""

from __future__ import annotations

from pydantic import ValidationError
from workflow_registry import OUTPUT_CAPABILITIES

from ..contracts import AgentState, LLMUsage, TaskDecision
from ..contracts.interaction import WorkflowContinuation
from ..contracts.outcomes import RequestedOutcome
from ..interpretation.hydration import hydrate_router_decision
from ..interpretation.semantic_goal import outcome_routing_state
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
