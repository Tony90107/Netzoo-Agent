"""Say what the request needs that no registered workflow does (Log 320).

TEST_PROMPTS Tests 4, 7, 8 and 9 (2026-10-03) ask for a step outside the
registry: single-cell networks, a prior filtered by open chromatin, a
comparison of module structure between two networks, a convex guarantee. The
replies answered with registered workflows alone, and Test 8 offered CONDOR
for "differential modular structure" as if it measured that. Each
`OUTSIDE_STEPS` entry adds one paragraph, before the closing line, when the
request's own words name that situation; it names the published method, says
it is not registered here, and gives the manual route. Nothing here selects,
ranks or recommends a workflow.
"""

from __future__ import annotations

import re

from workflow_registry import OUTSIDE_STEPS, OutsideStep

from .inspected_answers import _NOT_INSPECTED

__all__ = ["outside_steps", "with_outside_steps", "with_outside_steps_reply"]

_REPLY_KINDS = frozenset({
    "outcome_clarification", "research_choices", "verified_guidance", "scientific_guidance",
    "workflow_contract", "composition", "capability_gap", "hypothesis_routes",
})


def _listed(decision) -> set[str]:
    advice = decision.advisory_recommendation
    return {*decision.matched_actions, *decision.hypothesis_actions, *decision.recommended_actions,
            *([advice.action] if advice is not None else [])}


def outside_steps(decision, task: str) -> list[OutsideStep]:
    """The entries whose words the request states, for a reply listing one of their workflows."""
    listed = _listed(decision)
    return [
        step for step in OUTSIDE_STEPS
        if all(re.search(pattern, task, re.I) for pattern in step.witnesses)
        and (not step.workflows or step.workflows & listed)
    ]


def with_outside_steps(text: str, decision, task: str) -> str:
    steps = outside_steps(decision, task)
    if not steps or not text:
        return text
    block = "\n\n".join(step.note for step in steps)
    paragraphs = text.split("\n\n")
    # Above the closing paragraph, which may begin with another closing sentence.
    closing = next((i for i, part in enumerate(paragraphs) if _NOT_INSPECTED in part), None)
    if closing is None:
        return text + "\n\n" + block
    return "\n\n".join([*paragraphs[:closing], block, *paragraphs[closing:]])


def with_outside_steps_reply(result: dict, state, reply) -> dict:
    """`respond()`'s last step: the same reply, with the paragraphs when they apply."""
    from ..contracts import TaskDecision
    from ..llm import latest_user_task

    if result.get("reply_kind") not in _REPLY_KINDS:
        return result
    text = str(result["messages"][-1].content)
    updated = with_outside_steps(text, TaskDecision.model_validate(state["decision"]),
                                 latest_user_task(state["messages"]))
    return result if updated == text else reply(updated, result["reply_kind"])
