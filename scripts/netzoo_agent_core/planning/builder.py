"""Public orchestration entry point for deterministic planning."""

from __future__ import annotations

from typing import Any

from .assembly import _assemble_workflow_plan
from .context import _prepare_planning_context
from .evidence import _build_evidence_ledger
from ..contracts.requirements import RequestRequirements
from ..contracts import (
    Episode,
    InputEvidence,
    ProjectPolicySnapshot,
    TaskDecision,
    UserProfile,
    WorkflowPlan,
    WorkflowStep,
)

__all__ = ["build_workflow_plan"]


def build_workflow_plan(
    raw_decision: TaskDecision,
    task: str,
    profile: UserProfile | dict | None = None,
    retrieved_episodes: list[Episode | dict] | None = None,
    project_policy: ProjectPolicySnapshot | dict | None = None,
    content_mapper: Any | None = None,
    requirements: RequestRequirements | dict | None = None,
) -> WorkflowPlan:
    """Turn intent into an evidence-backed, multi-step NetZoo workflow.

    *requirements*: the turn's RequestRequirements (plan item 2).
    """
    if raw_decision.action == "download_string":
        decision = raw_decision.model_copy(deep=True)
        evidence = []
        for field, question, candidates in (
            ("taxon", "Which species should I download? Enter a species name or NCBI taxonomy ID.", []),
            ("string_network_type", "Which STRING network type: functional, physical, or regulatory?", ["functional", "physical", "regulatory"]),
        ):
            value = getattr(decision, field)
            evidence.append(InputEvidence(
                field=field, status="provided" if value else "missing", value=value,
                reason="Specified in the acquisition request." if value else question,
                candidates=candidates if not value else [],
            ))
        missing = [item.field for item in evidence if item.status == "missing"]
        decision.missing_inputs = missing
        decision.should_execute = not missing
        return WorkflowPlan(
            workflow="STRING-DOWNLOAD", objective=decision.reason,
            decision=decision.model_dump(), evidence=evidence,
            missing_inputs=missing,
            status="needs_input" if missing else "ready",
            question=" ".join(item.reason for item in evidence if item.status == "missing") or None,
            steps=[] if missing else [WorkflowStep(
                action="download_string",
                purpose="Download the selected existing STRING network from its official host.",
            )],
        )
    context_or_plan = _prepare_planning_context(
        raw_decision,
        task,
        profile,
        retrieved_episodes,
        project_policy,
        content_mapper,
        requirements,
    )
    if isinstance(context_or_plan, WorkflowPlan):
        return context_or_plan
    evidence = _build_evidence_ledger(context_or_plan)
    return _assemble_workflow_plan(context_or_plan, evidence)
