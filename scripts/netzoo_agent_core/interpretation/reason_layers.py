"""Harness repair P2 (user decision 2026-10-23, spec section 10): every part a reply cannot do has a reason.

Layer 1 is a reason code verifies against the contract and the user's words (`stated_reasons.stated`, ROUND-20).
When there is none, layer 2 says what was checked, never why it cannot be done: the user's words could not be
matched to anything a registered workflow produces or lets you set, what a workflow those words name gives, and --
once per reply -- which registered workflows take the kind of data the request describes. Every sentence is built in
code from the registry; none is the model's.

It replaces "not matched to any registered workflow" (ROUND-20: 67 of 208 decline replies said only that) and the
unverified "No registered workflow produces this", false when the check misjudged (live C51). A "no registered
workflow" claim stays only beside a registry-wide reason (`stated_reasons._form_reasons`, a registry_wide entry).
"""

from __future__ import annotations

from workflow_registry import OUTPUT_CAPABILITIES, workflow_name

from ..capability_sheet import entry, produced_text
from ..method_names import registered_workflows, workflows_in

__all__ = ["UNMATCHED", "UNMATCHED_RESULT", "is_unmatched", "options_line", "registry_wide", "unmatched"]

UNMATCHED = "I couldn't match this to anything a registered NetZoo workflow produces or lets you set."
UNMATCHED_RESULT = "I couldn't match this to a result any registered NetZoo workflow produces."


def unmatched(item) -> str:
    """Layer 2 for one result: the unmatched sentence, and what each workflow its own words name gives."""
    known = registered_workflows()
    gives = [f"{name} gives: {text[:1].lower()}{text[1:]}" for name in workflows_in(item.quote) if name in known
             and (text := produced_text(known[name]))]
    return " ".join([UNMATCHED, *gives])


def is_unmatched(line: str) -> bool:
    """Whether a rendered result line is layer 2."""
    return UNMATCHED in line or UNMATCHED_RESULT in line


def registry_wide(item) -> bool:
    """Whether the reasons the reply may say (`stated_reasons.stated`) hold one about every registered workflow."""
    from .stated_reasons import _form_reasons

    return bool(_form_reasons(item)) or any(entry(key).kind == "registry_wide" for key in item.not_by)


def options_line(decision) -> str:
    """Which registered workflows take the kind of data the request describes (the reading's input types), or "".
    "Take", not "can run": a workflow may also need priors the request does not mention (PANDA's motif and PPI)."""
    if decision is None:
        return ""
    stated = {*decision.guidance_input_artifacts,
              *(artifact for hypothesis in decision.outcome_hypotheses for artifact in hypothesis.outcome.input_artifacts)}
    stated -= {"unknown"}
    names = [workflow_name(action) for action, capability in OUTPUT_CAPABILITIES.items()
             if stated and capability.input_artifacts & stated and produced_text(action)]
    if not names:
        return ""
    return (f"Registered workflows that take the kind of data you described: {', '.join(names)}. "
            "Tell me if one of them gives what you meant, or which result you need.")
