"""Human-readable workflow-plan rendering."""

from __future__ import annotations

from ..contracts import WorkflowPlan

__all__ = ["render_plan"]


def render_plan(plan: WorkflowPlan) -> str:
    lines = [f"Workflow: {plan.workflow}", "Evidence ledger:"]
    if not plan.evidence:
        lines.append("- This task does not require local data files.")
    for item in plan.evidence:
        value = f" → {item.value}" if item.value else ""
        lines.append(f"- {item.field}: {item.status}{value} ({item.reason})")
        if item.status == "missing" and item.candidates:
            lines.append("  Candidates: " + ", ".join(item.candidates))
    if plan.steps:
        lines.append("Execution plan:")
        for index, step in enumerate(plan.steps, 1):
            lines.append(f"{index}. {step.action}: {step.purpose}")
    if plan.memory_notes:
        lines.append("Retrieved memory:")
        lines.extend(f"- {note}" for note in plan.memory_notes)
    if plan.policy_notes:
        lines.append(f"Project policy ({(plan.policy_hash or 'unknown')[:12]}):")
        lines.extend(f"- {note}" for note in plan.policy_notes)
    if plan.preference_proposals:
        lines.append("Preference changes awaiting confirmation:")
        lines.extend(
            f"- {proposal.key} = {proposal.value} ({proposal.reason})"
            for proposal in plan.preference_proposals
        )
    if plan.question:
        lines.append("User input required: " + plan.question)
    return "\n".join(lines)
