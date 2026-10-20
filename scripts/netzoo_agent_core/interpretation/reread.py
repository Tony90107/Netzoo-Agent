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
from .capability_check import _full_gap, request_sentences
from .request_facts import merge_facts

__all__ = ["MIN_UNREAD_WORDS", "letter_runs", "merge_reread", "reread_passages", "unread_stretches"]

MIN_UNREAD_WORDS = 3
"""Unread words (`letter_runs`) a stretch beside a quoted result must hold to be read again, before or after it alike.
On the 373 distinct recorded first checks of held-out items (2026-10-11 to 10-14) every gold requirement left unread
sat in a stretch of 8 or more unread words; 3 reaches all 11 and a short ask such as "and upload them", re-reading 76
checks of 373. Most of those are the words before a quote that only say how the sentence asks ("We want to know",
"Is there a method that", 4-6 words): the re-read answers that they ask for nothing, at a median 29 s. Counting only
after the first quote re-read 21, but missed an ask placed first (review of 474a83c).
`docs/research-log/coverage-2026-10-14/stretches.py`."""


@lru_cache(maxsize=1)
def _workflow_names() -> re.Pattern:
    parts = {part for item in sheet_entries().values() if item.workflow for part in item.workflow.split("-")}
    return re.compile(r"\b(?:" + "|".join(sorted(map(re.escape, parts), key=len, reverse=True)) + r")\b", re.I)


def _mask(task: str, quotes) -> list[bool]:
    covered = [False] * len(task)
    folded = task.casefold()
    for quote in quotes:
        quote = quote.strip()
        start = folded.find(quote.casefold()) if quote else -1
        if start >= 0:
            for index in range(start, min(len(task), start + len(quote))):
                covered[index] = True
    return covered


def _covered(task: str, check) -> list[bool]:
    return _mask(task, [item.quote for item in check.requirements])


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


def unread_stretches(task: str, check) -> list[tuple[int, int, int]]:
    """Item 4 (2026-10-14): in each sentence where a result was quoted, the stretches no quote covers, before and after
    its quotes, trimmed of punctuation, as (start, end, unread words). A second ask goes unread beside a quoted one
    (heldout14 P1: "..., emailed to each patient's doctor automatically"), and as well before it as after it (review of
    474a83c: "Align our raw reads to the genome and then build TF-gene networks per sample."). Stretches that only
    words read as context or a methods question separate are one passage, whose unread words are counted (live check
    VP5q: "and also aligns" and "to the genome first" around the context quote "our raw reads")."""
    covered = _covered(task, check)
    in_result = _mask(task, [item.quote for item in check.results()])
    results = [quote for item in check.results() if (quote := item.quote.strip().casefold())]
    stretches = []
    for start, end in request_sentences(task):
        if not any(quote in task[start:end].casefold() for quote in results):
            continue
        index = start
        group = None
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
                piece = (index + left, index + right, letter_runs(text))
                if group is not None and not any(in_result[group[1]:piece[0]]):
                    group = (group[0], piece[1], group[2] + piece[2])
                else:
                    if group is not None:
                        stretches.append(group)
                    group = piece
            index = run_end
        if group is not None:
            stretches.append(group)
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
    tails = [task[start:end] for start, end, words in unread_stretches(task, check) if words >= MIN_UNREAD_WORDS]
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

    Item 4: a new result must quote words the re-read was given (`passages`); what it quotes elsewhere was the first
    reading's. Given a stretch after a quoted result, it must quote words the first reading left unread: a stretch
    can hold a context quote (VP5q), and the data it names is not asked for. Given a whole sentence it may read anew
    what the first reading filed as context or a methods question (Log 406, VN5q). An unchecked sentence the re-read
    was given whole is read now -- an empty answer says it asks for nothing ("Opinions welcome.") -- unless a quote of
    the re-read could not be found in the request (`rejected`).
    """
    found = [item.quote for item in check.results()]
    sentences = {task[start:end].strip() for start, end in request_sentences(task)}
    whole = [span for passage in passages if passage in sentences and (span := _span(task, passage)) is not None]
    tails = [span for passage in passages if passage not in sentences and (span := _span(task, passage)) is not None]
    read = _covered(task, check)

    def given(quote: str) -> bool:
        span = _span(task, quote)
        if span is None:
            return False
        if any(min(span[1], b) > max(span[0], a) for a, b in whole):
            return True
        return any(min(span[1], b) > max(span[0], a) for a, b in tails) and not all(read[span[0]:span[1]])

    new = [item for item in reread.results() if not _overlaps(task, item.quote, found)
           and (not passages or given(item.quote))]
    unchecked = list(check.unchecked) if rejected else [item for item in check.unchecked if item not in passages]
    if not new and unchecked == check.unchecked:
        return check
    kept = [item for item in check.requirements
            if item.kind == "result" or not _overlaps(task, item.quote, [result.quote for result in new])]
    requirements = [*kept, *new]
    results = [item for item in requirements if item.kind == "result"]
    full_gap = _full_gap(results, unchecked)
    # ROUND-03: the facts the new results cite join the record; their conflicts with them.
    facts = merge_facts(check.facts, reread.facts, {fact_id for item in new for fact_id in item.fact_ids})
    added = {item.quote for item in new}
    conflicts = [*check.fact_conflicts, *(found for found in reread.fact_conflicts
                                          if found.result in added and found not in check.fact_conflicts)]
    return check.model_copy(update={"requirements": requirements, "unchecked": unchecked, "full_gap": full_gap,
                                    "facts": facts, "fact_conflicts": conflicts})
