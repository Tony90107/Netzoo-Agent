"""Phase 1b intent-probe variant: the three reader arms of one dev round, side by side (no model calls).

Arms on the same reads: first (first read alone), menu (first read + focused re-read + requirement check), probe (the
same with the focused intent probe after the re-read). Dev classes: ask, dont, do (no vague items in the dev set).
A wrong commitment is a DO or DECLINE that is wrong for its class; a needless question is ASK or CLARIFY on a do item.
Probe changes are counted from the merge report: agree, unclear, adopted, kept not stated, per intent.

Usage: probe_arms.py TAG   (reads ../closed-menu-phase1-2026-10-18/live/TAG/dev.json)
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

DEV = Path(__file__).resolve().parent.parent / "closed-menu-phase1-2026-10-18"
RIGHT = {"ask": ("ASK", "CLARIFY"), "dont": ("DECLINE",), "do": ("DO",)}


def arm_row(row, arm):
    return row if arm == "first" else row["final" if arm == "menu" else "final_probe"]


def main(tag):
    rows = json.loads((DEV / "live" / tag / "dev.json").read_text())["rows"]
    items = {i["id"]: i for i in json.loads((DEV / "dev_items.json").read_text())["items"]}
    print(f"| arm | right (ask/dont/do) | wrong commitments | needless questions on do |")
    for arm in ("first", "menu", "probe"):
        right, wrong, needless = Counter(), 0, 0
        for row in rows:
            cls, got = items[row["id"]]["class"], arm_row(row, arm)
            kind = got["kind"] if got.get("status", "read") != "failed" else "UNCHECKED"
            ok = kind in RIGHT[cls] and not (kind == "DO" and got.get("partial"))
            right[cls] += ok
            wrong += kind in ("DO", "DECLINE") and not ok
            needless += cls == "do" and kind in ("ASK", "CLARIFY")
        print(f"| {arm} | {right['ask']}/{right['dont']}/{right['do']} = {sum(right.values())}/{len(rows)} "
              f"| {wrong}/{len(rows)} | {needless}/22 |")
    changes = Counter()
    for row in rows:
        for line in row.get("probe", {}).get("filled") or []:
            match = re.match(r"(agree|unclear|adopted|kept not stated): q\d+ (\w+)", line)
            if match:
                changes[match.groups()] += 1
    print("probe answers:", {f"{k}:{d}": n for (k, d), n in sorted(changes.items())})


if __name__ == "__main__":
    main(sys.argv[1])
