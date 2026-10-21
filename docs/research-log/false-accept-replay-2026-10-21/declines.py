"""ROUND-12 tables (collab/ROUND-12-PLAN.md section 3), from b2.json; and ROUND-11's variants decided by B2. No model
calls.

Usage:
  python3 declines.py tables b2.json               B2 vs recorded, and every gold-DECLINE call by B2 kind
  python3 declines.py round11 OUT.json             ROUND-11's B / O-a / O-b / O-c / O-ab / O, each decided by B2
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import replay_full  # noqa: E402  (sets the import paths)

sys.path.insert(0, str(HERE.parent / "unit-typing-d1-2026-10-21"))
import oracle  # noqa: E402
import units  # noqa: E402

MINI, GPT4O = ("p4b", "p4c", "p5r"), ("g4o1", "g4o2")


def _kind(call: dict) -> str:
    return f"{call['kind']}{'(partial)' if call.get('partial') else ''}"


def tables(path: str):
    rows = json.loads(Path(path).read_text())
    for group, names in (("mini", MINI), ("gpt-4o", GPT4O)):
        mine = [r for r in rows if r["round"] in names]
        print(f"== {group}: {len(mine)} readings; B2 = recorded {sum(r['b2']['kind'] == r['recorded'] for r in mine)}; "
              f"right: recorded {sum(r['recorded'] == r['gold'] for r in mine)}, B2 "
              f"{sum(r['b2']['kind'] == r['gold'] for r in mine)}")
        for r in mine:
            if r["b2"]["kind"] != r["recorded"]:
                print(f"  differs {r['round']}:{r['item']} gold {r['gold']} recorded {r['recorded']}/{r['recorded_basis']}"
                      f" -> B2 {r['b2']['kind']}/{r['b2']['basis']} steps {r['b2']['steps']}")
        declines = [r for r in mine if r["gold"] == "DECLINE"]
        print(f"  gold DECLINE {len(declines)}: B2 {dict(Counter(_kind(r['b2']) for r in declines))}")
        for r in declines:
            if r["b2"]["kind"] != "DECLINE":
                results = [(row["status"], row["quote"][:50], (row["limits"] or row["violations"])[:1])
                           for row in r["b2"]["rows"] if row["kind"] == "result"]
                print(f"    {r['round']}:{r['item']} {_kind(r['b2'])}/{r['b2']['basis']} recorded {r['recorded']} "
                      f"results {results}")


def round11(out: str):
    truth, tasks = units.gold(), units.items()
    rows = []
    for name, model in units.ROUNDS.items():
        for item, folder, task, payload, reread, _failed in units.recorded(name):
            if item not in truth or payload is None:
                continue
            found = replay_full.events(folder)
            row = {"round": name, "item": item, "gold": tasks[item]["gold"], "calls": {}}
            for variant in oracle.VARIANTS:
                edited, again, changed = ((payload, reread, {}) if variant == "B"
                                          else oracle.edit(task, truth[item], payload, reread, variant))
                call = replay_full.replay(folder, task, edited, again, found)
                row["calls"][variant] = {"kind": call["kind"], "basis": call.get("basis"), "changed": changed}
            rows.append(row)
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    for group, names in (("mini", MINI), ("gpt-4o", GPT4O)):
        mine = [r for r in rows if r["round"] in names]
        wrong = sum(r["calls"]["B"]["kind"] != r["gold"] for r in mine)
        print(f"== {group}: {len(mine)} readings, B2 right {len(mine) - wrong}, wrong {wrong}")
        for variant in oracle.VARIANTS[1:]:
            fixed = [f"{r['round']}:{r['item']}" for r in mine
                     if r["calls"]["B"]["kind"] != r["gold"] and r["calls"][variant]["kind"] == r["gold"]]
            broke = [f"{r['round']}:{r['item']}" for r in mine
                     if r["calls"]["B"]["kind"] == r["gold"] and r["calls"][variant]["kind"] != r["gold"]]
            print(f"  {variant:4} fixed {len(fixed)} {fixed}; broke {len(broke)} {broke}")


if __name__ == "__main__":
    args = sys.argv[1:]
    {"tables": tables, "round11": round11}[args[0]](args[1])
