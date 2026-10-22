"""h6 audit (ROUND.md): the text-only baseline (`text-baseline-2026-10-22`'s model) trained on all 300 earlier items
predicts h6. Prints its accuracy, per class, and the ids it gets wrong (the hard subset) -- never a prompt.

Usage: python3 baseline_audit.py OUT.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "text-baseline-2026-10-22"))
from baseline import CLASSES, fit_predict, items  # noqa: E402


def main(out: str):
    train = items()
    test = [{"id": item["id"], "set": "h6", "text": item["prompt"], "label": item["class"]}
            for item in json.loads((HERE / "items.json").read_text())["items"]]
    predicted, _, _ = fit_predict(train, test)
    right = [row["id"] for row, guess in zip(test, predicted) if guess == row["label"]]
    hard = sorted(row["id"] for row in test if row["id"] not in right)
    per_class = {c: f"{sum(r['id'] in right for r in test if r['label'] == c)}/{sum(r['label'] == c for r in test)}"
                 for c in CLASSES}
    Path(out).write_text(json.dumps({"right": len(right), "n": len(test), "per_class": per_class, "hard": hard},
                                    indent=1))
    print(f"text-only baseline on h6: {len(right)}/{len(test)}; per class {per_class}; hard subset {hard}")


if __name__ == "__main__":
    main(sys.argv[1])
