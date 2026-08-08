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


__all__ = ["render_spec_backed_concept_answer"]
