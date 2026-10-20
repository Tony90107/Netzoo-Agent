"""The slim reading's facts with their evidence (ROUND-02 task A, collab/ROUND-02-PLAN.md): what each number and each
data statement counts, which statements a later one corrected, and what code derived. `slim_reader` reads; this module
assembles what was read into `Stated` facts that keep their words, so the veto can tell a number the user gave from
one code computed, and one data object's versions from different objects' counts.
"""

from __future__ import annotations

from ..contracts.slim_reading import Evidence, Stated
from .menu_reader import Layout, ReadReport, _norm, _verified, quote_in

__all__ = ["_count_facts", "_data_facts"]


def _corrections(entries: list[dict], same) -> dict[int, int]:
    """{earlier index: later index} for each `corrects` code can verify (ROUND-02 A2): the entry it names exists, is
    about the same thing (`same(earlier, later)`), and its words come earlier in the request. A correction that fails
    any check is dropped and both statements stay (a conflict is kept, never resolved by picking one)."""
    found = {}
    for later, entry in enumerate(entries):
        target = entry.get("corrects")
        if not isinstance(target, int) or not 1 <= target <= len(entries) or target - 1 == later:
            continue
        earlier = target - 1
        if entries[earlier].get("_start", -1) < entry.get("_start", -1) and same(entries[earlier], entry) \
                and earlier not in found:
            found[earlier] = later
    return found

def _data_facts(raw: list, task: str, layout: Layout, table, report: ReadReport) -> list[Stated]:
    """A3 with its evidence (ROUND-02 A2): a verified correction retires the earlier statement; two live statements
    of one kind that disagree are a conflict, kept as unsure (never one picked); unsure never counts as lacking."""
    entries = []
    for index, entry in enumerate(raw):
        kind = str(entry.get("kind") or "")
        if kind not in table.dimensions["data_available"].values:
            report.dropped.append(f"data[{index}]: {kind!r} is no data kind")
            continue
        quote = _verified(entry.get("quote"), task, f"data[{index}]", report)
        if not quote:
            continue
        status = entry.get("status") if entry.get("status") in ("has", "lacks", "unsure") else "has"
        target = str(entry.get("input_for") or "").strip()
        if target and target not in layout.names:
            report.dropped.append(f"data[{index}]: input_for {target!r} is no registered name in the request")
            target = ""
        entries.append({**entry, "kind": kind, "status": status, "quote": quote, "input_for": target,
                        "_start": _norm(task).find(_norm(quote))})
    retired = _corrections(entries, lambda a, b: a["kind"] == b["kind"])
    facts: dict[str, Stated] = {}
    for index, entry in enumerate(entries):
        if index in retired:
            continue
        kind, status = entry["kind"], entry["status"]
        evidence = [Evidence(quote=entries[e]["quote"], values=[entries[e]["status"]], role="corrected",
                             corrected_by=entry["quote"]) for e, later in retired.items() if later == index]
        evidence.append(Evidence(quote=entry["quote"], values=[status]))
        if kind not in facts:
            facts[kind] = Stated(field="A3", name=kind, value=status, quote=entry["quote"], workflow=entry["input_for"],
                                 evidence=evidence)
            continue
        known = facts[kind]
        merged = [*known.evidence, *evidence]
        if known.value != status:
            report.filled.append(f"data {kind}: {known.value} and {status} both stated, no verified correction -> unsure")
            known = known.model_copy(update={"value": "unsure"})
        facts[kind] = known.model_copy(update={"evidence": merged, "workflow": known.workflow or entry["input_for"]})
    return list(facts.values())

def _count_facts(raw: list, task: str, counts: tuple[str, ...], report: ReadReport) -> list[Stated]:
    """B6 with its evidence (ROUND-02 A1). Each number keeps its own words and the data it counts: versions of one
    data object are alternatives (never added), different objects are operands of a total code derives (kept with its
    formula, never passed off as words the user said), a number restated is counted once, and a verified correction
    retires the earlier statement."""
    entries = []
    for index, entry in enumerate(raw):
        quote = _verified(entry.get("quote"), task, f"focus.counts[{index}]", report)
        numbers = sorted({int(v) for v in entry.get("values") or []}) or (
            [int(entry["value"])] if entry.get("value") is not None else [])
        if not quote or not numbers:
            continue
        owner = str(entry.get("belongs_to") or "").strip()
        if owner and not quote_in(owner, task):
            report.dropped.append(f"focus.counts[{index}]: belongs_to {owner!r} is not the request's words")
            owner = ""
        what = "samples" if entry.get("what") == "samples" else "features"
        # The layer keys the data object (a restated count, with or without its file name, stays one object);
        # belongs_to names it in the user's words and keys it only when no layer is given.
        layer = str(entry.get("layer") or "").strip().casefold()
        key = "" if what == "samples" else layer or _norm(owner) or "features"
        entries.append({**entry, "what": what, "numbers": numbers, "quote": quote, "owner": owner or layer,
                        "key": key, "corrects": entry.get("corrects"), "_start": _norm(task).find(_norm(quote))})
    retired = _corrections(entries, lambda a, b: (a["what"], a["key"]) == (b["what"], b["key"]))
    live = [e for i, e in enumerate(entries) if i not in retired]

    def corrected(later: dict) -> list[Evidence]:
        return [Evidence(quote=entries[i]["quote"], values=list(map(str, entries[i]["numbers"])),
                         belongs_to=entries[i]["owner"], role="corrected", corrected_by=later["quote"])
                for i, j in retired.items() if entries[j] is later]

    facts = []
    samples = [e for e in live if e["what"] == "samples"]
    if "sample_count" in counts and samples:
        doubtful = [e for e in samples if len(e["numbers"]) >= 2]
        failed = any(e.get("corrects") is not None for e in samples) and len({e["numbers"][0] for e in samples}) > 1
        if failed and not doubtful:
            # A correction code could not verify: both statements stand as a conflict, never one picked (A2).
            numbers = sorted({e["numbers"][0] for e in samples})
            facts.append(Stated(field="B6", name="sample_count", quote=samples[-1]["quote"], values=list(map(str, numbers)),
                                evidence=[Evidence(quote=e["quote"], values=list(map(str, e["numbers"])),
                                                   belongs_to=e["owner"], role="alternative") for e in samples]))
            report.filled.append("sample_count: a correction that could not be verified -> both numbers kept")
            samples = []
    if "sample_count" in counts and samples:
        chosen = doubtful[0] if doubtful else max(samples, key=lambda e: e["numbers"][0])
        if not doubtful and len({e["numbers"][0] for e in samples}) > 1:
            report.filled.append(f"sample_count: several numbers stated, the largest ({chosen['numbers'][0]}) is "
                                 f"taken as the total")
        values = list(map(str, chosen["numbers"]))
        evidence = [*corrected(chosen), Evidence(quote=chosen["quote"], values=values, belongs_to=chosen["owner"],
                                                 role="alternative" if doubtful else "value")]
        facts.append(Stated(field="B6", name="sample_count", quote=chosen["quote"], evidence=evidence,
                            value="" if doubtful else values[0], values=values if doubtful else []))
    if "feature_count" in counts:
        layers: dict[str, list[dict]] = {}
        for e in live:
            if e["what"] == "features":
                layers.setdefault(e["key"], []).append(e)
        if layers:
            facts += _feature_facts(layers, corrected)
    return facts

def _feature_facts(layers: dict[str, list[dict]], corrected) -> list[Stated]:
    """The feature total over the data objects (each object's versions are its options), and the one object's own
    count when there is one (h3 L40: COBRA's genes > samples reads it)."""
    parts = []  # (owner, options, entries)
    for found in layers.values():
        options = sorted({n for e in found for n in e["numbers"]})
        parts.append((found[0]["owner"], options, found))
    totals = {0}
    for _owner, options, _found in parts:
        totals = {total + option for total in totals for option in options}
    several = len(parts) > 1
    evidence = []
    for owner, options, found in parts:
        for e in found:
            role = "alternative" if len(options) > 1 else "operand" if several else "value"
            evidence += [*corrected(e), Evidence(quote=e["quote"], values=list(map(str, e["numbers"])),
                                                 belongs_to=owner, role=role)]
    unsure = next((found[0]["quote"] for _o, options, found in parts if len(options) > 1), "")
    quote = unsure or parts[0][2][0]["quote"]
    derived = " + ".join(" or ".join(f"{n:,}" for n in options) for _o, options, _f in parts) if several else ""
    facts = [Stated(field="B6", name="feature_count", quote=quote, evidence=evidence, derived=derived,
                    value="" if len(totals) > 1 else str(next(iter(totals))),
                    values=[str(v) for v in sorted(totals)] if len(totals) > 1 else [])]
    if not several:
        options = parts[0][1]
        facts.append(Stated(field="B6", name="single_feature_count", quote=quote, evidence=evidence,
                            value="" if len(options) > 1 else str(options[0]),
                            values=list(map(str, options)) if len(options) > 1 else []))
    return facts
