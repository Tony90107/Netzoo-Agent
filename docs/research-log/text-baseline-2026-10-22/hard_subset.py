"""Post hoc, written after `baseline.py` showed the text-only classifier at 40/48 on h5 (above the pipeline's 68.8%):
two checks on what that number means. No model calls.

1. Permuted-label control: the main model trained on shuffled labels (20 shuffles) -- the accuracy surface cues alone
   cannot explain.
2. Hard and easy h5 items, after Gururangan et al. 2018: "easy" = the text-only classifier gets the item right, "hard" =
   it does not. The pipeline's live accuracy on each subset (96 sessions, both reps).

Usage: python3 hard_subset.py results.json
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

from baseline import LOGS, fit_predict, items


def main(results: str):
    rows = items()
    train = [r for r in rows if r["set"] != "h5"]
    test = [r for r in rows if r["set"] == "h5"]
    shuffled = []
    for seed in range(20):
        labels = [r["label"] for r in train]
        random.Random(seed).shuffle(labels)
        pred, _, _ = fit_predict([dict(r, label=l) for r, l in zip(train, labels)], test)
        shuffled.append(sum(p == r["label"] for r, p in zip(test, pred)))
    print(f"permuted labels, 20 shuffles: right on h5 {min(shuffled)}-{max(shuffled)} of 48, "
          f"mean {sum(shuffled) / len(shuffled):.1f}")

    predicted = json.loads(Path(results).read_text())["main"]["predictions"]
    gold = {r["id"]: r["label"] for r in test}
    easy = {i for i in gold if predicted[i] == gold[i]}
    live = json.loads((LOGS / "heldout-h5-2026-10-21/score.json").read_text())["rows"]
    tally = Counter()
    for row in live:
        subset = "easy" if row["item"] in easy else "hard"
        tally[(subset, row["outcome"] == "correct")] += 1
    for subset in ("easy", "hard"):
        right, n = tally[(subset, True)], tally[(subset, True)] + tally[(subset, False)]
        print(f"{subset}: {n // 2} items; pipeline live right {right}/{n} sessions = {right / n:.3f}")
    hard = sorted(i for i in gold if i not in easy)
    print("hard items:", [(i, gold[i], predicted[i]) for i in hard])


if __name__ == "__main__":
    main(sys.argv[1])
