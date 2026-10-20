"""An unexplained data quantity is not evidence that a sample minimum is met.

This detects a reading gap, not the meaning of a number: it never turns gene,
batch or time counts into samples, nor infers a rejection from them. Count
meaning still comes from the single reading and the existing fact record.
"""
from __future__ import annotations

from ..capability_sheet import sheet_entries
from ..contracts.core_decision import FactQuestion
from ..workflow_conditions import conditions_for, stated_numbers
from .request_spans import _locate, scope_applies


def _unexplained_context(check, task, result):
    quotes = []
    for row in check.requirements:
        if row.kind != "context" or not (where := _locate(task, row.quote)):
            continue
        numbers = set(stated_numbers(task[where[0]:where[1]]))
        for fact in check.facts:
            if fact.scope_unverified or not scope_applies(result, fact.applies_to):
                continue
            for evidence in fact.evidence:
                if evidence.result and not scope_applies(result, [evidence.result]):
                    continue
                span = _locate(task, evidence.quote) if evidence.quote else None
                if span is None or not (span[0] < where[1] and where[0] < span[1]):
                    continue
                common = task[max(span[0], where[0]):min(span[1], where[1])]
                values = set()
                for value in [fact.value, *fact.values]:
                    try:
                        values.add(float(value))
                    except (TypeError, ValueError):
                        pass
                numbers -= values & set(stated_numbers(common))
        if numbers and row.quote not in quotes:
            quotes.append(row.quote)
    return quotes


def _confirmed_here(check, task, quote, result, minimum):
    """A verified, applicable sample count inside this very data description settles its minimum.

    Other numbers beside it (e.g. three sequencing batches) need no second sample
    question. A count quoted for another data description cannot settle this one.
    """
    where = _locate(task, quote)
    for fact in check.facts:
        if (fact.property != "sample_count" or fact.state != "stated" or fact.scope_unverified
                or not scope_applies(result, fact.applies_to)):
            continue
        try:
            if float(fact.value) < minimum:
                continue
        except (TypeError, ValueError):
            continue
        for evidence in fact.evidence:
            if evidence.result and not scope_applies(result, [evidence.result]):
                continue
            span = _locate(task, evidence.quote) if evidence.quote else None
            if span and where[0] <= span[0] and span[1] <= where[1]:
                return True
    return False


def unread_sample_conditions(check, task):
    """Questions and audit evidence for a DO that would ignore an unread quantity.

    A sample count already compiled for this result wins. Facts are matched by
    their own quoted evidence, never by a number appearing elsewhere in the task.
    No inference is made about unquantified background or generic method queries.
    """
    if check is None or not task:
        return [], []
    known = sheet_entries()
    missing = []
    for row in check.results():
        if row.status not in ("available", "with_step", "partial") or row.method.get("samples") is not None:
            continue
        quotes = _unexplained_context(check, task, row.quote)
        if not quotes:
            continue
        for key in row.delivered_by:
            entry = known.get(key)
            limits = conditions_for(entry.workflow) if entry else None
            if limits is None or limits.min_samples is None:
                continue
            unexplained = [q for q in quotes if not _confirmed_here(check, task, q, row.quote, limits.min_samples)]
            if not unexplained:
                continue
            item = {"result": row.quote, "workflow": limits.workflow,
                    "minimum_samples": limits.min_samples, "unexplained_context": unexplained}
            if item not in missing:
                missing.append(item)
    if not missing:
        return [], []
    workflows = list(dict.fromkeys(item["workflow"] for item in missing))
    quotes = list(dict.fromkeys(q for item in missing for q in item["unexplained_context"]))
    thresholds = dict((item["workflow"], item["minimum_samples"]) for item in missing)
    many = len({item["result"] for item in missing}) > 1
    question = ("How many independent biological samples are available for each requested result? " if many else
                "How many independent biological samples are available? ")
    question += "; ".join(f"{name}'s input check requires at least {minimum}" for name, minimum in thresholds.items())
    question += ". The sample count in the copied data description has not been verified."
    return [FactQuestion(question=question, user_quote="\n".join(quotes), workflows=workflows,
                         depends_on="sample_count", uncertainty="unread",
                         notes={name: str(minimum) for name, minimum in thresholds.items()})], missing
