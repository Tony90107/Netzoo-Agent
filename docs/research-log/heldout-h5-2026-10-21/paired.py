"""h5 metric 5 (ROUND.md), no model calls: rep 1's recorded readings decided by B2 with this code and with the code
before ROUND-17 (425df6fa), each scored by `score.outcome`; fixes and breaks per item.

Usage: python3 paired.py NOW.json BEFORE.json   (harness.py run outputs: this code, and --scripts the old scripts)
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import score  # noqa: E402

SESSION = re.compile(r"^hb-h5main-(Q\d+)-1$")


def calls(path):
    return {SESSION.match(r["session"]).group(1): r for r in json.loads(Path(path).read_text()).values()
            if SESSION.match(r["session"])}


def main(now_path, before_path):
    items = score.items()
    labelled = json.loads((HERE / "facts-checked.json").read_text()) if (HERE / "facts-checked.json").exists() else {}
    key = json.loads((HERE / "fact-key.json").read_text()) if (HERE / "fact-key.json").exists() else {}
    right = {key[s]: v for s, v in labelled.items()}
    now, before = calls(now_path), calls(before_path)
    rows, totals = [], Counter()
    for item in sorted(now):
        # The right-fact label is for the live session's question; the same recorded reading gives the same question.
        fact = right.get(f"{item}-1")
        a = score.outcome(items[item], {"kind": before[item]["kind"], "workflows": [], "partial": before[item]["partial"]}, fact)
        b = score.outcome(items[item], {"kind": now[item]["kind"], "workflows": [], "partial": now[item]["partial"]}, fact)
        totals["before"] += a == "correct"
        totals["now"] += b == "correct"
        if (a == "correct") != (b == "correct"):
            rows.append((item, items[item]["class"], f"{before[item]['kind']}/{before[item]['basis']}",
                         f"{now[item]['kind']}/{now[item]['basis']}", "FIX" if b == "correct" else "BREAK"))
    print(f"rep 1, {len(now)} items: before ROUND-17 {totals['before']} correct, now {totals['now']} correct")
    for row in rows:
        print("  ", *row)


if __name__ == "__main__":
    main(*sys.argv[1:3])
