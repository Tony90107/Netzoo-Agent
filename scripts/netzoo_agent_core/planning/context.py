"""Validated planning context preparation and early-plan decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from workflow_registry import (
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
from ..policy import ProjectPolicyLoader
from ..routing import enforce_capability_gate

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
    content_mapper: Any | None = None
    preflight_errors: list[str] = field(default_factory=list)


def _prepare_planning_context(
    raw_decision: TaskDecision,
    task: str,
    profile: UserProfile | dict | None,
    retrieved_episodes: list[Episode | dict] | None,
    project_policy: ProjectPolicySnapshot | dict | None,
    content_mapper: Any | None = None,
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
    action = decision.action
    workflow = _workflow_name(action)
    if action != "no_tool":
        decision = enforce_capability_gate(decision, user_task=task)
        action = decision.action
        workflow = _workflow_name(action)

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
        content_mapper=content_mapper,
    )
