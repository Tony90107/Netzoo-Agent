"""Core decision spec, phase 5b (section 13.3): a count the request gives as candidates, judged in code.

Rounds p2-p4c C45 ("I don't remember whether the proteomics we got back is the 200-protein targeted panel or the
2,000-protein discovery panel"): the check read the 300 miRNAs only, so LIONESS-DRAGON was credited, and the fact
agent asked about the data's format. Code can judge each candidate: 500 features fit LIONESS-DRAGON's 20,000,000
values, 2,300 give 132,192,500. Each candidate is fitted with `method_fitting` (the limits are `workflow_conditions`'
alone); only when the workflows that can run differ does the result wait on it, with each candidate's outcome --
verified, so said with the question. Counts only: candidate setting values are not here (spec 13.6).
"""

from __future__ import annotations

from ..capability_sheet import entry
from ..workflow_conditions import stated_numbers
from .method_conditions import method_fitting
from .request_spans import _span

__all__ = ["count_line", "count_outcome_lines", "count_question", "count_update", "verified_count_alternatives"]

_DIMENSION = {"samples": "sample_count", "features": "feature_count"}
_LABEL = {"sample_count": "samples", "feature_count": "features"}


def verified_count_alternatives(task: str, proposal) -> list[dict]:
    """Each candidate count whose words are in the request and state every candidate number, at least two."""
    found = []
    for item in getattr(getattr(proposal, "conditions", None), "count_alternatives", None) or ():
        span = _span(task, item.quote) if (item.quote or "").strip() else None
        if span is None:
            continue
        words, values = task[span[0]:span[1]], sorted(set(item.values))
        stated = stated_numbers(words)
        if len(values) < 2 or any(value <= 0 or value not in stated for value in values):
            continue
        reading = {"of": item.of, "quote": words, "values": values, "span": list(span)}
        if reading not in found:
            found.append(reading)
    return found


def _inside(span, outer) -> bool:
    return outer[0] <= span[0] and span[1] <= outer[1]


def _base(task: str, method: dict, alternative: dict) -> dict:
    """The method without a stated count of the same kind whose words are inside the candidates' (never settled).

    m3 U06 ("whether 20 or 200 genes remain for the 40 samples"): the 40 samples are inside the words too, and stated.
    """
    base, outer = dict(method), alternative["span"]
    if alternative["of"] == "samples":
        said = _span(task, base["samples_quote"]) if base.get("samples_quote") else None
        if said is not None and _inside(said, outer):
            base.pop("samples", None)
            base.pop("samples_quote", None)
        return base
    if "feature_items" in base:
        kept = [item for item in base["feature_items"] if not _inside(item[:2], outer)]
        for key in ("features", "feature_counts", "feature_items"):
            base.pop(key, None)
        if kept:
            base.update(features=sum(item[2] for item in kept), feature_counts=len(kept), feature_items=kept)
    return base


def _with(base: dict, alternative: dict, value: int) -> dict:
    """The method with one candidate: the samples, or one more data type of that many features."""
    method = dict(base)
    if alternative["of"] == "samples":
        method.update(samples=value, samples_quote=alternative["quote"])
        return method
    counted = base.get("feature_counts", 1 if base.get("features") else 0)
    method.update(features=base.get("features", 0) + value, feature_counts=counted + 1)
    return method


def count_update(task: str, alternatives: list[dict], method: dict, keys: list[str], quote: str,
                 single_result: bool) -> dict | None:
    """The result's wait on a candidate count, or its gap when every candidate rules it out; None when no candidate
    changes what can run.

    `keys`: the result's credited entries before the data size is judged. With several credited results
    (`single_result` False), a count applies to one only when its words overlap that result's words (a count could be
    another dataset's); a result no workflow is credited with does not make several. Returns the fields to set:
    status, delivered_by, method (without the unsettled count), limits, and for a wait the outcomes.
    """
    where = _span(task, quote)
    for alternative in alternatives:
        if not keys or not single_result and (
                where is None or not (where[0] < alternative["span"][1] and alternative["span"][0] < where[1])):
            continue
        base = _base(task, method, alternative)
        base_limits = method_fitting(base, keys)[1]
        outcomes, notes = {}, {}
        for value in alternative["values"]:
            kept, limits, *_rest = method_fitting(_with(base, alternative, value), keys)
            outcomes[str(value)] = kept
            if new := [limit for limit in limits if limit not in base_limits]:
                notes[str(value)] = new[0]
        if len({frozenset(found) for found in outcomes.values()}) > 1:
            return {"status": "needs_fact", "delivered_by": list(dict.fromkeys(k for found in outcomes.values()
                                                                               for k in found)),
                    "method": base, "limits": base_limits, "depends_on": _DIMENSION[alternative["of"]],
                    "outcomes": outcomes, "unknown_quote": alternative["quote"], "by_code": True,
                    "outcome_notes": notes, "file_checked": None}
        if not any(outcomes.values()):
            return {"status": "not_available", "delivered_by": [], "method": base,
                    "limits": [*base_limits, *(f"with {int(value):,}: {note}" for value, note in notes.items())]}
    return None


def _names(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " or " + names[-1]


def count_question(item) -> str:
    """The question of a candidate count (a requirement or a fact): which of the user's numbers is right."""
    return f"Which of these is right: {_names([f'{int(value):,}' for value in item.outcomes])}?"


def count_outcome_lines(outcomes: dict[str, list[str]], notes: dict[str, str]) -> list[str]:
    """What each candidate leads to, from the workflow names code fitted it to and the limit that removed a credit."""
    lines = []
    for value, names in outcomes.items():
        number = f"{int(value):,}"
        if not names:
            lines.append(f"{number}: no registered workflow can do this as asked"
                         + (f" -- {notes[value]}" if value in notes else ""))
        else:
            lines.append(f"{number}: {_names(names)} can do this" + (f" ({notes[value]})" if value in notes else ""))
    return lines


def count_line(item) -> str:
    """The understanding line of a result waiting on a candidate count."""
    outcomes = {value: list(dict.fromkeys(entry(key).workflow for key in keys)) for value, keys in item.outcomes.items()}
    return (f'"{item.quote}" -- depends on a number you gave candidates for ("{item.unknown_quote}"): '
            + "; ".join(count_outcome_lines(outcomes, item.outcome_notes)) + ".")
