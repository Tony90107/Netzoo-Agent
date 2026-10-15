"""M2 (2026-10-14): when the user's next message changes the run a turn planned or held.

a24b K02: after "Can you run DRAGON on our liver proteomics and phosphoproteomics tables?" started the input wizard,
"I just checked: the phospho data come from a different set of 25 mice than the proteomics." continued it as a wizard
answer -- interactively, as the path of omics_layer_1 -- and the run kept its approval. K09: after the GPU run was
held, "Never mind the GPU - CPU is fine, just use single precision." was answered as guidance and no run was planned.
Such a message is the run, checked again with the whole request (`WorkflowContinuation.recheck`).
"""

from __future__ import annotations

import re

from ..settings import INPUT_ROLE_FIELDS, OUTPUT_ROLE_FIELDS

__all__ = ["recheck_task"]

_MARKERS = ("PREVIOUS_ACTION=", "CONFIRMED_", "SELECTED_FIELD=", "CORRECTED_INPUT_", "CARRIED_DISCOVERED_FIELD=")
_EXTENSIONS = r"(?:tsv|tab|txt|csv|gmt|npy|h5|hdf|gz)"
# A path from a root may hold spaces, typed or escaped by a terminal drop ("/Users/me/LLM AGENT/expr.tsv",
# "LLM\ AGENT"); it ends at the first data file name, so words after it are not part of it.
_SPACED_PATH = r"(?:~|\.{1,2})?/[^\n,;=\"']*?\." + _EXTENSIONS + r"(?=$|[\s,;])"
_VALUE = r'''(?:"[^"\n]+"|'[^'\n]+'|''' + _SPACED_PATH + r'''|[^\s,;="']+)'''
_INPUT_ASSIGNMENT = re.compile(
    r"(?:" + "|".join(sorted(INPUT_ROLE_FIELDS | OUTPUT_ROLE_FIELDS)) + r")\s*=\s*" + _VALUE,
    re.I,
)


def _wizard_answer(text: str, plan=None) -> bool:
    """Whether text answers an input question: a number, a path or file, role=path assignments, custom, yes or no.

    M2 (a24b K02): "I just checked: the phospho data come from a different set of 25 mice than the proteomics."
    continued the input wizard as if it were one, and interactively it became the path of omics_layer_1.
    """
    cleaned = text.strip().strip("'\"。.")
    if not cleaned or cleaned.isdigit() or cleaned.casefold() in {"custom", "y", "yes", "n", "no"}:
        return True
    if "=" in cleaned:
        # Consume the entire answer, not just a path assignment inside a new scientific constraint.
        remaining = text.strip().rstrip("。.")
        while remaining:
            match = _INPUT_ASSIGNMENT.match(remaining)
            if match is None:
                return False
            remaining = remaining[match.end():]
            if remaining and not re.match(r"[\s,;]", remaining):
                return False
            remaining = remaining.lstrip(" \t\r\n,;")
        return True
    if plan is not None and "lioness_mode" in plan.missing_inputs:
        from workflow_registry import ACTION_DEFINITIONS, registered_actions_for_family

        choices = {name.casefold() for action in registered_actions_for_family("lioness")
                   for name in (action, ACTION_DEFINITIONS[action].workflow)}
        if cleaned.casefold() in choices:
            return True
    match = re.fullmatch(r"(?:use\s+)?(" + _VALUE + r")(?:\s+please)?", text.strip().rstrip("。."), re.I)
    if match is None:
        return False
    path = match.group(1).strip("'\"")
    return bool(re.search(r"[/\\]|\." + _EXTENSIONS + "$", path, re.I))


def _is_question(text: str) -> bool:
    return text.rstrip().rstrip("'\")").endswith(("?", "？"))


def recheck_task(conversation, text: str) -> str:
    """The request the run is checked against: the user's last goal, then each message that changed it."""
    prior = next((str(message.content) for message in reversed(conversation)
                  if getattr(message, "type", "") in {"human", "user"}
                  and not any(marker in str(message.content) for marker in _MARKERS)), "")
    prior = prior if prior.startswith("Previous NetZoo goal:") else f"Previous NetZoo goal: {prior}"
    return f"{prior}\nUser follow-up: {text.strip()}"
