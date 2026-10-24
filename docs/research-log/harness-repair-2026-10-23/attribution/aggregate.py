"""Harness repair P5 error attribution (ATTRIBUTION.md): the labellers' layers, tallied; the spot-check sample.

Usage: python3 aggregate.py table             -> attribution.json and printed tables
       python3 aggregate.py sample N          -> spot-check.json: N records drawn with a fixed seed (evidence + label)
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parents[1]
SEED = 1024


def load():
    replay = {r["key"]: r for r in json.loads((HERE / "evidence-replay.json").read_text())}
    h7 = {r["id"]: r for r in json.loads((HERE / "evidence-h7.json").read_text())}
    labels = {}
    for path in sorted(HERE.glob("labels-*.json")):
        labels.update(json.loads(path.read_text()))
    return replay, h7, labels


def table():
    replay, h7, labels = load()
    missing = [k for k in [*replay, *h7] if k not in labels]
    report = {"missing_labels": missing}
    rows = [(r, labels[k]) for k, r in replay.items() if k in labels]
    report["replay"] = {
        "records": len(rows),
        "layer": dict(Counter(l["layer"] for _, l in rows)),
        "subtype": dict(Counter(l["subtype"] for _, l in rows).most_common()),
        "by_error": {e: dict(Counter(l["layer"] for r, l in rows if r["error"] == e))
                     for e in ("FA", "FR", "MA", "extra questions", "wrong question kind", "UNCHECKED")},
        "low_confidence": sum(l.get("confidence") == "low" for _, l in rows)}
    by_item = defaultdict(list)
    for r, l in rows:
        by_item[(r["set"], r["item"])].append(l["layer"])
    dominant = Counter(Counter(layers).most_common(1)[0][0] for layers in by_item.values())
    report["replay"]["items"] = {"n": len(by_item), "dominant_layer": dict(dominant),
                                 "mixed": sorted(f"{s}:{i}" for (s, i), layers in by_item.items() if len(set(layers)) > 1)}
    audit = json.loads((LOGS / "strictness-audit-2026-10-20/audit.json").read_text())["items"]
    report["replay"]["vs_audit_cause"] = dict(Counter(
        f'{l["layer"]} | audit cause: {audit[r["item"]].get("cause")}' for r, l in rows
        if r["set"] != "core" and r["item"] in audit))
    h_rows = [(r, labels[k]) for k, r in h7.items() if k in labels]
    report["h7"] = {"records": len(h_rows),
                    "by_round": {rnd: dict(Counter(l["layer"] for r, l in h_rows if r["round"] == rnd))
                                 for rnd in ("p5r1", "p5r2")},
                    "subtype": dict(Counter(l["subtype"] for _, l in h_rows).most_common()),
                    "by_part": {p: dict(Counter(l["layer"] for r, l in h_rows if r["part"] == p))
                                for p in ("single", "multi")},
                    "low_confidence": sum(l.get("confidence") == "low" for _, l in h_rows)}
    rounds = defaultdict(dict)
    for r, l in h_rows:
        rounds[r["item"]][r["round"]] = l["layer"] + "/" + l["subtype"]
    report["h7"]["stable_both_rounds"] = {i: v for i, v in sorted(rounds.items()) if len(v) == 2}
    report["h7"]["one_round_only"] = {i: v for i, v in sorted(rounds.items()) if len(v) == 1}
    (HERE / "attribution.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(json.dumps(report, indent=1, ensure_ascii=False))


def sample(n: int):
    replay, h7, labels = load()
    pool = sorted(k for k in [*replay, *h7] if k in labels)
    picked = random.Random(SEED).sample(pool, n)
    out = [{"key": k, "label": labels[k], "evidence": replay.get(k) or h7.get(k)} for k in picked]
    (HERE / "spot-check.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"{len(out)} records drawn: {picked}")


if __name__ == "__main__":
    {"table": lambda: table(), "sample": lambda: sample(int(sys.argv[2]))}[sys.argv[1]]()
