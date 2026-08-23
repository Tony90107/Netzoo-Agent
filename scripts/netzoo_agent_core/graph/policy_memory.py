"""Project-policy and durable-memory graph nodes."""

from __future__ import annotations

from ..contracts import (
    AgentState,
    EvaluationResult,
    ToolExecutionResult,
    WorkflowPlan,
    _trace,
)
from .context import _GraphContext, record_event

__all__: list[str] = []


def apply_project_policy(context: _GraphContext, state: AgentState) -> dict:
    project_policy = context.project_policy
    _trace(
        "policy",
        f"Project policy loaded: version={project_policy.policy_version}, "
        f"hash={project_policy.policy_hash[:12]}",
        f"AGENTS={project_policy.agents_path}, workflows={len(project_policy.workflows)}",
    )
    record_event(
        context,
        state,
        "policy.loaded",
        "apply_project_policy",
        {
            "policy_version": project_policy.policy_version,
            "policy_hash": project_policy.policy_hash,
            "agents_path": project_policy.agents_path,
            "workflow_count": len(project_policy.workflows),
        },
    )
    return {"project_policy": project_policy.model_dump()}


def retrieve_memory(context: _GraphContext, state: AgentState) -> dict:
    user_task = str(state["messages"][-1].content)
    profile = context.profile_store.load(context.profile_id)
    hits = context.episode_store.search_hits(context.profile_id, user_task, limit=3)
    episodes = [hit.episode for hit in hits]
    _trace(
        "memory",
        f"Memory retrieval: profile={profile.profile_id}, episodes={len(episodes)}",
    )
    record_event(
        context,
        state,
        "memory.retrieved",
        "retrieve_memory",
        {
            "profile_id": profile.profile_id,
            "episode_count": len(episodes),
            "episodes": [hit.trace_payload() for hit in hits],
        },
    )
    return {
        "profile": profile.model_dump(),
        "retrieved_episodes": [episode.model_dump() for episode in episodes],
    }


def consolidate_memory(context: _GraphContext, state: AgentState) -> dict:
    evaluation_data = state.get("evaluation")
    result_data = state.get("tool_results", [])
    if not evaluation_data or not result_data:
        return {}
    evaluation = EvaluationResult.model_validate(evaluation_data)
    if evaluation.status not in {"completed", "failed"}:
        return {}
    plan = WorkflowPlan.model_validate(state["plan"])
    results = [ToolExecutionResult.model_validate(item) for item in result_data]
    task = str(state["messages"][-1].content)
    episode = context.episode_store.record(
        profile_id=context.profile_id,
        task=task,
        plan=plan,
        results=results,
        evaluation=evaluation,
        replan_count=state.get("replan_count", 0),
    )
    _trace(
        "memory",
        f"Memory consolidation: recorded episode {episode.episode_id[:8]}",
        f"workflow={episode.workflow}, status={episode.status}",
    )
    record_event(
        context,
        state,
        "memory.consolidated",
        "consolidate_memory",
        {
            "episode_id": episode.episode_id,
            "workflow": episode.workflow,
            "status": episode.status,
        },
    )
    return {}
