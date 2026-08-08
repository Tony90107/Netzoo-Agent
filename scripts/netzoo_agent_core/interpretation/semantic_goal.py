"""Public summaries derived from validated transient semantic-goal facts."""

from __future__ import annotations

from ..contracts import TaskDecision
from workflow_registry import workflow_name


def public_semantic_summary(semantic_goal: dict, decision: TaskDecision) -> str:
    candidates = semantic_goal.get("candidates") or []
    unresolved = semantic_goal.get("unresolved_dimensions") or []
    display_candidates = [workflow_name(action) for action in candidates]
    goal = semantic_goal.get("goal") or ""
    if candidates and unresolved:
        prefix = f"Goal: {goal} " if goal else "I found multiple registered approaches for this goal. "
        return f"{prefix}Candidates: {', '.join(display_candidates)}. I still need: {', '.join(unresolved)}."
    if candidates:
        prefix = f"Goal: {goal} " if goal else "I found registered approaches that fit this goal. "
        return f"{prefix}Candidates: {', '.join(display_candidates)}."
    if decision.action == "no_tool":
        return "This request does not need files or tool execution."
    return "I selected a registered workflow before proceeding."


def semantic_summary_detail(semantic_goal: dict, decision: TaskDecision) -> dict:
    return {"kind": "semantic_goal", "text": public_semantic_summary(semantic_goal, decision)}
