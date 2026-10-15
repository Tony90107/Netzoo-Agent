"""Core decision spec, phase 1: the reply to a request that names no result yet (CLARIFY, spec section 5).

Round p0 (2026-10-15): of 14 requests that named no result, 9 were answered "No registered workflow produces this"
and 2 were given one workflow as fitting. The goal is asked before any workflow is chosen: the reply lists what the
registered workflows can give from the data the request states -- as possible results, never as fitting -- and asks
one question. It is the whole reply: nothing understood-as-asked, no workflow card, no plan.
"""

from __future__ import annotations

from workflow_registry import ACTION_DEFINITIONS

from ..capability_sheet import produced_text

__all__ = ["CLARIFY_KIND", "clarify_result", "clarify_reply"]

CLARIFY_KIND = "clarify_goal"
_ARTIFACT_NAMES = {"expression_matrix": "expression data", "mutation_matrix": "somatic mutations",
                   "measurement_dataset": "a second omics layer", "regulatory_network": "an existing regulatory network",
                   "coexpression_network": "a co-expression matrix"}


def _first_sentence(text: str) -> str:
    head = text.split(". ")[0].strip().rstrip(".")
    return head if len(head) <= 160 else head[:157].rstrip() + "..."


def clarify_reply(core) -> str:
    need = core.clarify
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
        lead + "\n" + "\n".join(lines[:10]),
        need.question,
        "Nothing was selected and nothing runs before you answer.\n\nNo files were inspected and no analysis ran.",
    ])


def clarify_result(state, reply) -> dict | None:
    """The whole reply when the turn's core call is CLARIFY, else None."""
    from ..contracts import TaskDecision

    core = TaskDecision.model_validate(state["decision"]).core
    if core is None or core.kind != "CLARIFY" or core.clarify is None or not core.clarify.question:
        return None  # a phase-0 CLARIFY (nothing read, nothing routed) keeps its existing reply
    return reply(clarify_reply(core), CLARIFY_KIND)
