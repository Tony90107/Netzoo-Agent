"""Harness repair P2: the reasons of the decline/partial replies after two-layer reasons, against the P0 baseline.

REPLIES.json comes from ROUND-20's `replies.py` on this checkout (no model calls). A row with no tagged reason (R0) must
now say layer 2 in the rendered reply: `"<quote>" -- I couldn't match this ...`, or, when the reply has no rows, "I
couldn't match what you asked for ...". A reply keeps its baseline category when its stated reasons are unchanged; a
baseline no_reason reply whose rows all say layer 2 is `layer_two`; every other reply needs a category in REVIEW.

Usage: python3 layers.py REPLIES.json
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("reasons_base", HERE / "reasons_base.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

ORDER = ("wrong", "misleading", "right", "true_not_main", "layer_two", "no_reason")
ROW = "\" -- I couldn't match this"
WHOLE = "I couldn't match what you asked for"
OLD = "not matched to any registered workflow"

# My category for each reply whose stated reasons changed from the P0 baseline (ROUND-19 standards).
REVIEW: dict[str, tuple[str, str]] = {
    "hb-h2main-J44-1": ("right", "DO + partial: the GPU reason (the gold) on the setting row, OTTER offered on its own settings"),
    "hb-h3main-L21-1": ("right", "DO + partial: GIRAFFE's no-settings reason (the gold) on each setting row, plus the true ALT"),
    "hb-h1-H40-1": ("right", "as L21; the reasons no longer sit on the run row and the background phrase (was misleading)"),
    "cj-g4o1-C08-1": ("misleading", "unchanged from P0: the unrelated PANDA near miss beside the right reasons; + true ALT"),
    "cj-g4o2-C08-1": ("misleading", "as g4o1"),
    "cj-p2-C08-1": ("right", "unchanged reasons plus the true ALT on the setting rows"),
    "cj-p3-C08-1": ("right", "as p2"),
    "cj-p5-C08-1": ("right", "as p2"),
    "cj-p5r-C08-1": ("right", "as p2"),
}


def baseline() -> dict[str, str]:
    replies, categories = base.round20()
    found = {}
    for row in json.loads((HERE / "replies-base.json").read_text()):
        if row["session"] in base.REVIEW and row["key"] not in replies or base.statements(row) != base.statements(
                replies.get(row["key"], {"lines": []})):
            found[row["key"]] = base.REVIEW[row["session"]][0] if row["session"] in base.REVIEW else "no_reason"
        else:
            found[row["key"]] = categories[row["key"]] if base.statements(row) else "no_reason"
    return found


def covered(row: dict) -> list[str]:
    """The R0 rows of a reply that do not say layer 2."""
    reply = row["reply"]
    return [line["quote"] for line in row["lines"] if line["type"] == "R0" and not (
        f"\"{line['quote']}{ROW}" in reply or (line["quote"] == row["task"] and WHOLE in reply))]


def main(path: str):
    before = baseline()
    old = {row["key"]: row for row in json.loads((HERE / "replies-base.json").read_text())}
    rows = json.loads(Path(path).read_text())
    found, review, gaps, stale = {}, [], [], []
    for row in rows:
        if missing := covered(row):
            gaps.append((row["session"], missing))
        if OLD in row["reply"]:
            stale.append(row["session"])
        was = old.get(row["key"])
        if was is not None and base.statements(was) == base.statements(row):
            category = before[row["key"]]
            found[row["key"]] = "layer_two" if category == "no_reason" and not covered(row) else category
        elif row["session"] in REVIEW:
            found[row["key"]] = REVIEW[row["session"]][0]
        else:
            review.append(row)
    print(f"{len(rows)} replies; R0 rows without layer 2: {gaps or 'none'}; replies still saying '{OLD}': "
          f"{stale or 'none'}")
    counts = Counter(found.values())
    print("P2   " + "  ".join(f"{name} {counts[name]:3}" for name in ORDER) + f"  -- to review: {len(review)}")
    counts = Counter(before.values())
    print("base " + "  ".join(f"{name} {counts[name]:3}" for name in ORDER))
    for row in review:
        print(f"== {row['session']} gold {row['gold']} {row['kind']}{'(p)' if row['partial'] else ''} | "
              f"was {before.get(row['key'], 'not a decline')}")
        was = {(q, t) for q, t in base.statements(old[row["key"]])} if row["key"] in old else set()
        for quote, text in base.statements(row):
            print(f"   {'  ' if (quote, text) in was else '+ '}{quote[:40]!r}: {text[:160]}")
        for quote, text in sorted(was - set(base.statements(row))):
            print(f"   - {quote[:40]!r}: {text[:160]}")


if __name__ == "__main__":
    main(sys.argv[1])
