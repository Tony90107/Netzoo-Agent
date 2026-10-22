"""Same-day paired comparison of the verified-forms change: the frozen code (tag vqbase, 91a8c2d9) and the new code
(tag vqnew, 81912052) on the same 18 items, one session each; FA / FR / MA primary, a question as a cost
(2026-10-22 user rule). Beside each call: the ask forms and the request-level form with its quote. No model calls.

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

GOLD = {"do": "DO", "dont": "DECLINE", "ask": "ASK", "vague": "CLARIFY"}
FORMS = ("group_membership", "time_model", "spatial")
OFF = {"group_membership": "several_groups", "time_model": "dynamic", "spatial": "uses_neighbors"}


def outcome(gold, kind, partial):
    if gold == "DO":
        return "right" if kind == "DO" and not partial else "FR" if kind in ("DECLINE", "DO") else "cost"
    if gold == "DECLINE":
        return "right" if kind == "DECLINE" else "FA" if kind == "DO" else "cost"
    if kind in ("DO", "DECLINE"):
        return "MA"
    return "right" if kind == gold else "cost"


def call(tag: str, item: str) -> dict:
    folder = HERE / "live" / tag / f"hb-{tag}-{item}-1" / "t1"
    found = [json.loads(line) for line in (folder / "events.jsonl").read_text().splitlines() if line.strip()]
    core = next((e["payload"] for e in reversed(found) if e["event_type"] == "core.decision"), {})
    reading = next((e["payload"]["proposal"] for e in found if e["event_type"] == "routing.capability_checked"
                    and e["payload"].get("proposal")), {})
    asks = [a for key, part in reading.items() if key[:1] == "s" and key[1:].isdigit()
            for a in (part or {}).get("asks") or []]
    cond = reading.get("conditions") or {}
    return {"kind": core.get("kind"), "partial": bool(core.get("partial")), "basis": core.get("basis"),
            "ask_off": sorted({f"{f}={a.get(f)}" for a in asks for f in FORMS if a.get(f) == OFF[f]}),
            "condition_off": {f: cond.get(f"{f}_quote", "") for f in FORMS if cond.get(f) == OFF[f]}}


def main(out: str):
    rows = []
    for item in items():
        gold = GOLD[item["class"]]
        row = {"set": item["set"], "item": item["id"], "class": item["class"]}
        for tag, arm in (("vqbase", "base"), ("vqnew", "new")):
            got = call(tag, item["id"])
            row[arm] = {**got, "outcome": outcome(gold, got["kind"], got["partial"])}
        rows.append(row)
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    for arm in ("base", "new"):
        print(arm, dict(Counter(r[arm]["outcome"] for r in rows)))
    errors = ("FA", "FR", "MA")
    print("errors only in base (fixed):", [r["item"] for r in rows if r["base"]["outcome"] in errors
                                           and r["new"]["outcome"] not in errors],
          "| errors only in new (broken):", [r["item"] for r in rows if r["new"]["outcome"] in errors
                                             and r["base"]["outcome"] not in errors])
    for r in rows:
        b, n = r["base"], r["new"]
        print(f"{r['set']:9} {r['item']} {r['class']:4} base {b['kind']}{'p' if b['partial'] else ''}/{b['basis']} "
              f"[{b['outcome']}] {b['ask_off']} {b['condition_off']}  ||  new {n['kind']}{'p' if n['partial'] else ''}"
              f"/{n['basis']} [{n['outcome']}] {n['ask_off']} {n['condition_off']}")


if __name__ == "__main__":
    main(sys.argv[1])
