"""Same-day paired comparison: the new code (tag nsfields) and the base code (tag nsbase) on the same 20 items, one
session each; FA / FR / MA primary, a question as a cost (2026-10-22 user rule). No model calls.

Usage: python3 paired.py OUT.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.argv = sys.argv[:2]
sys.path.insert(0, str(HERE))
from run_live import items  # noqa: E402
from score import GOLD, asks, outcome  # noqa: E402


def call(tag: str, item: str) -> dict:
    folder = HERE / "live" / tag / f"hb-{tag}-{item}-1" / "t1"
    found = [json.loads(line) for line in (folder / "events.jsonl").read_text().splitlines() if line.strip()]
    core = next((e["payload"] for e in reversed(found) if e["event_type"] == "core.decision"), {})
    reading = next((e["payload"]["proposal"] for e in found if e["event_type"] == "routing.capability_checked"
                    and e["payload"].get("proposal")), {})
    return {"kind": core.get("kind"), "partial": bool(core.get("partial")), "basis": core.get("basis"),
            "questions": [f.get("question") for f in core.get("facts") or []],
            "fields": [(a.get("group_membership"), a.get("input_network")) for a in asks(reading)]}


def main(out: str):
    rows = []
    for item in items():
        gold = GOLD[item["class"]]
        row = {"set": item["set"], "item": item["id"], "class": item["class"]}
        for tag, arm in (("nsbase", "base"), ("nsfields", "new")):
            got = call(tag, item["id"])
            row[arm] = {**got, "outcome": outcome(gold, got["kind"], got["partial"])}
        rows.append(row)
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    for arm in ("base", "new"):
        print(arm, dict(Counter(r[arm]["outcome"] for r in rows)))
    errors = ("FA", "FR", "MA")
    fixed = [r["item"] for r in rows if r["base"]["outcome"] in errors and r["new"]["outcome"] not in errors]
    broke = [r["item"] for r in rows if r["new"]["outcome"] in errors and r["base"]["outcome"] not in errors]
    print("errors only in base (fixed):", fixed, "| errors only in new (broken):", broke)
    for r in rows:
        b, n = r["base"], r["new"]
        mark = "" if (b["kind"], b["partial"]) == (n["kind"], n["partial"]) else "  <-- differs"
        print(f"{r['set']} {r['item']} {r['class']:5} base {b['kind']}{'p' if b['partial'] else ''}/{b['basis']} "
              f"[{b['outcome']}] {b['fields']}  new {n['kind']}{'p' if n['partial'] else ''}/{n['basis']} "
              f"[{n['outcome']}] {n['fields']}{mark}")


if __name__ == "__main__":
    main(sys.argv[1])
