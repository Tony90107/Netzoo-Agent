"""Bind a misplaced ask to the sentence containing its exact quote."""
from __future__ import annotations

import re

from .request_spans import _locate

_SENTENCE_END = re.compile(r"(?<=[.!?。！？])\s+|\n+")


def request_sentences(task: str) -> list[tuple[int, int]]:
    """(start, end) of each sentence with words in it; also the provider's s1/s2 boundaries."""
    spans, start = [], 0
    for match in _SENTENCE_END.finditer(task):
        spans.append((start, match.start()))
        start = match.end()
    spans.append((start, len(task)))
    return [(s, e) for s, e in spans if re.search(r"\w{2,}", task[s:e])]


def background_owner(task, quote, source, sentences, spans):
    """A different, explicitly background sentence owns this quote, or None.

    Do not infer intent from vocabulary or fuzzy quote recovery. Cross-sentence
    quotes and missing sentence readings keep the existing interpretation.
    """
    if not quote.strip():
        return None
    owners = [index for index, (start, end) in enumerate(spans[:len(sentences)])
              if _locate(task[start:end], quote) is not None]
    if len(owners) != 1:
        return None
    owner = owners[0]
    return owner if owner != source and sentences[owner].role == "background" else None


def owned_sentences(task, sentences):
    """Return an immutable correction of cross-container background asks and its audit record."""
    spans = request_sentences(task)
    asks, contexts = [list(s.asks) for s in sentences], [list(s.has) for s in sentences]
    rejected = []
    for source, sentence in enumerate(sentences):
        for item in sentence.asks:
            # A supported or explicitly refused result remains an ask even if
            # the sentence-role reading disagrees (archived C47: risk drivers).
            if item.delivered_by or item.not_by:
                continue
            owner = background_owner(task, item.quote, source, sentences, spans)
            if owner is None:
                continue
            asks[source].remove(item)
            if item.quote not in contexts[owner]:
                contexts[owner].append(item.quote)
            rejected.append({"quote": item.quote, "reason": "ask_in_other_background_sentence",
                             "source_sentence": source + 1, "owner_sentence": owner + 1})
    return [s.model_copy(update={"asks": asks[i], "has": contexts[i]})
            for i, s in enumerate(sentences)], rejected
