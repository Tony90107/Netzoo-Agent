"""ROUND-26 plan 3.3 (1): how the reader links the request's words to registry entries, scored against the field gold.
No model calls -- the recorded readings (first pass, re-read, recorded settings reads) as they are.

Units come from the gold (`labels-*.json`); a reader link answers a unit when its quote overlaps the unit's quote in
the request (first occurrence of each quote).

- settings: right = a reader setting over the unit's words has the gold name; wrong = reader settings there, none
  with the gold name; missed = none there. `unregistered` gold is right when no registered name is read there.
  Declared-data settings (log_transformed, centered, gmt_msigdb, with_header) are reported apart from requested
  options (SPOT-CHECK.md). extra = reader settings over no gold setting's words.
- results: the reader's own credits (produces ids, before any typed-attribute fitting) over the unit's words.
  Gold with produces: right = credits within the gold set; partial = some in, some out; wrong = none in; missed = no
  credit. Gold with no produces: right = no credit; wrong = a credit. Named-method units (the quote is a workflow
  name and at most two other words) and wide units (more than 3 ids) are reported apart (SPOT-CHECK.md).

Usage: python3 linking.py OUT.json   (per-reading units in OUT.json; a summary per set on stdout)
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.path.insert(0, str(LOGS / "stability-round13-2026-10-21"))
import harness  # noqa: E402  (sets the import paths to this checkout's scripts)

DECLARED = {"BONOBO.log_transformed", "BONOBO.centered", "SAMBAR.gmt_msigdb", "PANDA.with_header"}
WORKFLOWS = ("LIONESS-COEXPRESSION", "LIONESS-DRAGON", "LIONESS-PANDA", "LIONESS-PUMA", "PANDA", "PUMA", "DRAGON",
             "BONOBO", "CONDOR", "COBRA", "OTTER", "GIRAFFE", "SAMBAR")
SETS = {"h1": "h1", "h2main": "h2", "h3main": "h3", "h4main": "h4", "h5main": "h5", "h6main": "h6"}
H6 = LOGS / "heldout-h6-2026-10-22" / "fields.json"  # h6 final run (its ROUND.md): the sealed field gold


def span(task: str, quote: str):
    start = task.find(quote) if quote else -1
    return (start, start + len(quote)) if start >= 0 else None


def overlaps(a, b) -> bool:
    return a is not None and b is not None and a[0] < b[1] and b[0] < a[1]


def _asks(reading: dict):
    for value in (reading or {}).values():
        if isinstance(value, dict):
            yield from (ask for ask in value.get("asks") or [] if isinstance(ask, dict))


def reader_links(payload: dict, reread: dict | None, found: list[dict]):
    """(settings [(name, quote)], results [(quote, credits)]) the reader itself wrote."""
    from netzoo_agent_core.capability_sheet import sheet_entries

    known = sheet_entries()
    readings = [payload, (reread or {}).get("reread") or {}]
    settings = [(item.get("name", ""), item.get("quote", ""))
                for item in (payload.get("conditions") or {}).get("settings") or [] if isinstance(item, dict)]
    results = []
    for reading in readings:
        for ask in _asks(reading):
            settings += [(item.get("name", ""), item.get("quote", "")) for item in ask.get("settings") or []
                         if isinstance(item, dict)]
            credits = [key for key in ask.get("delivered_by") or [] if key in known and known[key].kind == "produces"]
            results.append((ask.get("quote", ""), credits))
    for event in found:  # ROUND-22 (R22-B): the settings a recorded settings read added
        if event["event_type"] == "core.settings_read" and isinstance(event["payload"].get("read"), dict):
            workflow, read = event["payload"]["workflow"], event["payload"]["read"]
            settings += [(f"{workflow}.{name[:-6]}", words) for name, words in read.items()
                         if name.endswith("_words") and words]
    return settings, results


def named_method(quote: str) -> bool:
    rest = quote
    for name in WORKFLOWS:
        rest = re.sub(re.escape(name), " ", rest, flags=re.I)
    return rest != quote and len(rest.split()) <= 2


def score(task: str, gold: dict, settings, results) -> list[dict]:
    units = []
    read_settings = [(name, span(task, quote)) for name, quote in settings]
    gold_spans = []
    for unit in gold.get("settings", []):
        where = span(task, unit["quote"])
        gold_spans.append(where)
        there = {name for name, place in read_settings if overlaps(where, place)}
        name = unit["setting"]
        registered = {n for n in there if n != "unregistered"}
        outcome = (("right" if not registered else "wrong") if name == "unregistered"
                   else "right" if name in there else "wrong" if there else "missed")
        units.append({"field": "settings", "kind": "declared" if name in DECLARED else "option", "gold": name,
                      "quote": unit["quote"], "read": sorted(there), "outcome": outcome})
    for name, place in read_settings:
        if place is not None and not any(overlaps(place, where) for where in gold_spans):
            units.append({"field": "settings", "kind": "extra", "gold": None, "quote": None, "read": [name],
                          "outcome": "extra"})
    read_results = [(span(task, quote), credits) for quote, credits in results]
    for unit in gold.get("results", []):
        where = span(task, unit["quote"])
        credits = sorted({key for place, keys in read_results if overlaps(where, place) for key in keys})
        wanted = set(unit.get("produces") or [])
        if not wanted:
            outcome = "wrong" if credits else "right"
        elif not credits:
            outcome = "missed"
        else:
            inside = [key for key in credits if key in wanted]
            outcome = "right" if len(inside) == len(credits) else "partial" if inside else "wrong"
        kind = ("named_method" if named_method(unit["quote"]) else "wide" if len(wanted) > 3 else
                "none_produces" if not wanted else "result_words")
        units.append({"field": "results", "kind": kind, "gold": sorted(wanted), "quote": unit["quote"],
                      "read": credits, "outcome": outcome})
    return units


def main(out: str):
    labels = {path.stem.split("-", 1)[1]: {item["id"]: item for item in json.loads(path.read_text())["items"]}
              for path in HERE.glob("labels-*.json")}
    if H6.exists():
        labels["h6"] = {item["id"]: item for item in json.loads(H6.read_text())["items"]}
    rows, table = [], defaultdict(Counter)
    for key, folder, sid, task, payload, reread, found, _n in harness.readings():
        match = harness.SESSION.match(sid)
        if not match:
            continue
        where, item = ("core", match.group("item")) if match.group("item") else (SETS.get(match.group("set")),
                                                                                 match.group("hitem"))
        gold = labels.get(where, {}).get(item)
        if gold is None:
            continue
        settings, results = reader_links(payload, reread, found)
        units = score(task, gold, settings, results)
        rows.append({"key": key, "session": sid, "set": where, "item": item, "units": units})
        for unit in units:
            table[(where, unit["field"], unit["kind"])][unit["outcome"]] += 1
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    print(f"{len(rows)} readings scored")
    for field in ("settings", "results"):
        print(f"== {field}")
        for (where, f, kind), counts in sorted(table.items()):
            if f == field:
                total = sum(v for k, v in counts.items() if k != "extra")
                right = counts.get("right", 0)
                print(f"  {where:5} {kind:13} {dict(counts)}" + (f"  right {right}/{total}" if total else ""))


if __name__ == "__main__":
    main(sys.argv[1])
