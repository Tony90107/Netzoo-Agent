"""Where a quoted passage sits in the request (Log 387), shared by the capability check and its M1 method rules."""

from __future__ import annotations

import re

from ..routing.study_purpose_verify import _locate

__all__: list[str] = []

_TOKEN = re.compile(r"\w+")


def _locate_tokens(task: str, quote: str) -> tuple[int, int] | None:
    """The request passage a near-verbatim quote copies, or None.

    Log 387 smoke run: the model copies the words but trims or rejoins them
    ("We want a classifier using those networks ..." for "then a classifier
    using those networks ..."). A quote stands for the densest passage holding
    at least 70% of its words (and three) in order (difflib blocks, at most 1.5x its length);
    the reply always shows the request's own words.
    """
    from difflib import SequenceMatcher

    wanted = [word.casefold() for word in _TOKEN.findall(quote)]
    if len(wanted) < 3:
        return None
    found = list(_TOKEN.finditer(task))
    words = [match.group().casefold() for match in found]
    blocks = [block for block in SequenceMatcher(None, words, wanted, autojunk=False).get_matching_blocks()
              if block.size]
    best, best_score = None, None
    for first in range(len(blocks)):
        matched = 0
        for last in range(first, len(blocks)):
            start, end = blocks[first].a, blocks[last].a + blocks[last].size
            if end - start > 1.5 * len(wanted):
                break
            matched += blocks[last].size
            score = matched - 0.5 * ((end - start) - matched)
            if matched >= max(3, 0.7 * len(wanted)) and (best_score is None or score > best_score):
                best, best_score = (found[start].start(), found[end - 1].end()), score
    return best


def _span(task: str, quote: str) -> tuple[int, int] | None:
    return _locate(task, quote) or _locate_tokens(task, quote)


def same_words(task: str, a: str, b: str) -> bool:
    """Whether two quotes are, in the request, overlapping words (by containment when they cannot be placed)."""
    if task and (first := _span(task, a)) is not None and (second := _span(task, b)) is not None:
        return first[0] < second[1] and second[0] < first[1]
    a, b = a.casefold().strip(), b.casefold().strip()
    return bool(a and b) and (a in b or b in a)


def scope_applies(result: str, scopes: list[str] | None) -> bool:
    """An already verified scope contains the result's words, or vice versa. None means shared, [] unrelated.

    Do not use the 70%-word recovery rule here: two results differing only in their cohort name are distinct
    owners even when almost all their words match. Both strings have already been located in the request.
    """
    return scopes is None or any(_locate(result, quote) is not None or _locate(quote, result) is not None
                                 for quote in scopes)


def distinct_passages(spans) -> int:
    """How many separate passages the spans quote: spans whose words overlap are one (live attempt-06 T03: "one
    TF-to-gene network per biological sample from pine_bulk.tsv, ..." and "one TF-to-gene network per biological
    sample" are one result read twice, not two)."""
    count, end = 0, -1
    for start, stop in sorted(spans):
        if start >= end:
            count += 1
        end = max(end, stop)
    return count


def distinct_quotes(quotes) -> int:
    """How many separate passages the quotes are, when only their words are known: a quote inside another is it."""
    quotes = [quote.casefold() for quote in dict.fromkeys(quotes)]
    return sum(1 for quote in quotes if not any(quote != other and quote in other for other in quotes))
