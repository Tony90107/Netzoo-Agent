"""ROUND-19 step 3: the final category of each reply -- the judge's, overridden where my review of every judge-'wrong'
reply disagreed (review.md). Categories: wrong (states something false), misleading (true but points at the wrong
obstacle or an unrelated near miss), right, true_not_main, no_reason (only "not matched ...").

Usage: python3 final.py JUDGED.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import judge  # noqa: E402

# My review of the 43 replies the judge put in 'wrong' (review.md): (session, my category, the false premise or note).
REVIEW = {
    "hb-h4main-M32-1": ("misleading", "'none models other regulators' for a causal request; the obstacle is causality"),
    "hb-h2main-J20-1": ("wrong", "'no setting for' output paths, 'start it right away' and the default lambda estimate"),
    "hb-h2main-J31-1": ("misleading", "'none models other regulators' for a causal request"),
    "hb-h2main-J33-1": ("true_not_main", "no per-sample OTTER is true and relevant"),
    "hb-h2main-J46-1": ("right", "CONDOR cannot skip building a network: the gold reason"),
    "hb-h1-H14-1": ("misleading", "'none models other regulators' for a causal request"),
    "hb-h1-H40-1": ("misleading", "true GIRAFFE reason attached to a background phrase read as a request"),
    "cj-g4o1-C07-1": ("wrong", "a doable request (LIONESS-DRAGON) given reasons it cannot be done"),
    "cj-g4o1-C08-1": ("misleading", "unrelated PANDA near miss for 'a TF activity matrix'"),
    "cj-g4o1-C16-1": ("true_not_main", "'none models single cells' is true and relevant"),
    "cj-g4o1-C40-1": ("wrong", "doable request; unsettled genes_axis words given as the reason"),
    "cj-g4o1-C44-1": ("wrong", "'OTTER needs a TF motif prior' though the user has seed_W_mm.tsv"),
    "cj-g4o1-C47-1": ("misleading", "true 'no Cox model' beside unrelated PANDA time-point near misses"),
    "cj-g4o1-C57-1": ("wrong", "COBRA's design table treated as a setting it cannot take"),
    "cj-g4o2-C07-1": ("wrong", "a doable request given reasons it cannot be done"),
    "cj-g4o2-C08-1": ("misleading", "unrelated PANDA near miss for 'a TF activity matrix'"),
    "cj-g4o2-C16-1": ("true_not_main", "'none models single cells' is true and relevant"),
    "cj-g4o2-C40-1": ("wrong", "doable request; unsettled genes_axis words given as the reason"),
    "cj-g4o2-C44-1": ("wrong", "'OTTER needs a TF motif prior' though the user has seed_W_mm.tsv"),
    "cj-g4o2-C47-1": ("true_not_main", "'no registered penalized Cox model' is true"),
    "cj-g4o2-C57-1": ("wrong", "'rows match the sample IDs exactly' treated as a setting COBRA cannot take"),
    "cj-p0-C16-1": ("true_not_main", "'none models single cells'"),
    "cj-p0-C40-1": ("wrong", "doable; condition check: 'BONOBO does not meet gene IDs in the first column ...'"),
    "cj-p0-C47-1": ("true_not_main", "'no registered penalized Cox model' (the call itself runs a part: permissive)"),
    "cj-p0-C51-1": ("wrong", "doable; 'OTTER has no setting for header row, gene IDs in the first column'"),
    "cj-p1-C16-1": ("true_not_main", "'none models single cells'"),
    "cj-p1-C47-1": ("true_not_main", "'no registered penalized Cox model' (the call runs a part: permissive)"),
    "cj-p2-C16-1": ("true_not_main", "'none models single cells'"),
    "cj-p2-C32-1": ("wrong", "doable; condition check: 'DRAGON does not meet complete continuous values with no NAs'"),
    "cj-p2-C46-1": ("true_not_main", "'no registered DESeq2' is true"),
    "cj-p3-C16-1": ("true_not_main", "'none models single cells'"),
    "cj-p3b-C47-1": ("true_not_main", "'no registered penalized Cox model'"),
    "cj-p4b-C16-1": ("true_not_main", "'none models single cells'"),
    "cj-p4b-C47-1": ("true_not_main", "'no registered penalized Cox model'"),
    "cj-p4c-C16-1": ("true_not_main", "'none models single cells'"),
    "cj-p4c-C17-1": ("right", "the alternative (DRAGON with its own settings) is true; the lambda pair reason is right"),
    "cj-p4c-C47-1": ("true_not_main", "'no registered penalized Cox model'"),
    "cj-p4c-C52-1": ("wrong", "doable; condition check: 'BONOBO does not meet log2-transformed and centered'"),
    "cj-p5-C16-1": ("true_not_main", "'none models single cells'"),
    "cj-p5r-C16-1": ("true_not_main", "'none models single cells'"),
    "cj-p5r-C18-1": ("misleading", "'none models other regulators' for CONDOR on raw expression"),
    "cj-p5r-C32-1": ("wrong", "doable; 'DRAGON has no setting for edge list' (edge_list is an allowed output_format)"),
    "cj-p5r-C47-1": ("true_not_main", "'no registered penalized Cox model'"),
}
ORDER = ("wrong", "misleading", "right", "true_not_main", "no_reason")


def final(row: dict) -> str:
    return REVIEW[row["session"]][0] if row["session"] in REVIEW else judge.category(row)


def main(path: str):
    rows = json.loads(Path(path).read_text())["rows"]
    judged_wrong = [r for r in rows if judge.category(r) == "wrong"]
    assert {r["session"] for r in judged_wrong} == set(REVIEW), "review must cover every judge-'wrong' reply"
    counts = Counter(final(r) for r in rows)
    print(f"{len(rows)} replies: " + ", ".join(f"{name} {counts[name]} ({counts[name] / len(rows):.1%})"
                                              for name in ORDER))
    print(f"judge 'wrong' confirmed by review: {sum(REVIEW[r['session']][0] == 'wrong' for r in judged_wrong)}"
          f"/{len(judged_wrong)}")
    for gold in ("DECLINE", "DO", "CLARIFY", "ASK"):
        mine = [r for r in rows if r["gold"] == gold]
        found = Counter(final(r) for r in mine)
        print(f"  gold {gold:8} n={len(mine):3} " + " ".join(f"{name} {found[name]}" for name in ORDER if found[name]))
    print("wrong replies:")
    for r in rows:
        if final(r) == "wrong":
            print(f"  {r['session']:18} gold {r['gold']:8} {r['kind']}{'(p)' if r['partial'] else ''}: "
                  f"{REVIEW[r['session']][1]}")


if __name__ == "__main__":
    main(sys.argv[1])
