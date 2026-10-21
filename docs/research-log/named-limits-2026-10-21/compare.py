"""ROUND-18 offline check (no model calls): every recorded reading decided by B2 with the code before ROUND-18 (a
`git archive` of c6b58f5b, `--scripts`) and with this checkout, comparing the call and each result row's reasons.

Usage:
  python3 compare.py run OUT.json [--scripts DIR]
  python3 compare.py diff BEFORE.json AFTER.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "stability-round13-2026-10-21"))
import harness  # noqa: E402  (honours --scripts)


def run(out: str):
    by_session, core = harness._gold()
    rows = {}
    for key, folder, sid, task, payload, reread, found, _n in harness.readings():
        try:
            call = harness.replay_full.replay(folder, task, payload, reread, found)
        except Exception as error:  # noqa: BLE001 -- the three 10-20 T01 readings of a withdrawn shape
            call = {"kind": f"error:{type(error).__name__}", "rows": []}
        rows[key] = {"session": sid, "turn": folder.name, "gold": harness._label(sid, by_session, core),
                     "kind": call["kind"], "basis": call.get("basis"), "partial": call.get("partial"),
                     "results": [[r["quote"][:70], r["status"], (r["limits"] or r["violations"])[:2]]
                                 for r in call.get("rows", []) if r["kind"] == "result"]}
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    labelled = [r for r in rows.values() if r["gold"]]
    print(f"{len(rows)} readings; right {sum(r['kind'] == r['gold'] for r in labelled)}/{len(labelled)}")


def diff(before_path: str, after_path: str):
    before, after = json.loads(Path(before_path).read_text()), json.loads(Path(after_path).read_text())
    calls = reasons = 0
    for key in sorted(after):
        a, b = before[key], after[key]
        if (a["kind"], a["partial"]) != (b["kind"], b["partial"]):
            calls += 1
            mark = ("" if not b["gold"] else "FIX" if b["kind"] == b["gold"] != a["kind"]
                    else "BREAK" if a["kind"] == a["gold"] != b["kind"] else "other")
            print(f"CALL {mark:5} {b['session']}/{b['turn']} gold {b['gold']}: {a['kind']}/{a['basis']} -> "
                  f"{b['kind']}/{b['basis']}")
        elif a["results"] != b["results"]:
            reasons += 1
            for x, y in zip(a["results"], b["results"]):
                if x != y:
                    print(f"WHY   {b['session']}/{b['turn']} gold {b['gold']} ({b['kind']}): \"{y[0]}\" {y[1]}\n"
                          f"        before {x[2]}\n        after  {y[2]}")
    print(f"{calls} calls changed; {reasons} readings changed only their reasons")


if __name__ == "__main__":
    args = [a for i, a in enumerate(sys.argv[1:], 1) if a != "--scripts" and sys.argv[i - 1] != "--scripts"]
    run(args[1]) if args[0] == "run" else diff(args[1], args[2])
