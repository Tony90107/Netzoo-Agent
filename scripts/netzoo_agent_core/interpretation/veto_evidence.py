"""What the contract veto may lean on (ROUND-02, collab/ROUND-02-PLAN.md tasks B and C). Pure code.

A veto or a question is only as good as the words behind it. H2 (h4) found three ways they failed: a count the user
gave two ways was judged as one (M38, "either 8 or 15 tumours" read as 8), the toolkit's own name was taken for an
unregistered method (M48), and a question quoted words about another fact (M01, a CpG probe-count doubt asked as
continuous-or-binary). Here:

- `backed_counts`: a stated count is judged only when its words back the one number -- the number is in them, no
  other number stands beside it as an alternative ("8 or 15", "8-15"), and a total code derived names its operands,
  each in its own words. Anything else is set aside (reported, never judged), so every rule that reads the count --
  the count limits and the settings checked against it (SAMBAR's kmax <= samples) -- sees it as unstated.
- `backed_questions`: a question keeps only values its words support; a categorical doubt on words that are a count's
  doubt is that count's question, not a second one. Legacy readings (before ROUND-02, no evidence) keep their
  questions, marked unverified.
- `veto_ledger`: every cell code lists for the chosen workflows, with what was read, why not, and what the judgment
  did with it -- including the cells nothing was read for, and a summary when the reads failed or never ran.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from ..contracts.slim_reading import SlimReading, Stated
from .menu_focus import focus_limits
from .menu_reader import _IDENTIFIER, _norm, request_layout

__all__ = ["backed_counts", "backed_questions", "count_backing", "veto_ledger"]

_COUNTS = ("sample_count", "feature_count", "single_feature_count")


def _numbers(quote: str) -> list[tuple[float, int, int]]:
    """(value, start, end) of each number in the words, less those inside a file name or identifier (rna_85.csv)."""
    inside = [(m.start(), m.end()) for m in _IDENTIFIER.finditer(quote)]
    return [(n.value, n.start, n.end) for n in request_layout(quote).numbers
            if not any(s <= n.start < e for s, e in inside)]


def _side_by_side(quote: str, value: float) -> bool:
    """Whether another number stands beside this one as an alternative: at most one word between them and no other
    number ("8 or 15", "8-15", "8, 15"). Two quantities of different things have their own words between them
    ("6 tumours x 900 genes")."""
    numbers = _numbers(quote)
    for v, start, end in numbers:
        if v != value:
            continue
        for other, o_start, o_end in numbers:
            if other == value:
                continue
            gap = quote[end:o_start] if o_start >= end else quote[o_end:start]
            if len(re.findall(r"[^\W\d_]+", gap)) <= 1 and len(gap) <= 12:
                return True
    return False


def count_backing(fact: Stated) -> str:
    """Why a stated count cannot be judged ("" when its words back it)."""
    value = float(fact.value)
    live = [e for e in fact.evidence if e.role != "corrected"]
    if fact.derived:
        operands = [e for e in live if e.role == "operand"]
        if not operands or any(len(e.values) != 1 or float(e.values[0]) not in [n for n, _s, _e in _numbers(e.quote)]
                               or _side_by_side(e.quote, float(e.values[0])) for e in operands):
            return "a total whose parts are not each in their own words"
        if sum(float(e.values[0]) for e in operands) != value:
            return "a total that is not the sum of its parts"
        return ""
    if fact.evidence and any(e.role == "alternative" for e in live):
        return "the user gave it more than one way"
    quotes = [e.quote for e in live] or [fact.quote]
    if not any(value in [n for n, _s, _e in _numbers(q)] for q in quotes):
        return ("a number not in its own words (a legacy reading: a total without its parts)" if not fact.evidence
                else "a number not in its own words")
    if any(_side_by_side(q, value) for q in quotes):
        return "its words give another number beside it"
    return ""


def backed_counts(slim: SlimReading) -> tuple[SlimReading, list[str]]:
    """The reading with every count its words do not back set aside, and why (ROUND-02 B1)."""
    kept, notes = [], []
    for fact in slim.stated:
        if fact.field == "B6" and fact.name in _COUNTS and fact.value and not fact.values:
            reason = count_backing(fact)
            if reason:
                notes.append(f'{fact.name} {fact.value} not judged: {reason} ("{fact.quote}")')
                continue
        kept.append(fact)
    return (slim.model_copy(update={"stated": kept}) if len(kept) != len(slim.stated) else slim), notes


def _count_doubts(slim: SlimReading) -> dict[str, Stated]:
    """Normalized words -> the count whose doubt they are (alternative evidence; ROUND-02 readings only)."""
    found = {}
    for fact in slim.stated:
        if fact.field == "B6" and fact.values:
            for e in fact.evidence:
                if e.role == "alternative":
                    found[_norm(e.quote)] = fact
    return found


def backed_questions(questions: list, slim: SlimReading) -> tuple[list, list[str]]:
    """The questions whose words back what they ask (ROUND-02 B3), and a note for each one set aside."""
    doubts = _count_doubts(slim)
    counts = {f.name: f for f in slim.stated if f.field == "B6" and f.values}
    kept, notes = [], []
    for q in questions:
        if not q.quote:  # core data never mentioned, a required declaration: no words of the user's to check
            kept.append(q)
            continue
        if q.dimension in ("sample_count", "feature_count"):
            fact = counts.get(q.dimension)
            if fact is None or not fact.evidence:
                in_words = {n for n, _s, _e in _numbers(q.quote)}
                unsupported = [v for v in q.values if float(v) not in in_words]
                kept.append(replace(q, evidence="legacy_unverified") if unsupported else q)
                continue
            options = [e for e in fact.evidence if e.role == "alternative"]
            if not options:
                notes.append(f"question on {q.dimension} set aside: no words give its options")
                continue
            kept.append(replace(q, quote=options[0].quote, derived=fact.derived,
                                belongs_to=options[0].belongs_to, layer_values=tuple(options[0].values)))
            continue
        owner = doubts.get(_norm(q.quote))
        if owner is not None:
            notes.append(f'question on {q.dimension} set aside: "{q.quote}" is the doubt of {owner.name}')
            continue
        kept.append(q)
    return kept, notes


# --- task C: the ledger ---------------------------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class _Cell:
    cell: str
    workflow: str
    kind: str  # control, count, data, condition, method, claim


def _cells(workflows: tuple[str, ...]) -> list[_Cell]:
    """Every cell code lists for the chosen workflows -- what the veto could read and judge, read or not."""
    from ..judgment_defaults import judgment_defaults

    table, limits = judgment_defaults(), focus_limits(tuple(workflows))
    cells = [_Cell(f"setting:{w}.{c}", w, "control") for _key, (w, c, _l) in limits["controls"].items()]
    cells += [_Cell(name, ",".join(workflows), "count") for name in limits["counts"]]
    for w in workflows:
        for need in table.workflow_data.get(w, ((), ()))[1]:
            cells.append(_Cell(f"data:{need}", w, "data"))
        for name in table.b4_conditions.get(w, ()):
            cells.append(_Cell(name if not name.startswith("setting:") else f"declare:{w}.{name.split(':', 1)[1]}",
                               w, "condition"))
    cells += [_Cell(name, ",".join(workflows), "claim") for name in ("claims", "delivery")]
    cells.append(_Cell("method", ",".join(workflows), "method"))
    return list(dict.fromkeys(cells))


def _read(cell: _Cell, slim: SlimReading) -> list[Stated]:
    if cell.kind == "control":
        workflow, control = cell.cell.split(":", 1)[1].split(".", 1)
        return [f for f in slim.stated if f.field == "B5" and f.name == control and f.workflow in (workflow, "")]
    if cell.kind == "count":
        return [f for f in slim.stated if f.field == "B6" and f.name == cell.cell]
    if cell.kind == "data":
        kinds = cell.cell.split(":", 1)[1].split("|")
        return [f for f in slim.data if f.name in kinds or (kinds == ["two_layers"] and f.name == "two_layers")]
    if cell.kind == "condition" and cell.cell.startswith("declare:"):
        control = cell.cell.split(".", 1)[1]
        return [f for f in slim.stated if f.name in (f"setting:{control}", control)]
    return [f for f in slim.stated if f.name == cell.cell]


def _violated(cell: _Cell, name: str, violation) -> bool:
    """Whether a violation is about this cell, by the field it was found in (contract_veto's kinds)."""
    if cell.kind == "count":
        return violation.kind == "B6" or violation.kind == "B5" and "samples" in violation.reason
    if cell.kind == "control":
        return violation.kind in ("B5", "C7") and re.search(rf"(?<![\w]){re.escape(name)}(?![\w])", violation.reason)
    if cell.kind == "data":
        return violation.kind in ("C6", "C8") and any(k in violation.reason for k in name.split("|"))
    if cell.kind == "method":
        return violation.kind == "C5"
    if cell.kind == "claim":
        return violation.kind == {"claims": "C2", "delivery": "C3"}[cell.cell]
    return violation.kind in ("B4", "C4") and violation.reason.startswith(f"{name}=")


def veto_ledger(workflows, status: str, slim: SlimReading | None = None, reports=(), verdict=None,
                set_aside=()) -> dict:
    """The veto's record, one row per cell (ROUND-02 C). status: checked, read_failed, or why it never ran. A cell
    nothing was read for is `not_read` with its reason -- never a pass."""
    workflows = tuple(workflows)
    cells = _cells(workflows) if workflows else []
    if status != "checked" or slim is None:
        return {"status": status, "cells": [{"cell": c.cell, "workflow": c.workflow, "read": "not_run",
                                             "judged": "not_evaluated"} for c in cells]}
    dropped = [line for report in reports for line in getattr(report, "dropped", [])]
    violations = [v for vs in (verdict.violations.values() if verdict else ()) for v in vs]
    asked = {q.dimension for q in (verdict.questions if verdict else ())}
    rows = []
    for c in cells:
        facts = _read(c, slim)
        name = c.cell.split(".", 1)[-1] if c.kind == "control" else c.cell.split(":", 1)[-1]
        why = [line for line in dropped if name and re.search(rf"(?<![\w]){re.escape(name)}(?![\w])", line)]
        aside = [n for n in set_aside if n.startswith(c.cell + " ")]
        row = {"cell": c.cell, "workflow": c.workflow,
               "read": "read" if facts else "dropped" if why else "not_mentioned",
               "values": [f.value or list(f.values) for f in facts], "quotes": [f.quote for f in facts],
               "evidence": [[e.model_dump(exclude_defaults=True) for e in f.evidence] for f in facts],
               "legacy": bool(facts) and not any(f.evidence for f in facts),
               "drop_reasons": why, "set_aside": aside}
        hit = [v for v in violations if v.workflow in c.workflow.split(",") and _violated(c, name, v)]
        row["judged"] = ("violate" if hit else "ask" if c.cell in asked or f"setting:{c.cell.split(':', 1)[-1]}" in asked
                         else "set_aside" if aside else "pass" if facts else "not_evaluated")
        rows.append(row)
    return {"status": status, "cells": rows}
