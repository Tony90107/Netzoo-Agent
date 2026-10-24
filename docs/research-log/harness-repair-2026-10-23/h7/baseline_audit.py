"""h7 audit (ROUND-P5.md): the text-only baseline (`text-baseline-2026-10-22`'s model) trained on all 348 earlier
items (core, h1-h4, h5, h6) predicts h7's single-turn items, and the turn-1 prompts of the multi-turn items (ASK -> ask,
CLARIFY -> vague). Prints accuracy, per class, and the ids it gets wrong (the hard subset) -- never a prompt.
PARTIAL and DECLINE items are class dont for the baseline, as in its training data.

Usage: python3 baseline_audit.py OUT.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parents[1]
sys.path.insert(0, str(LOGS / "text-baseline-2026-10-22"))
from baseline import CLASSES, fit_predict, items  # noqa: E402


def main(out: str):
    train = items() + [{"id": item["id"], "set": "h6", "text": item["prompt"], "label": item["class"]}
                       for item in json.loads((LOGS / "heldout-h6-2026-10-22/items.json").read_text())["items"]]
    data = json.loads((HERE / "items.json").read_text())
    test = [{"id": item["id"], "set": "h7", "text": item["prompt"], "label": item["class"]} for item in data["single"]]
    test += [{"id": item["id"], "set": "h7", "text": item["prompt"],
              "label": "ask" if item["t1_call"] == "ASK" else "vague"} for item in data["multi"]]
    predicted, _, _ = fit_predict(train, test)
    right = {row["id"] for row, guess in zip(test, predicted) if guess == row["label"]}
    report = {"train": len(train)}
    for part, rows in (("single", [r for r in test if r["id"].startswith("S")]),
                       ("multi_t1", [r for r in test if r["id"].startswith("M")])):
        report[part] = {"right": sum(r["id"] in right for r in rows), "n": len(rows),
                        "per_class": {c: f"{sum(r['id'] in right for r in rows if r['label'] == c)}/"
                                         f"{sum(r['label'] == c for r in rows)}" for c in CLASSES},
                        "hard": sorted(r["id"] for r in rows if r["id"] not in right)}
    Path(out).write_text(json.dumps(report, indent=1))
    print(json.dumps(report))


if __name__ == "__main__":
    main(sys.argv[1])
