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

from ..capability_sheet import data_units, entry, sheet_entries
from ..contracts.capability_check import CapabilityCheck, CheckedRequirement, proposal_sentences
from ..routing.study_purpose_verify import _locate

__all__ = [
    "build_capability_check", "request_sentences", "understanding_paragraph", "full_gap_reply", "full_gap_result",
    "with_capability_check_reply", "unavailable_rows", "second_opinion_pairs", "apply_second_opinion",
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


_TYPED = ("scale", "omics_layers", "data_unit", "regulator_kinds", "needs_sign")


def _fitting(keys: list[str], item) -> list[str]:
    """The delivered entries that fit the ask's typed attributes (Logs 388-389).

    Data unit, regulator kinds, sign and layers can rule every entry out -- no
    registered workflow takes single cells, models lncRNA regulators, signs PANDA's
    edges or joins three omics layers. A scale only narrows the list and never
    empties it, because a misread scale must not turn a deliverable result into a gap.
    """
    known = sheet_entries()
    if item.data_unit != "not_stated" and item.data_unit not in data_units():
        return []
    wanted = set(item.regulator_kinds)
    keys = [k for k in keys
            if (known[k].layers is None or item.omics_layers <= known[k].layers)
            and (known[k].regulators is None or wanted <= known[k].regulators)
            and not (item.needs_sign and known[k].signed is False)]
    want = {"per_sample": "sample_specific", "whole_cohort": "aggregate"}.get(item.scale)
    narrowed = [k for k in keys if want is None or want in known[k].granularity]
    return narrowed or keys


def build_capability_check(
    task: str, proposal, verified_claims: frozenset[str] = frozenset(),
) -> tuple[CapabilityCheck, list[dict]]:
    """The verified check for one proposal, and what was rejected.

    A registry-wide reason (no causal proof, no prediction) is kept only when the
    study-purpose reader verified that claim with its cue words: the smoke run cited
    both for a splicing request.

    A passage asked for several times is one requirement; when one reading names an
    entry and another names none (Log 387 dev round: a network and a forecast quoted as
    one sentence twice) it is `partial`, never `available`.
    """
    known = sheet_entries()
    rejected, spans, asks, other = [], [], {}, {}

    def place(quote: str):
        span = _span(task, quote)
        if span is None:
            rejected.append({"quote": quote, "reason": "quote_not_in_request"})
        else:
            spans.append(span)
        return span

    for sentence in proposal_sentences(proposal):
        for kind, quotes in (("context", sentence.has), ("about_methods", sentence.about_methods)):
            for quote in quotes:
                if (span := place(quote)) is not None:
                    other.setdefault(span, kind)
        for item in sentence.asks:
            if (span := place(item.quote)) is None:
                continue
            if sentence.role in ("background", "methods_question") and not (item.delivered_by or item.not_by):
                # The model's own role rules out an ask it matched to nothing (Log 387 dev round 3:
                # "We have expression from 50 kidney samples ..." filed as an ask); an ask it
                # matched to an entry stands. The words still count as read.
                other.setdefault(span, "context" if sentence.role == "background" else "about_methods")
            else:
                asks.setdefault(span, []).append(item)
    requirements = []
    for span, items in asks.items():
        readings = [_fitting([k for k in item.delivered_by if known.get(k) and known[k].kind == "produces"], item)
                    for item in items]
        delivered = list(dict.fromkeys(k for keys in readings for k in keys))
        not_by = list(dict.fromkeys(
            k for item in items for k in item.not_by
            if known.get(k) and (known[k].kind == "near_miss"
                                 or (known[k].kind == "registry_wide" and known[k].claim in verified_claims))))
        status = "partial" if delivered and not all(readings) else _status(delivered)
        attrs = {key: getattr(items[0], key) for key in _TYPED}
        requirements.append(CheckedRequirement(quote=task[span[0]:span[1]], kind="result", status=status,
                                               delivered_by=delivered, not_by=not_by, attrs=attrs))
    requirements += [CheckedRequirement(quote=task[span[0]:span[1]], kind=kind, status="not_checked")
                     for span, kind in other.items() if span not in asks]
    unchecked = [task[s:e].strip() for s, e in request_sentences(task)
                 if not any(a < e and s < b for a, b in spans)]
    results = [item for item in requirements if item.kind == "result"]
    full_gap = bool(results) and not unchecked and all(item.status == "not_available" for item in results)
    return CapabilityCheck(requirements=requirements, unchecked=unchecked, full_gap=full_gap), rejected


def _names(names: list[str]) -> str:
    names = list(dict.fromkeys(names))
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " or " + names[-1]


def _workflows(keys: list[str]) -> str:
    return _names([entry(key).workflow for key in keys])


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
    if item.status == "partial":
        return (f"{quote} -- partly available: {_workflows(item.delivered_by)} gives part of it; no registered "
                "workflow produces the rest.")
    if item.status == "with_step":
        first = entry(item.delivered_by[0])
        return (f"{quote} -- available from {_workflows(item.delivered_by)}'s output plus a step you run "
                f"outside NetZoo: {first.step}")
    reasons = _why_not(item)
    if not reasons:
        return f"{quote} -- not matched to any registered workflow."
    return " ".join([f"{quote} -- not available here: no registered workflow produces this.", *reasons])


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
            rows.append((item.quote, reasons[0] if reasons else "Not matched to any registered workflow."))
    rows += [(sentence, "Not checked against the registered workflows.") for sentence in check.unchecked]
    return rows


def second_opinion_pairs(check: CapabilityCheck, actions: list[str]) -> list[tuple[int, str, list[str]]]:
    """(requirement index, workflow action, its fitting entry ids) to ask about (Log 390).

    Asked when a full gap would clear an exact routing match. Each not-available
    result is paired with each matched workflow, shown with all of its produces
    entries that fit the ask's typed attributes, because a request can need two
    of one workflow's outputs together (dev smoke: KC8's network with per-edge
    significance is DRAGON's network plus its p-values, and each alone was "no").
    A workflow the attributes rule out entirely is never asked about.
    """
    from types import SimpleNamespace

    if not check.full_gap:
        return []
    known = sheet_entries()
    pairs = []
    for index, requirement in enumerate(check.requirements):
        if requirement.kind != "result" or requirement.status != "not_available" or not requirement.attrs:
            continue
        for action in actions:
            produces = [key for key, item in known.items() if item.kind == "produces" and item.action == action]
            fitting = _fitting(produces, SimpleNamespace(**requirement.attrs))
            if fitting:
                pairs.append((index, action, fitting))
    return pairs


def apply_second_opinion(check: CapabilityCheck, pairs: list[tuple[int, str, list[str]]],
                         answers: list[bool]) -> CapabilityCheck:
    """Credit a workflow's fitting entries for every pair answered yes; the gap stands only if none was."""
    requirements = [item.model_copy() for item in check.requirements]
    for (index, _action, keys), yes in zip(pairs, answers):
        if yes:
            item = requirements[index]
            delivered = list(dict.fromkeys([*item.delivered_by, *keys]))
            requirements[index] = item.model_copy(update={
                "delivered_by": delivered, "status": _status(delivered), "second_opinion": True})
    results = [item for item in requirements if item.kind == "result"]
    full_gap = bool(results) and not check.unchecked and all(item.status == "not_available" for item in results)
    return check.model_copy(update={"requirements": requirements, "full_gap": full_gap})
