"""Validated planning context preparation and early-plan decisions."""

from __future__ import annotations

import re
from dataclasses import dataclass

from workflow_registry import (
    LOCAL_WORKFLOW_ACTIONS,
    REQUIRED_INPUTS,
    workflow_name as _workflow_name,
)

from ..contracts import (
    Episode,
    ProjectPolicySnapshot,
    TaskDecision,
    UserProfile,
    WorkflowPlan,
    WorkflowPolicySpec,
    WorkflowStep,
)
from ..interpretation import (
    _lioness_mode_plan,
    _needs_lioness_mode_choice,
)
from ..policy import ProjectPolicyLoader
from ..routing import (
    MIN_TOOL_CONFIDENCE,
    enforce_capability_gate,
    validate_task_text,
)

__all__: list[str] = []


@dataclass
class _PlanningContext:
    decision: TaskDecision
    task: str
    profile: UserProfile
    episodes: list[Episode]
    memory_notes: list[str]
    policy: ProjectPolicySnapshot | None
    policy_hash: str | None
    policy_notes: list[str]
    workflow_spec: WorkflowPolicySpec | None
    action: str
    workflow: str
    required: list[str]


def _prepare_planning_context(
    raw_decision: TaskDecision,
    task: str,
    profile: UserProfile | dict | None,
    retrieved_episodes: list[Episode | dict] | None,
    project_policy: ProjectPolicySnapshot | dict | None,
) -> _PlanningContext | WorkflowPlan:
    decision = raw_decision.model_copy(deep=True)
    profile_model = (
        UserProfile.model_validate(profile)
        if profile is not None
        else UserProfile(profile_id="default")
    )
    episode_models = [
        Episode.model_validate(item) for item in (retrieved_episodes or [])
    ]
    memory_notes = [
        f"Retrieved {episode.status} episode {episode.episode_id[:8]} for {episode.workflow}."
        for episode in episode_models
    ]
    policy_model = (
        ProjectPolicySnapshot.model_validate(project_policy)
        if project_policy is not None
        else None
    )
    if policy_model is not None:
        ProjectPolicyLoader._validate_against_code(policy_model.workflows)
    policy_hash = policy_model.policy_hash if policy_model else None
    policy_notes = []
    workflow_spec = None
    preferred_workflow_authorized = False
    preferred_workflow = profile_model.preferences.get("preferred_workflow")
    if (
        decision.action == "no_tool"
        and isinstance(preferred_workflow, str)
        and re.search(
            r"(preferred|default).{0,16}workflow|workflow.{0,16}(preferred|default)"
            r"|偏好.{0,8}(工作流|流程)|預設.{0,8}(工作流|流程)",
            task,
            flags=re.IGNORECASE,
        )
        and re.search(r"(run|execute|start|執行|開始|跑)", task, flags=re.IGNORECASE)
    ):
        decision.action = f"run_{preferred_workflow}"
        decision.in_scope = True
        decision.should_execute = True
        decision.confidence = max(decision.confidence, MIN_TOOL_CONFIDENCE)
        decision.reason = (
            f"The user explicitly requested the confirmed preferred workflow: "
            f"{preferred_workflow}."
        )
        preferred_workflow_authorized = True
        memory_notes.append(
            f"Applied confirmed preferred_workflow={preferred_workflow}."
        )
    if _needs_lioness_mode_choice(task):
        return _lioness_mode_plan(
            decision,
            task,
            memory_notes=memory_notes,
            policy_hash=policy_hash,
        )
    action = decision.action
    workflow = _workflow_name(action)
    if action in {"query_context7", "web_search"}:
        decision = enforce_capability_gate(decision, user_task=task)
        action = decision.action
        workflow = _workflow_name(action)
    elif action != "no_tool":
        rejection = (
            None if preferred_workflow_authorized else validate_task_text(task, action)
        )
        reasons = []
        if rejection:
            reasons.append(rejection)
        if (
            action in LOCAL_WORKFLOW_ACTIONS
            and decision.intent_type == "answer_question"
        ):
            reasons.append(
                "The request was classified as an information question, not an execution request."
            )
        if not decision.in_scope:
            reasons.append("The task is outside the NetZoo agent capability scope.")
        if decision.confidence < MIN_TOOL_CONFIDENCE:
            reasons.append(
                f"Tool-selection confidence is too low ({decision.confidence:.2f})."
            )
        if reasons:
            decision = TaskDecision(
                action="no_tool",
                in_scope=decision.in_scope,
                should_execute=False,
                confidence=decision.confidence,
                reason="；".join(reasons),
                recommended_actions=decision.recommended_actions,
            )
            action = "no_tool"
            workflow = "NO-TOOL"

    if policy_model and action in policy_model.workflows:
        workflow_spec = policy_model.workflows[action]
        policy_notes = [
            f"Validated workflow specification {workflow_spec.workflow} under project policy {policy_hash[:12]}.",
            *workflow_spec.conventions,
        ]

    if action == "no_tool" or action in {"query_context7", "web_search"}:
        steps = (
            []
            if action == "no_tool"
            else [
                WorkflowStep(
                    action=action,
                    purpose="Retrieve reference material required for the answer.",
                )
            ]
        )
        return WorkflowPlan(
            workflow=workflow,
            objective=decision.reason,
            decision=decision.model_dump(),
            steps=steps,
            status="respond_only" if action == "no_tool" else "ready",
            memory_notes=memory_notes,
            policy_hash=policy_hash,
            policy_notes=policy_notes,
        )

    required = (
        list(workflow_spec.required_inputs)
        if workflow_spec is not None
        else list(REQUIRED_INPUTS[action])
    )
    return _PlanningContext(
        decision=decision,
        task=task,
        profile=profile_model,
        episodes=episode_models,
        memory_notes=memory_notes,
        policy=policy_model,
        policy_hash=policy_hash,
        policy_notes=policy_notes,
        workflow_spec=workflow_spec,
        action=action,
        workflow=workflow,
        required=required,
    )
