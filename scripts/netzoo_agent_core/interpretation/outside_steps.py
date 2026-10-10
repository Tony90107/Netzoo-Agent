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

from .inspected_answers import _NOT_INSPECTED, above_closing

__all__ = ["outside_concern_answer", "outside_steps", "with_outside_steps", "with_outside_steps_reply"]

_REPLY_KINDS = frozenset({
    "outcome_clarification", "research_choices", "verified_guidance", "scientific_guidance",
    "workflow_contract", "composition", "capability_gap", "hypothesis_routes",
    "capability_unconfirmed", "unmapped_request",  # Log 403
})


def _listed(decision) -> set[str]:
    advice = decision.advisory_recommendation
    check = decision.capability_check
    return {*decision.matched_actions, *decision.hypothesis_actions, *decision.recommended_actions,
            *([advice.action] if advice is not None else []),
            # Log 392: candidates a full gap cleared still tie their notes (ALPACA beside CONDOR).
            *(check.cleared if check is not None else [])}


def outside_steps(decision, task: str) -> list[OutsideStep]:
    """The entries whose words the request states, for a reply listing one of their workflows."""
    listed = _listed(decision)
    return [
        step for step in OUTSIDE_STEPS
        if all(re.search(pattern, task, re.I) for pattern in step.witnesses)
        and (not step.workflows or step.workflows & listed)
    ]


def outside_concern_answer(action: str, quote: str) -> str | None:
    """What to say instead of `action`'s own note when the quoted concern is a step outside the registry.

    Test 8 (r5, Log 331): the concern matcher tied "how can we directly
    quantify this differential modular structure between the two networks?"
    to CONDOR's downstream note, so core scores read as the answer. The quote
    itself must name the step (every witness), and the step must concern this
    workflow; its paragraph is then in the same reply (`with_outside_steps`).
    """
    return next((step.concern_answer for step in OUTSIDE_STEPS
                 if step.concern_answer and (not step.workflows or action in step.workflows)
                 and all(re.search(pattern, quote, re.I) for pattern in step.witnesses)), None)


# A quoted request ("…?") inside a paragraph is not the reply's own question.
_QUOTED = re.compile(r'"[^"]*"|“[^”]*”')


def _asks(paragraph: str) -> bool:
    """The reply's closing question, as the reply renderers write it: plain prose with a '?'."""
    return not paragraph.lstrip().startswith(("-", "*", "#")) and "?" in _QUOTED.sub("", paragraph)


def with_outside_steps(text: str, decision, task: str) -> str:
    """The notes above the reply's question, or above its closing paragraph when it asks none.

    Test 4 (r5, Log 331): the single-cell note came after "Which reading
    should we start with ...?", so the question was asked before the reader
    learned the workflows are built for bulk samples.
    """
    steps = outside_steps(decision, task)
    if not steps or not text:
        return text
    block = "\n\n".join(step.note for step in steps)
    paragraphs = text.split("\n\n")
    closing = next((i for i, part in enumerate(paragraphs) if _NOT_INSPECTED in part), None)
    if closing is not None and closing > 1 and _asks(paragraphs[closing - 1]):
        return "\n\n".join([*paragraphs[:closing - 1], block, *paragraphs[closing - 1:]])
    return above_closing(text, block)


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
