"""Deterministic answers for basic registered-workflow concept questions."""

from __future__ import annotations

import re

from ..contracts import ProjectPolicySnapshot, TaskDecision
from ..presentation import _ui_text

_PURPOSE_PATTERN = re.compile(
    r"\b(?:function|purpose|what\s+is|what\s+does)\b|(?:功能|用途|是什麼)",
    flags=re.IGNORECASE,
)


def render_spec_backed_concept_answer(
    task: str,
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
) -> str | None:
    """Return registered workflow facts for a basic no-tool purpose question."""
    if not (
        decision.in_scope
        and decision.action == "no_tool"
        and _PURPOSE_PATTERN.search(task)
    ):
        return None
    normalized = task.casefold()
    for spec in policy.workflows.values():
        if spec.workflow.casefold() not in normalized:
            continue
        inputs = ", ".join(spec.required_inputs) or "no registered required inputs"
        return _ui_text(
            f"{spec.workflow} {spec.description}\n\n"
            f"Registered required inputs: {inputs}.\n"
            "No files were inspected and no analysis ran."
        )
    return None


def render_ambiguous_workflow_guidance(
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
) -> str | None:
    """Explain multiple registered candidates without inventing a selection."""
    if not (
        decision.in_scope
        and decision.action == "no_tool"
        and len(decision.recommended_actions) > 1
    ):
        return None
    specs = [policy.workflows.get(action) for action in decision.recommended_actions]
    registered = [spec for spec in specs if spec is not None]
    if len(registered) < 2:
        return None
    options = "\n".join(f"- {spec.workflow}: {spec.description}" for spec in registered)
    return _ui_text(
        "I can match your goal to more than one registered workflow:\n"
        f"{options}\n\n"
        "To recommend one workflow, please clarify which regulatory relationship "
        "you want to model. No files were inspected and no analysis ran."
    )


__all__ = ["render_spec_backed_concept_answer", "render_ambiguous_workflow_guidance"]
