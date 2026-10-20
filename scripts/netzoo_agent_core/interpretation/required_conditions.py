"""ROUND-10 (collab/ROUND-10-PLAN.md): a quantity condition the request does not state is said, never taken as met.

A workflow's sample minimum, output size cap and gene/sample relation (`workflow_conditions`) are its contract,
whatever the reading wrote. When the request states the counts, code judges them (`method_fitting`); when it gives
candidates, code weighs each (`count_update`). When it states nothing, the condition is still there: a run meets it
only through the input preflight, which counts from the files (step 0: every minimum and cap is enforced there), and
an answer about whether a workflow can do it says the condition instead of implying it is met. Step 0 on 383
recorded DO calls: 36 answers stated no count for a condition like this.
"""
from __future__ import annotations

from ..capability_sheet import entry
from ..workflow_conditions import conditions_for
from .needed_facts import check_unknowns
from .request_spans import scope_applies

__all__ = ["quantity_note"]

_RELATIONS = {"features>samples": "more genes than samples"}
"""How each registered relation (`workflow_conditions._RELATIONS`) is said."""


def _known(check, item) -> set[str]:
    """The quantities read for this result: on its method, in the shared record, or as candidates."""
    found = set()
    if item.method.get("samples") is not None:
        found.add("samples")
    if item.method.get("features") is not None:
        found.add("features")
    for fact in check.facts:
        if fact.scope_unverified or not scope_applies(item.quote, fact.applies_to):
            continue
        if fact.property == "sample_count":
            found.add("samples")
        elif fact.property == "feature_count":
            found.add("features")
    found.update({"samples": "samples", "features": "features"}[alternative["of"]]
                 for alternative in check.count_alternatives)
    if any(about == "sample_count" for about, _said, _domain in check_unknowns(check, item.quote)):
        found.add("samples")
    return found


def quantity_note(check, item) -> str:
    """The sentence saying each quantity condition of the result's workflows that the request does not state; empty
    when it states every count they need, or the result is not given."""
    if item.status not in ("available", "with_step", "partial") or check.provisional:
        return ""
    known = _known(check, item)
    parts = []
    for name in dict.fromkeys(entry(key).workflow for key in item.delivered_by if entry(key)):
        limits = conditions_for(name)
        if limits is None:
            continue
        if limits.min_samples is not None and "samples" not in known:
            parts.append(f"{name} needs at least {limits.min_samples} samples")
        if limits.max_values is not None and not {"samples", "features"} <= known:
            parts.append(f"{name}'s output is capped at {limits.max_values:,} values ({limits.size_formula})")
        if limits.relation is not None and not {"samples", "features"} <= known:
            parts.append(f"{name} needs {_RELATIONS.get(limits.relation_name, limits.relation_name)}")
    if not parts:
        return ""
    return (" Not stated in your request: " + "; ".join(parts)
            + " -- checked against your files before any run.")
