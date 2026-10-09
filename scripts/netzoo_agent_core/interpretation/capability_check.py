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
    "implied_actions",
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


_TYPED = ("scale", "omics_layers", "data_unit", "regulator_kinds", "needs_sign", "input_network")


def _fitting(keys: list[str], item) -> list[str]:
    """The delivered entries that fit the ask's typed attributes (Logs 388-389).

    Data unit, regulator kinds, sign, layers and input network can rule every entry
    out -- no registered workflow takes single cells, models lncRNA regulators, signs
    PANDA's edges, joins three omics layers, or partitions a gene-gene network. A scale only narrows the list and never
    empties it, because a misread scale must not turn a deliverable result into a gap.
    """
    known = sheet_entries()
    if item.data_unit != "not_stated" and item.data_unit not in data_units():
        return []
    wanted = set(item.regulator_kinds)
    keys = [k for k in keys
            if (known[k].layers is None or item.omics_layers <= known[k].layers)
            and (known[k].regulators is None or wanted <= known[k].regulators)
            and not (item.needs_sign and known[k].signed is False)
            and (known[k].input_network is None or getattr(item, "input_network", "none") in ("none", known[k].input_network))]
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
        blank = not any(item.delivered_by or item.not_by for item in items)
        requirements.append(CheckedRequirement(quote=task[span[0]:span[1]], kind="result", status=status,
                                               delivered_by=delivered, not_by=not_by, attrs=attrs, blank=blank))
    requirements += [CheckedRequirement(quote=task[span[0]:span[1]], kind=kind, status="not_checked")
                     for span, kind in other.items() if span not in asks]
    # Log 392 (B): the schema has one field per numbered sentence, so a sentence the model
    # gave a background or methods-question role was read even when it quoted nothing
    # (TEST_PROMPTS r9: such background sentences were listed as "Not checked").
    read = {index for index, sentence in enumerate(proposal_sentences(proposal))
            if sentence.role in ("background", "methods_question")}
    unchecked = [task[s:e].strip() for index, (s, e) in enumerate(request_sentences(task))
                 if index not in read and not any(a < e and s < b for a, b in spans)]
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


def _line(item: CheckedRequirement, provisional: bool = False) -> str:
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
    if provisional and item.status == "not_available":
        return f"{quote} -- {PROVISIONAL_NOT_MATCHED[0].lower()}{PROVISIONAL_NOT_MATCHED[1:]}"
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
    lines += [f"{index}. {_line(item, check.provisional)}" for index, item in enumerate(results, 1)]
    lines += [f'Not checked against the registered workflows: "{sentence}"' for sentence in check.unchecked]
    if check.provisional:
        lines.append(PROVISIONAL_NOTE)
    return "\n".join(lines)


def full_gap_reply(check: CapabilityCheck, *, with_note: bool = False) -> str:
    """The full-gap reply; `with_note` when an outside-step note follows (Log 393).

    TEST_PROMPTS r10 test4: "none is offered" read against the note's own "a registered
    route: pseudo-bulk ... then PANDA". The note's route is a different request (bulk, or a
    method not registered here), so the sentence says "as you asked" and points to it.
    """
    many = len(check.results()) > 1
    them, it = ("these", "them") if many else ("this", "it")
    closing = (f"No registered workflow produces {them} as you asked {it}, so none is offered for {it} as asked. "
               "The note below describes the closest route." if with_note else
               f"No registered workflow produces {them}, so none is offered as the way to get {it}.")
    return "\n\n".join([
        understanding_paragraph(check) or "",
        closing,
        "No files were inspected and no analysis ran.",
    ])


# Log 401: what the backup model found is said as unconfirmed, and nothing is withdrawn for it.
PROVISIONAL_NOT_MATCHED = "The backup check matched no registered workflow to this (not confirmed)."
PROVISIONAL_NOTE = (
    "The usual capability check could not run this turn, so a backup model read the request; the lines above "
    "are not confirmed, and the methods below were not removed for them."
)

UNAVAILABLE_NOTE = (
    "This turn could not be checked against what the registered workflows produce, so the methods "
    "below have not been confirmed to give what you asked for."
)


def full_gap_result(state, reply) -> dict | None:
    """The whole reply when nothing registered produces what was asked, else None."""
    from ..contracts import TaskDecision

    from ..llm import latest_user_task
    from .outside_steps import with_outside_steps

    decision = TaskDecision.model_validate(state["decision"])
    check = decision.capability_check
    if check is None or not check.full_gap:
        return None
    # Log 392 (A): the verified outside-step notes (Log 320: SCORPION's pseudo-bulk route,
    # SPIDER, ALPACA) stay; TEST_PROMPTS r9 tests 4 and 8 lost them to the full gap.
    task = latest_user_task(state.get("messages") or [])
    plain = full_gap_reply(check)
    if with_outside_steps(plain, decision, task) != plain:
        return reply(with_outside_steps(full_gap_reply(check, with_note=True), decision, task), "capability_check_gap")
    return reply(plain, "capability_check_gap")


def with_capability_check_reply(result: dict, state, reply) -> dict:
    """Open any other reply with what was understood (the full gap has its own reply)."""
    from ..contracts import TaskDecision

    decision = TaskDecision.model_validate(state["decision"])
    check = decision.capability_check
    if check is None or check.full_gap or result.get("reply_kind") in (None, "execution"):
        return result
    paragraph = UNAVAILABLE_NOTE if check.unavailable else understanding_paragraph(check)
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
            reasons = [PROVISIONAL_NOT_MATCHED] if check.provisional else _why_not(item)
            rows.append((item.quote, reasons[0] if reasons else "Not matched to any registered workflow."))
    rows += [(sentence, "Not checked against the registered workflows.") for sentence in check.unchecked]
    return rows


def implied_actions(requirement: CheckedRequirement) -> list[str]:
    """The workflows a blank verdict's own typed attributes point to (Log 397).

    Only attributes that single out a few workflows count: two or more omics layers
    (the DRAGON family), a sign (GIRAFFE), miRNA regulators (the PUMA family) and a
    regulator-gene input network (CONDOR). TF regulators or a scale point to most of
    the registry and imply nothing, so a blank verdict on, say, copy-number calling has
    no workflow to ask and its gap stands. heldout6 NC6: a metabolite-lipid network
    came back blank with routing failed, omics_layers=2, and was gapped 3/3.
    """
    from types import SimpleNamespace

    attrs = SimpleNamespace(**requirement.attrs) if requirement.attrs else None
    if attrs is None or requirement.status != "not_available" or not requirement.blank:
        return []
    known = sheet_entries()
    def picks(item) -> bool:
        return ((attrs.omics_layers >= 2 and item.layers is not None)
                or (attrs.needs_sign and item.signed is True)
                or ("mirna" in attrs.regulator_kinds and item.regulators is not None and "mirna" in item.regulators)
                or (getattr(attrs, "input_network", "none") == "regulator_gene"
                    and item.input_network == "regulator_gene"))
    keys = [key for key, item in known.items() if item.kind == "produces" and picks(item)]
    return list(dict.fromkeys(known[key].action for key in _fitting(keys, attrs)))


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
