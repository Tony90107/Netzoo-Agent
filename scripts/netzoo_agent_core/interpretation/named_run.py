"""Named run in the row's sentence (docs/research-log/excluded-entries-2026-11-01/ROUND-N.md). Off by default:
NETZOO_NAMED_RUN_SENTENCE=on.

`same_run.same_run_holds` (harness repair P2) releases a run a set-apart setting blocks only when a doable row names
the workflow, tested on the row's quote. j11 C34 "Please run PANDA on our 120 ... samples ... to get the aggregate
TF-gene network." was quoted as "to get the aggregate TF-gene network", so the run the user asked for by name was held.
The request sentence holding the row's words is the user's, not the reading's choice of span; an attached question
("Can you set it up that way?", h-set H18) names nothing in its own sentence and stays held.
"""

from __future__ import annotations

import os

from ..method_names import workflows_in
from .request_spans import _span
from .sentence_ownership import request_sentences

__all__ = ["named_in_sentence"]


def named_in_sentence(task: str, quotes: list[str]) -> set[str]:
    """The workflows named in a request sentence overlapping one of the quotes; empty when the flag is off."""
    if os.environ.get("NETZOO_NAMED_RUN_SENTENCE", "off").strip().lower() != "on":
        return set()
    sentences = request_sentences(task)
    found = set()
    for quote in quotes:
        if (span := _span(task, quote)) is None:
            continue
        for start, end in sentences:
            if start < span[1] and span[0] < end:
                found.update(workflows_in(task[start:end]))
    return found
