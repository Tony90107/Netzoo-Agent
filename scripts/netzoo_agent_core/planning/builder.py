"""Public orchestration entry point for deterministic planning."""

from __future__ import annotations

from typing import Any

from .assembly import _assemble_workflow_plan
from .context import _prepare_planning_context
from .evidence import _build_evidence_ledger
from ..contracts import (
    Episode,
    ProjectPolicySnapshot,
    TaskDecision,
    UserProfile,
    WorkflowPlan,
)

__all__ = ["build_workflow_plan"]


def build_workflow_plan(
    raw_decision: TaskDecision,
    task: str,
    profile: UserProfile | dict | None = None,
    retrieved_episodes: list[Episode | dict] | None = None,
    project_policy: ProjectPolicySnapshot | dict | None = None,
    content_mapper: Any | None = None,
) -> WorkflowPlan:
    """Turn intent into an evidence-backed, multi-step NetZoo workflow."""
    context_or_plan = _prepare_planning_context(
        raw_decision,
        task,
        profile,
        retrieved_episodes,
        project_policy,
        content_mapper,
    )
    if isinstance(context_or_plan, WorkflowPlan):
        return context_or_plan
    evidence = _build_evidence_ledger(context_or_plan)
    return _assemble_workflow_plan(context_or_plan, evidence)
