"""Where the core judgment goes wrong across five recorded 56-item rounds (2026-10-18, offline, no model calls).

Reads `core-judgment-2026-10-15/live/<round>/score-core.json` and each session's trace, and prints:

1. the wrong calls bucketed by the layer that produced them;
2. how two rounds agree, and how accurate the calls are where they agree;
3. every not-available result row behind a DECLINE or partial DO, split by whether it carried a contract reason.

Usage: python3 analyze_bottleneck.py
"""

from __future__ import annotations

import glob
import json
from collections import Counter
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1] / "core-judgment-2026-10-15"
ROUNDS = ("p4b", "p4c", "p5r", "g4o1", "g4o2")
GOLD = {"do": "DO", "dont": "DECLINE", "ask": "ASK", "vague": "CLARIFY"}
ITEMS = {item["id"]: item for item in json.loads((BENCH / "items.json").read_text())["items"]}


def scores(name: str) -> dict:
    return json.loads((BENCH / "live" / name / "score-core.json").read_text())["items"]


def last_check(name: str, item: str) -> dict | None:
    found = None
    for path in glob.glob(str(BENCH / "live" / name / f"*-{item}-1" / "t1" / "events.jsonl")):
        for line in open(path, encoding="utf-8"):
            event = json.loads(line)
            if event["event_type"] == "routing.capability_checked":
                found = event["payload"]["check"]
    return found


def bucket(gold: str, kind: str, basis: str) -> str:
    if kind == "UNCHECKED":
        return "E reading failed (UNCHECKED)"
    if gold != "DECLINE" and (basis in ("full_gap", "all_results_not_available") or kind == "DO(partial)"):
        return "A an uncredited row counted as cannot-do (full gap or partial)"
    if gold != "CLARIFY" and basis in ("goal_unclear", "no_result_read"):
        return "B the one goal field flipped the call to CLARIFY"
    if gold == "DECLINE" and kind.startswith("DO"):
        return "C a limit was not read (false accept)"
    if gold in ("ASK", "CLARIFY") and kind != gold:
        return "D should have asked or clarified, did not (or asked at the wrong level)"
    if kind == gold:
        return "F right kind, wrong workflow or fact"
    return f"G other {gold}->{kind}/{basis}"


def main() -> None:
    by_round = {name: scores(name) for name in ROUNDS}

    print("== 1. wrong calls by layer ==")
    found, where = Counter(), {}
    for name, items in by_round.items():
        for item, row in items.items():
            if row["outcome"] != "correct":
                label = bucket(GOLD[ITEMS[item]["class"]], row["kind"], row["basis"])
                found[label] += 1
                where.setdefault(label, set()).add(item)
    total = sum(found.values())
    print(f"{total} wrong of {sum(len(v) for v in by_round.values())} calls")
    for label, count in sorted(found.items()):
        print(f"{count:3d} {count / total:4.0%} {label}  {sorted(where[label])}")

    print("\n== 2. agreement between two rounds ==")
    for a, b in (("p4b", "p4c"), ("g4o1", "g4o2"), ("p5r", "g4o1")):
        first, second = by_round[a], by_round[b]
        shared = sorted(set(first) & set(second))
        agree = [i for i in shared if first[i]["kind"] == second[i]["kind"]]
        right = sum(first[i]["outcome"] == "correct" for i in agree)
        single = sum(r[i]["outcome"] == "correct" for r in (first, second) for i in shared) / 2
        print(f"{a} vs {b}: agree {len(agree)}/{len(shared)}, right where they agree {right}/{len(agree)} "
              f"({right / len(agree):.0%}); one round alone {single:.1f}/{len(shared)} ({single / len(shared):.0%})")

    print("\n== 3. not-available rows behind DECLINE / partial DO ==")
    kinds = Counter()
    for name, items in by_round.items():
        for item, row in items.items():
            if row["kind"] not in ("DECLINE", "DO(partial)") or (check := last_check(name, item)) is None:
                continue
            rows = [r for r in check["requirements"] if r["kind"] == "result" and r["status"] == "not_available"]
            if not rows:
                continue
            reasoned = all(r["limits"] or r["violations"] or r.get("not_by") for r in rows)
            kinds[(ITEMS[item]["class"], row["kind"], "contract reason" if reasoned else "uncredited only",
                   "right" if row["outcome"] == "correct" else "WRONG")] += 1
    for key, count in sorted(kinds.items()):
        print(count, key)


if __name__ == "__main__":
    main()
