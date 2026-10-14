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

Item 4 (2026-10-14): the re-read was given the whole sentence, and read again what it had read. On the recordings
of 2026-10-11 to 10-13, 13 gold requirements in such tails stayed unread; where the re-read ran it quoted the same
result again ("each patient's TF-gene network" beside "emailed to each patient's doctor automatically") or nothing.
Now it is given only the words no quote covers, counted in any script, and every sentence the check left unchecked.
"""

from __future__ import annotations

import re
from functools import lru_cache

from ..capability_sheet import sheet_entries
from ..contracts.capability_check import MAX_SENTENCES
from .capability_check import request_sentences

__all__ = ["MIN_UNREAD_WORDS", "letter_runs", "merge_reread", "reread_passages", "unread_stretches"]

MIN_UNREAD_WORDS = 3
"""Words (`letter_runs`) an unread stretch after a quoted result must hold to be read again. On the 361 distinct
recorded first checks of held-out items (2026-10-11 to 10-13) every gold requirement left unread there sat in a
stretch of 7 or more words; 3 reaches them all, and a short tail such as "and upload them", re-reading 16 checks of
361 (2 would re-read 45 and reach no more). `docs/research-log/coverage-2026-10-14/stretches.py`."""


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


_LETTERS = re.compile(r"[^\W\d_]+")
# Scripts written without spaces between words (kana, CJK ideographs, hangul): two characters count as one word.
_UNSPACED = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]")
_EDGES = " \t\n,;:.!?()[]{}\"'`-\u2013\u2014\uff0c\u3001\u3002\uff1b\uff1a\uff01\uff1f"


def letter_runs(text: str) -> int:
    """Words in any script: a run of letters is one word; in an unspaced script every two characters are one."""
    count = 0
    for run in _LETTERS.findall(text):
        unspaced = len(_UNSPACED.findall(run))
        count += (1 if unspaced < len(run) else 0) + (unspaced + 1) // 2
    return count


def unread_stretches(task: str, check) -> list[tuple[int, int]]:
    """Item 4 (2026-10-14): in each sentence where a result was quoted, the stretches no quote covers after its first
    quote, trimmed of punctuation. What precedes a sentence's first quote is how the sentence asks ("We want",
    "Which method"); what follows it, unquoted, is where a second ask goes unread (heldout14 P1: "..., emailed to each
    patient's doctor automatically")."""
    covered = _covered(task, check)
    results = [quote for item in check.results() if (quote := item.quote.strip().casefold())]
    stretches = []
    for start, end in request_sentences(task):
        if not any(quote in task[start:end].casefold() for quote in results):
            continue
        first = next((index for index in range(start, end) if covered[index]), end)
        index = first
        while index < end:
            if covered[index]:
                index += 1
                continue
            run_end = index
            while run_end < end and not covered[run_end]:
                run_end += 1
            text = task[index:run_end]
            left, right = len(text) - len(text.lstrip(_EDGES)), len(text.rstrip(_EDGES))
            if right > left:
                stretches.append((index + left, index + right))
            index = run_end
    return stretches


def reread_passages(task: str, decision) -> list[str]:
    """The words to read again, in order; [] when the check left nothing unread.

    Which turns are checked is the caller's choice (verdict layer step 1: a run too); r17b MX1-1 left "upload the
    networks to a public repository" unread because a run turn was never re-read. With no result found while routing
    offered workflows, every sentence; otherwise each unread stretch of `MIN_UNREAD_WORDS` or more after a quoted
    result, then each sentence the check left unchecked (after the twelfth, or read as asking but quoting nothing).
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
    tails = [task[start:end] for start, end in unread_stretches(task, check)
             if letter_runs(task[start:end]) >= MIN_UNREAD_WORDS]
    return list(dict.fromkeys([*tails, *check.unchecked]))[:MAX_SENTENCES]


def _span(task: str, quote: str):
    quote = quote.strip()
    start = task.casefold().find(quote.casefold()) if quote else -1
    return None if start < 0 else (start, start + len(quote))


def _overlaps(task: str, quote: str, others) -> bool:
    mine = _span(task, quote)
    return mine is not None and any(
        (theirs := _span(task, other)) is not None and min(mine[1], theirs[1]) > max(mine[0], theirs[0])
        for other in others)


def merge_reread(task: str, check, reread, passages=(), rejected=()):
    """The check with the re-read's new results: those overlapping a result already read are dropped
    (heldout11 VP5q: the whole sentence re-read as one result would have hidden the TF activity
    already found), and a background or methods quote a new result now covers gives way to it.

    Item 4: a new result must quote the words the re-read was given (`passages`); what it quotes elsewhere was the
    first reading's. An unchecked sentence the re-read was given whole is read now -- an empty answer says it asks for
    nothing ("Opinions welcome.") -- unless a quote of the re-read could not be found in the request (`rejected`).
    """
    found = [item.quote for item in check.results()]
    given = [span for passage in passages if (span := _span(task, passage)) is not None]
    new = [item for item in reread.results() if not _overlaps(task, item.quote, found)
           and (not given or _overlaps(task, item.quote, [task[a:b] for a, b in given]))]
    unchecked = list(check.unchecked) if rejected else [item for item in check.unchecked if item not in passages]
    if not new and unchecked == check.unchecked:
        return check
    kept = [item for item in check.requirements
            if item.kind == "result" or not _overlaps(task, item.quote, [result.quote for result in new])]
    requirements = [*kept, *new]
    results = [item for item in requirements if item.kind == "result"]
    full_gap = bool(results) and not unchecked and all(item.status == "not_available" for item in results)
    return check.model_copy(update={"requirements": requirements, "unchecked": unchecked, "full_gap": full_gap})
