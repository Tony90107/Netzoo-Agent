"""Core decision spec, phase 1: the reply to a request that names no result yet (CLARIFY, spec section 5).

Round p0 (2026-10-15): of 14 requests that named no result, 9 were answered "No registered workflow produces this"
and 2 were given one workflow as fitting. The goal is asked before any workflow is chosen: the reply lists what the
registered workflows can give from the data the request states -- as possible results, never as fitting -- and asks
one question. It is the whole reply: nothing understood-as-asked, no workflow card, no plan.
"""

from __future__ import annotations

import re

from workflow_registry import ACTION_DEFINITIONS

from ..capability_sheet import produced_text
from ..method_names import workflows_in

__all__ = ["CLARIFY_KIND", "clarify_result", "clarify_reply", "named_comparison"]

CLARIFY_KIND = "clarify_goal"
_ARTIFACT_NAMES = {"expression_matrix": "expression data", "mutation_matrix": "somatic mutations",
                   "measurement_dataset": "a second omics layer", "regulatory_network": "an existing regulatory network",
                   "coexpression_network": "a co-expression matrix"}


def _first_sentence(text: str) -> str:
    head = re.split(r"(?<!\be\.g)(?<!\bi\.e)\.\s", text)[0].strip().rstrip(".")
    return head if len(head) <= 160 else head[:157].rstrip() + "..."


def named_comparison(need) -> list[str]:
    """The workflows the request itself named, when they are the whole choice; else [].

    Spec section 5: a request that names workflows but no goal "may compare the named options, but must end by asking
    the goal". The candidates are then the named ones (`goal_evidence.method_choice`), never the whole registry.
    """
    from .goal_evidence import compared_workflows

    named = compared_workflows(need.goal_quote)
    return list(need.candidates) if len(need.candidates) >= 2 and set(need.candidates) <= set(named) else []


def _comparison_reply(names: list[str], need, task: str) -> str:
    """How the named workflows differ, from the registry alone; then the one question that picks between them."""
    from collections import Counter

    from workflow_registry import OUTPUT_CAPABILITIES

    from ..interpretation.practical_notes import practical_notes
    from ..interpretation.tie_guidance import _distinguishing_note, _inputs

    actions = {definition.workflow: action for action, definition in ACTION_DEFINITIONS.items()}
    # The tie replies' algorithm notes (Log 261): each method's least-shared tag among the ones named, so two methods
    # that give the same result are told apart by how they fit it.
    shared = Counter(tag for name in names for tag in OUTPUT_CAPABILITIES[actions[name]].selection_tags)
    lines = []
    for name in names:
        action = actions[name]
        parts = [f"- {name}: {_first_sentence(produced_text(action))}."]
        if note := _distinguishing_note(OUTPUT_CAPABILITIES[action], shared, full=False):
            parts.append(f"How it works: {note}")
        if needs := _inputs(ACTION_DEFINITIONS[action]):
            parts.append(needs)
        parts.extend(practical_notes(action, task, short=True))
        lines.append(" ".join(parts))
    return "\n\n".join([
        f"How {' and '.join(names) if len(names) == 2 else ', '.join(names[:-1]) + ' and ' + names[-1]} differ:",
        "\n".join(lines),
        f"To pick one for your study: {need.question}",
        "Nothing was selected and nothing runs before you answer.\n\nNo files were inspected and no analysis ran.",
    ])


def clarify_reply(core, task: str = "") -> str:
    need = core.clarify
    if names := named_comparison(need):
        return _comparison_reply(names, need, task)
    actions = {definition.workflow: action for action, definition in ACTION_DEFINITIONS.items()}
    lines = []
    for name in need.candidates:
        if (action := actions.get(name)) is not None and (text := produced_text(action)):
            lines.append(f"- {_first_sentence(text)} ({name})")
    data = [_ARTIFACT_NAMES.get(item, item.replace("_", " ")) for item in need.inputs]
    lead = (f"With {' and '.join(data)}, the registered workflows can give these results:" if data else
            "The registered workflows give these results:")
    return "\n\n".join([
        "I can't tell yet which result you want, so I have not chosen a workflow.",
        lead + "\n" + "\n".join(lines),
        need.question,
        "Nothing was selected and nothing runs before you answer.\n\nNo files were inspected and no analysis ran.",
    ])


def clarify_result(state, reply) -> dict | None:
    """The whole reply when the turn's core call is CLARIFY, else None."""
    from ..contracts import TaskDecision

    core = TaskDecision.model_validate(state["decision"]).core
    if core is None or core.kind != "CLARIFY" or core.clarify is None or not core.clarify.question:
        return None  # a phase-0 CLARIFY (nothing read, nothing routed) keeps its existing reply
    from ..llm import latest_user_task

    return reply(clarify_reply(core, latest_user_task(state.get("messages") or [])), CLARIFY_KIND)
