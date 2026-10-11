"""Log 409: base vs candidate on every reply the candidate changed, one blind labeller for both versions.

Usage (repository root): python docs/research-log/verdict-architecture-2026-10-12/compare409.py

Reads replay/labels-A.json (and replay/labels-checked.json, my corrections, when present) with
replay/key.json, and the gold expectation of each requirement. Per version: false accepts (a negative
given, incl. PARTLY), false refusals, clear answers, unclear answers and contradictions; then the
sessions whose outcome changed.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = HERE.parent
sys.path.insert(0, str(HERE))

from attribute import SETS  # noqa: E402

SAYS_GIVEN = {"GIVEN", "GIVEN_WITH_STEP", "GIVEN_IF_INPUT"}


def outcome(expect: str, label: str) -> str:
    if expect == "not_supported":
        return "FA" if label in SAYS_GIVEN | {"PARTLY"} else "clear" if label == "NOT_GIVEN" else "unclear"
    return "FR" if label == "NOT_GIVEN" else "clear" if label in SAYS_GIVEN else "unclear"


def main() -> None:
    key = json.loads((HERE / "replay" / "key.json").read_text())
    labels = json.loads((HERE / "replay" / "labels-A.json").read_text())
    checked = HERE / "replay" / "labels-checked.json"
    labels.update(json.loads(checked.read_text()) if checked.exists() else {})
    by_session = {}
    for code, ref in key.items():
        session, tree, version = ref.split("|")
        by_session.setdefault((session, tree), {})[version] = labels[code]
    totals = {"base": Counter(), "cand": Counter()}
    lines = []
    for (session, tree), versions in sorted(by_session.items()):
        tag, item = session.split("-")[1], session.split("-")[3]
        gold = {i["id"]: i for i in json.loads((LOG / SETS[tag]).read_text())["items"]}[item]["requirements"]
        summary = {}
        for version in ("base", "cand"):
            label = versions[version]
            outcomes = [outcome(r["expect"], given) for r, given in zip(gold, label["R"])]
            totals[version].update(outcomes)
            totals[version]["contradiction"] += str(label.get("contradiction", "no")).startswith("yes")
            summary[version] = (label["R"], outcomes, str(label.get("contradiction", "no"))[:3])
        if summary["base"] != summary["cand"]:
            lines.append(f"{session}: {[r['expect'][:3] for r in gold]} base {summary['base']} -> cand {summary['cand']}")
    for version in ("base", "cand"):
        print(f"{version}: {dict(totals[version])}")
    print()
    print("\n".join(lines))


if __name__ == "__main__":
    main()
