"""Public summaries derived from validated transient semantic-goal facts."""

from __future__ import annotations

from ..contracts import TaskDecision


def public_semantic_summary(semantic_goal: dict, decision: TaskDecision) -> str:
    goal = semantic_goal.get("goal") or "I am identifying the best registered workflow for this request."
    candidates = semantic_goal.get("candidates") or []
    unresolved = semantic_goal.get("unresolved_dimensions") or []
    if candidates and unresolved:
        return f"Goal: {goal} Candidates: {', '.join(candidates)}. I still need: {', '.join(unresolved)}."
    if candidates:
        return f"Goal: {goal} Matching registered workflows: {', '.join(candidates)}."
    if decision.action == "no_tool":
        return f"Goal: {goal} This request does not need files or tool execution."
    return f"Goal: {goal} I selected a registered workflow before proceeding."
