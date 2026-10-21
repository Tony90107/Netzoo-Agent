"""ROUND-20 step 5: the final category of each of the 209 replies, against ROUND-19's and the plan's gates.

A reply whose stated reasons are unchanged keeps its ROUND-19 final category (the judge's, with my review of every
judge-'wrong' reply). Each of the 34 changed replies (`compare.py`) was judged again by the frozen judge
(judged-changed.json) and reviewed by me; REVIEW holds my category for every one, by ROUND-19's standards.

Variant "without B": the eight replies rule B changed differ from ROUND-19 only by the removed condition-check line
(compare.py), so without B they are ROUND-19's replies and keep its categories.

Usage: python3 final.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROUND19 = HERE.parent / "reason-accuracy-2026-10-21"
sys.path.insert(0, str(ROUND19))
import final as round19  # noqa: E402
import judge  # noqa: E402

# (my category, note) for each changed reply. ROUND-19 standards: a true reason beside an unrelated near miss is
# misleading (C47 g4o1); the causal registry-wide sentence is true_not_main (L29, unchanged, is so in ROUND-19).
REVIEW = {
    "hb-h4main-M32-1": ("true_not_main", "only the causal registry-wide reason is left; as L29 in ROUND-19"),
    "hb-h2main-J20-1": ("right", "the four 'no setting for' lines are gone; the size limit (the gold) is left"),
    "hb-h2main-J31-1": ("no_reason", "'none models other regulators' was its only reason"),
    "hb-h2main-J46-1": ("true_not_main", "B: CONDOR's unmet condition (right) is gone; the delivery line is true, "
                                         "not the gold (judge: true_main, overruled)"),
    "hb-h1-H14-1": ("true_not_main", "only the causal registry-wide reason is left; as L29 in ROUND-19"),
    "hb-h1-H27-1": ("no_reason", "B: CONDOR's unmet condition was the right reason"),
    "hb-h1-H40-1": ("misleading", "unchanged from ROUND-19: true GIRAFFE reasons on background phrases read as asks"),
    "hb-h3main-L21-1": ("right", "the number-free PPI-weight line is gone; learning rate and iterations are left"),
    "cj-g4o1-C07-1": ("wrong", "a doable request; an unrelated PANDA near miss came up in place of the dropped lines"),
    "cj-g4o1-C08-1": ("misleading", "unchanged from ROUND-19: unrelated PANDA near miss beside the right reasons"),
    "cj-g4o1-C40-1": ("no_reason", "C: the unsettled genes_axis words are not said"),
    "cj-g4o1-C44-1": ("no_reason", "D: the motif prior ruled out only by 'only that co-expression file'"),
    "cj-g4o1-C57-1": ("misleading", "A: the design-table line is gone; COBRA's size limit (the gold) is left beside "
                                    "an unrelated PANDA near miss the 2-reason cap now shows"),
    "cj-g4o2-C07-1": ("wrong", "a doable request; an unrelated PANDA near miss came up in place of the dropped lines"),
    "cj-g4o2-C08-1": ("misleading", "unchanged from ROUND-19: unrelated PANDA near miss beside the right reasons"),
    "cj-g4o2-C40-1": ("no_reason", "C: the unsettled genes_axis words are not said"),
    "cj-g4o2-C44-1": ("no_reason", "D: as g4o1; its OTTER near miss goes with the row"),
    "cj-g4o2-C47-1": ("true_not_main", "kept as ROUND-19 (first row unchanged; the second row's R5 is gone)"),
    "cj-g4o2-C57-1": ("misleading", "as g4o1"),
    "cj-p0-C14-1": ("no_reason", "B: OTTER's unmet sparsity condition was the right reason"),
    "cj-p0-C40-1": ("no_reason", "B: the false 'BONOBO does not meet' line is gone"),
    "cj-p0-C51-1": ("no_reason", "A: 'header row, gene IDs in the first column' is no setting; its alternative goes too"),
    "cj-p1-C18-1": ("no_reason", "B: CONDOR's unmet condition was the right reason"),
    "cj-p2-C08-1": ("right", "the number-free PPI-weight line is gone; the rest is unchanged"),
    "cj-p2-C32-1": ("no_reason", "B: the false 'DRAGON does not meet' line is gone"),
    "cj-p3-C08-1": ("right", "the number-free PPI-weight line is gone; the rest is unchanged"),
    "cj-p4b-C18-1": ("no_reason", "B: CONDOR's unmet condition was the right reason"),
    "cj-p4b-C47-1": ("true_not_main", "kept as ROUND-19 (first row unchanged)"),
    "cj-p4c-C17-1": ("right", "kept as ROUND-19 (its first line is unchanged; see RESULTS: doubtful in both)"),
    "cj-p4c-C47-1": ("true_not_main", "kept as ROUND-19 (first row unchanged)"),
    "cj-p4c-C52-1": ("no_reason", "B: the false 'BONOBO does not meet' line is gone"),
    "cj-p5-C08-1": ("right", "the number-free PPI-weight line is gone; the rest is unchanged"),
    "cj-p5r-C18-1": ("right", "'none models other regulators' is gone; the motif/PPI route reason (the gold) is left"),
    "cj-p5r-C32-1": ("no_reason", "A: 'edge list' is an allowed output_format; its alternative goes too"),
}
ONLY_B = ("hb-h2main-J46-1", "hb-h1-H27-1", "cj-p0-C14-1", "cj-p1-C18-1", "cj-p4b-C18-1", "cj-p0-C40-1",
          "cj-p2-C32-1", "cj-p4c-C52-1")
ORDER = ("wrong", "misleading", "right", "true_not_main", "no_reason")


def _table(name: str, rows: list[dict], categories: dict[str, str]):
    counts = Counter(categories[r["key"]] for r in rows)
    print(f"{name:12} " + "  ".join(f"{c} {counts[c]:3}" for c in ORDER))
    return counts


def main():
    old = {r["key"]: r for r in json.loads((ROUND19 / "judged.json").read_text())["rows"]}
    new = json.loads((HERE / "replies.json").read_text())
    changed = {r["key"]: r for r in json.loads((HERE / "judged-changed.json").read_text())["rows"]}
    assert {changed[k]["session"] for k in changed} == set(REVIEW), "every changed reply is reviewed"
    before = {key: round19.final(row) for key, row in old.items()}
    after = {r["key"]: REVIEW[r["session"]][0] if r["key"] in changed else before[r["key"]] for r in new}
    without_b = {key: before[key] if old[key]["session"] in ONLY_B else value for key, value in after.items()}
    print(f"{len(new)} replies; {len(changed)} changed (judge on them: "
          f"{dict(Counter(judge.category(r) for r in changed.values()))})")
    counts = [_table(name, new, cats) for name, cats in
              (("ROUND-19", before), ("ROUND-20", after), ("without B", without_b))]
    for gold in ("DECLINE", "DO", "CLARIFY", "ASK"):
        mine = [r for r in new if r["gold"] == gold]
        _table(f"  {gold}", mine, after)
    base = counts[0]
    for name, found in zip(("ROUND-20", "without B"), counts[1:]):
        gates = {"1 wrong -8 or more": base["wrong"] - found["wrong"] >= 8,
                 "  (target <= 3)": found["wrong"] <= 3,
                 "2 right >= ROUND-19": found["right"] >= base["right"],
                 "3 misleading not up": found["misleading"] <= base["misleading"]}
        print(f"{name}: " + "; ".join(f"{gate} {'PASS' if ok else 'FAIL'}" for gate, ok in gates.items()))
    print("changed replies:")
    for r in new:
        if r["key"] in changed:
            print(f"  {r['session']:18} {before[r['key']]:13} -> {after[r['key']]:13} {REVIEW[r['session']][1]}")


if __name__ == "__main__":
    main()
