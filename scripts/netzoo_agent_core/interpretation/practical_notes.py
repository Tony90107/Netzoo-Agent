"""What to do or expect before running a workflow (Log 320).

TEST_PROMPTS Test 3 (2026-10-03) got CONDOR without being told that a PANDA
network's negative weights must be thresholded first; Tests 2 and 10 got
LIONESS-PANDA without its cost of one PANDA run per sample. The notes are
registry data (`WORKFLOW_PRACTICAL_NOTES`); the request is read only for its
own sample count, which is quoted back ("for your 90 patients"), never
mapped to anything.
"""

from __future__ import annotations

import re

from workflow_registry import WORKFLOW_PRACTICAL_NOTES, WORKFLOW_PRACTICAL_POINTS

__all__ = ["practical_notes"]

_COUNT = re.compile(
    r"\b(\d{1,6})\s+(?:[A-Za-z-]+\s+){0,2}"
    r"(samples?|patients?|individuals?|subjects?|donors?|participants?|tumou?rs?|biops(?:y|ies))\b",
    re.I,
)
_BASES = {"run_lioness_panda": "PANDA", "run_lioness_puma": "PUMA", "run_lioness_dragon": "DRAGON"}


def practical_notes(action: str, task: str = "", *, short: bool = False) -> list[str]:
    """The registry's notes for one workflow; `short` gives the card's one-line form."""
    notes = ([WORKFLOW_PRACTICAL_POINTS[action]] if short and action in WORKFLOW_PRACTICAL_POINTS
             else [] if short else list(WORKFLOW_PRACTICAL_NOTES.get(action, ())))
    match = _COUNT.search(task or "") if action in _BASES else None
    runs = ""
    if match and int(match.group(1)) > 1:
        count = int(match.group(1))
        runs = f" (for your {count} {match.group(2)}, {count + 1} {_BASES[action]} runs)"
    return [note.replace("{runs}", runs) for note in notes]
