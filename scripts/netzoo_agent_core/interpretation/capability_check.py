"""Verify the capability check, cover every sentence, and say what was understood (Log 387).

The model proposes, sentence by sentence, what the request asks for and which
capability-sheet entries give it (`graph.capability_check_call`). Code then:

- keeps a requirement only when its quote is in the request (`_locate`);
- decides each result's status from the sheet alone: `available` when a direct
  produces entry gives it, `with_step` when only a with-step entry does,
  `not_available` when none does -- near misses never decide anything;
- covers every request sentence: one that no kept quote overlaps is listed as
  not checked, never silently dropped (the user's Q3, 2026-10-08: an omitted
  requirement that cannot be done turns the rest back into a false yes);
- calls a full gap only when there is at least one result, every result is
  not available, and no sentence was left unchecked.

The reply always opens with what was understood, so a misreading is visible.
"""

from __future__ import annotations

import re

from ..capability_sheet import entry, sheet_entries
from ..contracts.capability_check import CapabilityCheck, CheckedRequirement, proposal_sentences
from ..routing.study_purpose_verify import _locate

__all__ = [
    "build_capability_check", "request_sentences", "understanding_paragraph", "full_gap_reply", "full_gap_result",
    "with_capability_check_reply", "unavailable_rows",
]

_SENTENCE_END = re.compile(r"(?<=[.!?。！？])\s+|\n+")


def request_sentences(task: str) -> list[tuple[int, int]]:
    """(start, end) of each sentence with words in it."""
    spans, start = [], 0
    for match in _SENTENCE_END.finditer(task):
        spans.append((start, match.start()))
        start = match.end()
    spans.append((start, len(task)))
    return [(s, e) for s, e in spans if re.search(r"\w{2,}", task[s:e])]


def _status(delivered: list[str]) -> str:
    levels = {entry(key).level for key in delivered}
    if "direct" in levels:
        return "available"
    return "with_step" if levels else "not_available"


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


def build_capability_check(
    task: str, proposal, verified_claims: frozenset[str] = frozenset(),
) -> tuple[CapabilityCheck, list[dict]]:
    """The verified check for one proposal, and what was rejected.

    A registry-wide reason (no causal proof, no prediction) is kept only when the
    study-purpose reader verified that claim with its cue words: the smoke run cited
    both for a splicing request.

    A passage read several ways (Log 387 smoke run: one quote as context, result and
    methods question at once) is a result when a reading names a sheet entry, or when
    every reading calls it a result; otherwise it is what the readings say it is.
    """
    known = sheet_entries()
    rejected, spans, readings = [], [], {}
    for items in proposal_sentences(proposal):
        for item in items:
            span = _span(task, item.quote)
            if span is None:
                rejected.append({"quote": item.quote, "reason": "quote_not_in_request"})
                continue
            spans.append(span)
            readings.setdefault(span, []).append(item)
    requirements = []
    for span, items in readings.items():
        delivered = list(dict.fromkeys(k for item in items for k in item.delivered_by
                                       if known.get(k) and known[k].kind == "produces"))
        not_by = list(dict.fromkeys(
            k for item in items for k in item.not_by
            if known.get(k) and (known[k].kind == "near_miss"
                                 or (known[k].kind == "registry_wide" and known[k].claim in verified_claims))))
        quote = task[span[0]:span[1]]
        named = any(item.delivered_by or item.not_by for item in items)  # as the model read it, before filtering
        if named or all(item.kind == "result" for item in items):
            requirements.append(CheckedRequirement(quote=quote, kind="result", status=_status(delivered),
                                                   delivered_by=delivered, not_by=not_by))
        else:
            kind = "context" if any(item.kind == "context" for item in items) else "about_methods"
            requirements.append(CheckedRequirement(quote=quote, kind=kind, status="not_checked"))
    unchecked = [task[s:e].strip() for s, e in request_sentences(task)
                 if not any(a < e and s < b for a, b in spans)]
    results = [item for item in requirements if item.kind == "result"]
    full_gap = bool(results) and not unchecked and all(item.status == "not_available" for item in results)
    return CapabilityCheck(requirements=requirements, unchecked=unchecked, full_gap=full_gap), rejected


def _workflows(keys: list[str]) -> str:
    names = list(dict.fromkeys(entry(key).workflow for key in keys))
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " or " + names[-1]


def _lower_first(text: str) -> str:
    """"The motif prior ..." -> "the motif prior ...", but "DRAGON returns ..." stays."""
    return text[:1].lower() + text[1:] if text[1:2].islower() else text


def _why_not(item: CheckedRequirement) -> list[str]:
    reasons = []
    for key in item.not_by:
        found = entry(key)
        reasons.append(found.why_not if found.kind == "registry_wide"
                       else f"{found.workflow} does not give it: {_lower_first(found.why_not)}")
    return list(dict.fromkeys(reasons))[:1]


def _line(item: CheckedRequirement) -> str:
    quote = f'"{item.quote}"'
    if item.status == "available":
        return f"{quote} -- available from {_workflows([k for k in item.delivered_by if entry(k).level == 'direct'])}."
    if item.status == "with_step":
        first = entry(item.delivered_by[0])
        return (f"{quote} -- available from {_workflows(item.delivered_by)}'s output plus a step you run "
                f"outside NetZoo: {first.step}")
    return " ".join([f"{quote} -- not available here: no registered workflow produces this.", *_why_not(item)])


def understanding_paragraph(check: CapabilityCheck) -> str | None:
    """What the request was understood to ask for, one line per result, plus the unchecked sentences."""
    results = check.results()
    if not results and not check.unchecked:
        return None
    lines = ["What I understood you are asking for:"] if results else []
    lines += [f"{index}. {_line(item)}" for index, item in enumerate(results, 1)]
    lines += [f'Not checked against the registered workflows: "{sentence}"' for sentence in check.unchecked]
    return "\n".join(lines)


def full_gap_reply(check: CapabilityCheck) -> str:
    many = len(check.results()) > 1
    return "\n\n".join([
        understanding_paragraph(check) or "",
        (f"No registered workflow produces {'these' if many else 'this'}, so none is offered as the way to get "
         f"{'them' if many else 'it'}."),
        "No files were inspected and no analysis ran.",
    ])


def full_gap_result(state, reply) -> dict | None:
    """The whole reply when nothing registered produces what was asked, else None."""
    from ..contracts import TaskDecision

    check = TaskDecision.model_validate(state["decision"]).capability_check
    return reply(full_gap_reply(check), "capability_check_gap") if check is not None and check.full_gap else None


def with_capability_check_reply(result: dict, state, reply) -> dict:
    """Open any other reply with what was understood (the full gap has its own reply)."""
    from ..contracts import TaskDecision

    decision = TaskDecision.model_validate(state["decision"])
    check = decision.capability_check
    if check is None or check.full_gap or result.get("reply_kind") in (None, "execution"):
        return result
    paragraph = understanding_paragraph(check)
    if paragraph is None:
        return result
    text = str(result["messages"][-1].content)
    return {**reply(f"{paragraph}\n\n{text}", result["reply_kind"]),
            **{key: value for key, value in result.items() if key not in ("messages", "reply_kind")}}


def unavailable_rows(check: CapabilityCheck) -> list[tuple[str, str]]:
    """(label, reason) for each result not available here and each unchecked sentence."""
    rows = []
    for item in check.results():
        if item.status == "not_available":
            reasons = _why_not(item)
            rows.append((item.quote, reasons[0] if reasons else "No registered workflow produces this."))
    rows += [(sentence, "Not checked against the registered workflows.") for sentence in check.unchecked]
    return rows
