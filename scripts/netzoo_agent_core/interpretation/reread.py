"""Which words of a request the capability check left unread, for a second reading (Log 406).

Two code-visible gaps, both from heldout11-13 recordings where an unsupported request was never
refused:

- the check's own model read every sentence and found no result, while routing offered workflows
  (heldout11 VN5q, heldout12 QN1: a result asked as "Is there a method that ..." was filed as a
  question about methods, and four TF-network workflows were said to "all fit");
- a sentence where the check quoted one result leaves a long stretch unquoted (heldout13 P1:
  "uploaded automatically to a public database when they are done"; heldout11 VP1: "a web
  dashboard where clinicians can browse them interactively") -- the unsupported half was omitted.

A question about how a named registered workflow works is not re-read: that workflow's
description answers it.
"""

from __future__ import annotations

import re
from functools import lru_cache

from ..capability_sheet import sheet_entries
from .capability_check import request_sentences

__all__ = ["MIN_UNQUOTED_WORDS", "merge_reread", "reread_passages"]

MIN_UNQUOTED_WORDS = 5
"""Unquoted words of four or more letters a quoted sentence must keep to be re-read. On the
heldout11-13 recordings, requests whose unquoted rest was data or framing ("We have ... plus",
"Sorry, I meant") kept at most 2; the omitted requests kept 7."""

_WORD = re.compile(r"[A-Za-z][A-Za-z-]{3,}")


@lru_cache(maxsize=1)
def _workflow_names() -> re.Pattern:
    parts = {part for item in sheet_entries().values() if item.workflow for part in item.workflow.split("-")}
    return re.compile(r"\b(?:" + "|".join(sorted(map(re.escape, parts), key=len, reverse=True)) + r")\b", re.I)


def _covered(task: str, check) -> list[bool]:
    covered = [False] * len(task)
    folded = task.casefold()
    for item in check.requirements:
        quote = item.quote.strip()
        start = folded.find(quote.casefold()) if quote else -1
        if start >= 0:
            for index in range(start, min(len(task), start + len(quote))):
                covered[index] = True
    return covered


def reread_passages(task: str, decision) -> list[str]:
    """The request sentences to read again, in order; [] when the check left nothing unread.

    Which turns are checked is the caller's choice (verdict layer step 1: a run too); r17b MX1-1 left "upload the
    networks to a public repository" unread because a run turn was never re-read.
    """
    check = decision.capability_check
    if check is None or check.unconfirmed() or check.full_gap:
        return []
    sentences = [(start, end) for start, end in request_sentences(task)]
    if not check.results():
        offered = decision.matched_actions or decision.hypothesis_actions or decision.recommended_actions
        named = any(_workflow_names().search(item.quote) for item in check.requirements if item.kind == "about_methods")
        if not offered or named:
            return []
        return [task[start:end].strip() for start, end in sentences]
    covered = _covered(task, check)
    results = [item.quote.strip().casefold() for item in check.results()]
    passages = []
    for start, end in sentences:
        text = task[start:end]
        if not any(quote and quote in text.casefold() for quote in results):
            continue
        rest = "".join(" " if covered[start + offset] else char for offset, char in enumerate(text))
        if len(_WORD.findall(rest)) >= MIN_UNQUOTED_WORDS:
            passages.append(text.strip())
    return passages


def _span(task: str, quote: str):
    quote = quote.strip()
    start = task.casefold().find(quote.casefold()) if quote else -1
    return None if start < 0 else (start, start + len(quote))


def _overlaps(task: str, quote: str, others) -> bool:
    mine = _span(task, quote)
    return mine is not None and any(
        (theirs := _span(task, other)) is not None and min(mine[1], theirs[1]) > max(mine[0], theirs[0])
        for other in others)


def merge_reread(task: str, check, reread):
    """The check with the re-read's new results: those overlapping a result already read are dropped
    (heldout11 VP5q: the whole sentence re-read as one result would have hidden the TF activity
    already found), and a background or methods quote a new result now covers gives way to it."""
    found = [item.quote for item in check.results()]
    new = [item for item in reread.results() if not _overlaps(task, item.quote, found)]
    if not new:
        return check
    kept = [item for item in check.requirements
            if item.kind == "result" or not _overlaps(task, item.quote, [result.quote for result in new])]
    requirements = [*kept, *new]
    results = [item for item in requirements if item.kind == "result"]
    full_gap = bool(results) and not check.unchecked and all(item.status == "not_available" for item in results)
    return check.model_copy(update={"requirements": requirements, "full_gap": full_gap})
