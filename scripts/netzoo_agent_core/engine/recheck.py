"""M2 (2026-10-14): when the user's next message changes the run a turn planned or held.

a24b K02: after "Can you run DRAGON on our liver proteomics and phosphoproteomics tables?" started the input wizard,
"I just checked: the phospho data come from a different set of 25 mice than the proteomics." continued it as a wizard
answer -- interactively, as the path of omics_layer_1 -- and the run kept its approval. K09: after the GPU run was
held, "Never mind the GPU - CPU is fine, just use single precision." was answered as guidance and no run was planned.
Such a message is the run, checked again with the whole request (`WorkflowContinuation.recheck`).
"""

from __future__ import annotations

import re

__all__ = ["recheck_task"]

_MARKERS = ("PREVIOUS_ACTION=", "CONFIRMED_", "SELECTED_FIELD=", "CORRECTED_INPUT_", "CARRIED_DISCOVERED_FIELD=")


def _wizard_answer(text: str) -> bool:
    """Whether text answers an input question: a number, a path or file, role=path assignments, custom, yes or no.

    M2 (a24b K02): "I just checked: the phospho data come from a different set of 25 mice than the proteomics."
    continued the input wizard as if it were one, and interactively it became the path of omics_layer_1.
    """
    cleaned = text.strip().strip("'\"。.")
    if not cleaned or cleaned.isdigit() or cleaned.casefold() in {"custom", "y", "yes", "n", "no"}:
        return True
    if "=" in cleaned or len(cleaned.split()) == 1:
        return True
    return bool(re.search(r"(?:^|\s)(?:~|\.{1,2})?/\S|\S/\S|\.(?:tsv|tab|txt|csv|gmt|npy|h5|gz)\b", cleaned, re.I)) \
        and len(cleaned.split()) <= 3


def _is_question(text: str) -> bool:
    return text.rstrip().rstrip("'\")").endswith(("?", "？"))


def recheck_task(conversation, text: str) -> str:
    """The request the run is checked against: the user's last goal, then each message that changed it."""
    prior = next((str(message.content) for message in reversed(conversation)
                  if getattr(message, "type", "") in {"human", "user"}
                  and not any(marker in str(message.content) for marker in _MARKERS)), "")
    prior = prior if prior.startswith("Previous NetZoo goal:") else f"Previous NetZoo goal: {prior}"
    return f"{prior}\nUser follow-up: {text.strip()}"
