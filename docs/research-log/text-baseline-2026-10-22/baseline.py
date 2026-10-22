"""Option B gate (`output/thesis/2026-10-22_瓶頸與下一步_文獻建議.md`, section 3): how far a text-only classifier, which
never sees the registry, gets on the four-way call. No model calls, no downloads.

Declared before running:
- Items: the 300 gold-labelled requests -- core (C01-C60), h1-h4 (H/J/L/M, 48 each), h5 (Q, 48). Text = the prompt,
  label = the gold class (do / dont / ask / vague).
- Main model: word 1-2-gram TF-IDF (sublinear tf, min_df 1) + logistic regression (C=1, balanced classes).
- Main split: train on core + h1-h4 (252), test on h5 (48) -- the same fresh items the pipeline scored 68.8% on live.
- Gate: h5 accuracy >= 68.8% keeps the classifier as a second-opinion candidate; below it, option B stops.
- Secondary (reported, not gated): leave-one-set-out over the six sets (each set written by a different author run);
  the top words per class; on h5, how the classifier's disagreements line up with the pipeline's live errors.

Usage: python3 baseline.py OUT.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix

LOGS = Path(__file__).resolve().parents[1]
CLASSES = ["do", "dont", "ask", "vague"]
KIND = {"DO": "do", "DECLINE": "dont", "ASK": "ask", "CLARIFY": "vague"}
PIPELINE_H5 = 0.6875


def items():
    rows = []
    core = json.loads((LOGS / "core-judgment-2026-10-15/items.json").read_text())["items"]
    for item in (core.values() if isinstance(core, dict) else core):
        rows.append({"id": item["id"], "set": "core", "text": item["prompt"], "label": item["class"]})
    for item in json.loads((LOGS / "strictness-audit-2026-10-20/audit.json").read_text())["items"].values():
        rows.append({"id": item["id"], "set": item["set"], "text": item["prompt"], "label": item["class"]})
    for item in json.loads((LOGS / "heldout-h5-2026-10-21/items.json").read_text())["items"]:
        rows.append({"id": item["id"], "set": "h5", "text": item["prompt"], "label": item["class"]})
    return rows


def model():
    return (TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, lowercase=True),
            LogisticRegression(C=1.0, class_weight="balanced", max_iter=5000))


def fit_predict(train, test):
    vec, clf = model()
    clf.fit(vec.fit_transform([r["text"] for r in train]), [r["label"] for r in train])
    return list(clf.predict(vec.transform([r["text"] for r in test]))), vec, clf


def per_class(test, predicted):
    return {c: f"{sum(p == r['label'] == c for r, p in zip(test, predicted))}/{sum(r['label'] == c for r in test)}"
            for c in CLASSES}


def main(out: str):
    rows = items()
    sets = Counter(r["set"] for r in rows)
    assert sum(sets.values()) == 300 and len({(r["set"], r["id"]) for r in rows}) == 300, sets
    train = [r for r in rows if r["set"] != "h5"]
    test = [r for r in rows if r["set"] == "h5"]
    predicted, vec, clf = fit_predict(train, test)
    accuracy = sum(p == r["label"] for r, p in zip(test, predicted)) / len(test)
    report = {"sets": dict(sets), "main": {
        "accuracy": accuracy, "right": sum(p == r["label"] for r, p in zip(test, predicted)), "n": len(test),
        "per_class": per_class(test, predicted), "pipeline_live_mean": PIPELINE_H5,
        "gate_passed": accuracy >= PIPELINE_H5,
        "confusion (rows gold, cols predicted)": {"order": CLASSES, "matrix": confusion_matrix(
            [r["label"] for r in test], predicted, labels=CLASSES).tolist()},
        "predictions": {r["id"]: p for r, p in zip(test, predicted)}}}

    names = np.array(vec.get_feature_names_out())
    report["top_words"] = {c: list(names[np.argsort(clf.coef_[i])[::-1][:12]]) for i, c in enumerate(clf.classes_)}

    report["leave_one_set_out"] = {}
    for held in sorted(sets):
        tr, te = [r for r in rows if r["set"] != held], [r for r in rows if r["set"] == held]
        pred, _, _ = fit_predict(tr, te)
        report["leave_one_set_out"][held] = {
            "accuracy": round(sum(p == r["label"] for r, p in zip(te, pred)) / len(te), 3),
            "per_class": per_class(te, pred)}

    # On h5: does the classifier disagree with the pipeline mostly where the pipeline was wrong?
    live = json.loads((LOGS / "heldout-h5-2026-10-21/score.json").read_text())["rows"]
    by_id = report["main"]["predictions"]
    table = Counter()
    for row in live:
        call = KIND.get(row["kind"], row["kind"])
        agrees = by_id[row["item"]] == call
        table[("agree" if agrees else "disagree", "pipeline right" if row["outcome"] == "correct" else "pipeline wrong")] += 1
    report["h5_disagreement_vs_pipeline"] = {f"{a} / {b}": n for (a, b), n in sorted(table.items())}

    Path(out).write_text(json.dumps(report, indent=1, ensure_ascii=False))
    main_ = report["main"]
    print(f"h5: {main_['right']}/{main_['n']} = {accuracy:.3f} (pipeline live {PIPELINE_H5}); gate "
          f"{'passed' if main_['gate_passed'] else 'NOT passed'}; per class {main_['per_class']}")
    print("confusion", main_["confusion (rows gold, cols predicted)"])
    print("leave-one-set-out", json.dumps(report["leave_one_set_out"]))
    print("disagreement vs pipeline (96 sessions)", report["h5_disagreement_vs_pipeline"])
    for c, words in report["top_words"].items():
        print(f"  {c}: {', '.join(words)}")


if __name__ == "__main__":
    main(sys.argv[1])
