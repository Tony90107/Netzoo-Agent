"""Score L1-L3 (ROUND.md) from the fc1 turn-1 traces. No model calls.

Usage: python3 score_live.py > RESULTS-LIVE.txt   (also writes score-fc1.json)
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def facts(turn: Path) -> dict:
    found = {"doubts": [], "waits": [], "call": None}
    for trace in sorted(turn.glob("trace-*.jsonl")):
        for line in trace.read_text().splitlines():
            row = json.loads(line)
            kind, payload = row.get("event_type"), row.get("payload") or {}
            if kind == "routing.capability_checked":  # the first reading (the re-read only adds asks)
                check = payload.get("check") or {}
                found["doubts"] = [[f["property"], f.get("values"), sorted({e["reader"] for e in f["evidence"]})]
                                   for f in check.get("facts") or [] if f.get("state") == "unsure"
                                   and f.get("property") in ("sample_count", "feature_count")]
                found["waits"] = [[r.get("depends_on"), r.get("by_code"), r.get("outcomes")]
                                  for r in check.get("requirements") or [] if r.get("status") == "needs_fact"]
            elif kind == "core.decision":
                found["call"] = f"{payload.get('kind')}/{payload.get('basis')}"
    return found


def main():
    rows = []
    for job in sorted((HERE / "live" / "fc1").glob("*/job.json")):
        record = json.loads(job.read_text())
        rows.append(record | facts(job.parent / "t1"))
    targets = [r for r in rows if r["group"] == "target"]
    l1 = [r["item"] for r in targets if any(w[0] == "feature_count" and w[1] for w in r["waits"])]
    l2 = [r["item"] for r in rows if r["group"] == "sample_doubt" and any(d[0] == "feature_count" for d in r["doubts"])]
    l3 = [r["item"] for r in rows if r["group"] == "no_doubt" and (r["call"] or "").startswith("ASK")
          and any(w[0] in ("feature_count", "sample_count") for w in r["waits"])]
    gates = {"L1": len(l1) * 2 >= len(targets), "L2": len(l2) <= 1, "L3": not l3}
    for r in rows:
        print(f"{r['item']} | {r['group']} | {r['call']} | doubts {r['doubts']} | waits {r['waits']}")
    print(f"L1 targets waiting on a feature count in code: {l1} of {len(targets)} -> {'PASS' if gates['L1'] else 'fail'}")
    print(f"L2 sample doubts typed feature_count: {l2} (<= 1) -> {'PASS' if gates['L2'] else 'fail'}")
    print(f"L3 new count asks on no-doubt items: {l3} -> {'PASS' if gates['L3'] else 'fail'}")
    (HERE / "score-fc1.json").write_text(json.dumps({"gates": gates, "rows": rows}, indent=1) + "\n")


if __name__ == "__main__":
    main()
