"""Jev guard arm S (PLAN-FRESH.md section 5): turn-1 gates F1-F5 on the sealed j1 sessions. No model calls.

The live call is the frozen call (shadow); the guard's call is `core.jev_guard`'s `would_have` (the live call when the
guard did not act or did not run). Right = kind in expected_call + also_acceptable, PARTIAL counted as DO.

Usage: python3 score_j1.py > RESULTS-J1.txt   (also writes gates-j1.json)
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "harness-repair-2026-10-23"))
from score import kind_of  # noqa: E402

ACTING = ("DO", "DECLINE")
MEASURES = ("right", "FA", "FR", "MA", "wrong question kind", "extra questions", "UNCHECKED")


def as_kind(call):
    return "DO" if call == "PARTIAL" else call


def events(turn: Path, kind: str) -> list[dict]:
    found = []
    for trace in sorted(turn.glob("trace-*.jsonl")):
        for line in trace.read_text().splitlines():
            if f'"{kind}"' in line and (row := json.loads(line)).get("event_type") == kind:
                found.append(row["payload"])
    return found


def outcome(kind, ok, expected):
    return "right" if kind in ok else kind_of(expected, kind)


def main():
    items = {i["id"]: i for i in json.loads((HERE / "j1" / "items.json").read_text())["single"]}
    rows = []
    for folder in sorted((HERE / "live" / "j1").glob("hb-j1-*-1")):
        item = items[folder.name.split("-")[2]]
        t1 = folder / "t1"
        core = (events(t1, "core.decision") or [None])[-1] or {}
        guard = (events(t1, "core.jev_guard") or [None])[-1] or {}
        live = core.get("kind") or "none"
        would = (guard.get("would_have") or {}).get("kind") or live
        rows.append({"id": item["id"], "group": item["category"], "sub": item["sub"],
                     "dragon": bool(item.get("dragon_control")), "expected": as_kind(item["expected_call"]),
                     "ok": {as_kind(k) for k in [item["expected_call"], *(item.get("also_acceptable") or [])]},
                     "live": live, "basis": core.get("basis"), "guard": would, "status": guard.get("status", "no_event"),
                     "action": guard.get("action"), "jev": guard.get("jev") or {}})
    changed = [r for r in rows if r["guard"] != r["live"]]
    hits = [r for r in changed if r["live"] not in r["ok"]]
    false = [r for r in changed if r["live"] in r["ok"]]
    k_false = [r["id"] for r in false if r["group"] in ("K1", "K2")]
    d_false = [r["id"] for r in false if r["dragon"]]
    before = Counter(outcome(r["live"], r["ok"], r["expected"]) for r in rows)
    after = Counter(outcome(r["guard"], r["ok"], r["expected"]) for r in rows)
    asks = [r for r in rows if r["live"] in ACTING and r["jev"].get("kind") == "ASK"
            and (r["jev"].get("confidence") or 0) >= 0.7]
    asks_acted = [r for r in asks if r["action"] == "ask"]
    gates = {
        "F1": len(hits) >= 4 and len({r["id"] for r in hits}) >= 4,
        "F2": bool(hits) and len(hits) >= len(false),
        "F3": len(k_false) <= 4 and len(d_false) <= 2,
        "F4": all(after[m] <= before[m] for m in ("FA", "FR", "MA"))
              and after["wrong question kind"] - before["wrong question kind"] <= before["MA"] - after["MA"],
        "F5": not asks or len(asks_acted) * 3 >= len(asks) * 2,
    }
    passed = all(gates.values())
    print(f"j1 arm S: {len(rows)} sessions; guard events {dict(Counter(r['status'] for r in rows))}; "
          f"actions {dict(Counter(r['action'] for r in rows))}")
    print(f"live (frozen) right {before['right']}/{len(rows)}; by group "
          + str({g: f"{sum(r['live'] in r['ok'] for r in rows if r['group'] == g)}/{sum(r['group'] == g for r in rows)}"
                 for g in ("V", "U", "K1", "K2")}))
    print(f"guard right {after['right']}/{len(rows)}; by group "
          + str({g: f"{sum(r['guard'] in r['ok'] for r in rows if r['group'] == g)}/{sum(r['group'] == g for r in rows)}"
                 for g in ("V", "U", "K1", "K2")}))
    print(f"Jev alone right {sum(r['jev'].get('kind') in r['ok'] for r in rows)}/{len(rows)}")
    print(f"hits {[r['id'] for r in hits]}; false alarms {[r['id'] for r in false]} (K {k_false}, DRAGON {d_false})")
    print(f"confident Jev ASK on an acting call: {len(asks)}, acted (sentence found) {len(asks_acted)}")
    print("before -> after: " + "  ".join(f"{m} {before[m]}->{after[m]}" for m in MEASURES))
    print("gates " + " ".join(f"{g} {'PASS' if v else 'fail'}" for g, v in gates.items())
          + f" -> {'PASSED' if passed else 'NOT PASSED'}")
    print("\nid | group/sub | D | expected(ok) | live/basis | guard (action) | jev kind conf")
    for r in sorted(rows, key=lambda r: (r["group"], r["id"])):
        print(f"  {r['id']} | {r['group']}/{r['sub']} | {'D' if r['dragon'] else '-'} | {r['expected']}"
              f"{sorted(r['ok'] - {r['expected']}) or ''} | {r['live']}/{r['basis']} | {r['guard']} ({r['action']}) | "
              f"{r['jev'].get('kind')} {r['jev'].get('confidence')}")
    (HERE / "gates-j1.json").write_text(json.dumps({
        "passed": passed, "gates": gates, "hits": [r["id"] for r in hits], "false_alarms": [r["id"] for r in false],
        "k_false": k_false, "dragon_false": d_false, "before": before, "after": after}, indent=1) + "\n")


if __name__ == "__main__":
    main()
