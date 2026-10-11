"""Log 409: when routing and the check disagree about which workflow gives a requirement, which is right?

Usage (repository root): python docs/research-log/verdict-architecture-2026-10-12/arbitration.py

Per (session, gold requirement) of every labelled normal-operation round, using the recorded decision only:
- routing's offer: the selected action plus matched/hypothesis/recommended candidates (`candidates`),
  and its status (exact, ambiguous, fallback, ...);
- the check's credit: the workflows of the sheet entries in the requirement's `delivered_by`
  (re-read from the recorded session file, since the structure keeps only the status).

Gold: a positive's `by` workflows; a negative has none. Reports, by routing status, how often each side's
workflows include a gold one when they disagree, and how a whole request the check found no result in
fares when routing offered workflows.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = HERE.parent
ROOT = LOG.parents[1]
WORKTREES = ROOT.parent / ".worktrees"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(HERE))

from attribute import ROUNDS, SETS, final_labels  # noqa: E402
from netzoo_agent_core.capability_sheet import sheet_entries  # noqa: E402

ARM_TREES = {
    "n11": {"base": "netzoo-verdict-base", "cand": "netzoo-verdict-cand"},
    "b12": {"base": "netzoo-p1-base", "cand": "netzoo-p1-cand"},
    "m13": {"base": "netzoo-cm-base", "cand": "netzoo-cm-cand"},
    "r14": {"base": "netzoo-rr-base", "cand": "netzoo-rr-cand"},
    "x15": {"live": "netzoo-score-live"},
}
SAYS_GIVEN = {"GIVEN", "GIVEN_WITH_STEP", "GIVEN_IF_INPUT"}


def action(name: str) -> str:
    return "run_" + name.lower().replace("-", "_")


def span(task, words):
    words = (words or "").strip().rstrip(".,;:!?").strip()
    start = task.casefold().find(words.casefold()) if words else -1
    return None if start < 0 else (start, start + len(words))


def overlap(task, one, other):
    a, b = span(task, one), span(task, other)
    if a is None or b is None:
        return 0
    shared = min(a[1], b[1]) - max(a[0], b[0])
    return shared if shared > 0 and shared >= 0.5 * min(a[1] - a[0], b[1] - b[0]) else 0


def main() -> None:
    entries = sheet_entries()
    conflict = defaultdict(Counter)
    no_result = Counter()
    no_result_items = defaultdict(list)
    for tag, trees in ARM_TREES.items():
        folder = ROUNDS[tag]
        rows = json.loads((LOG / folder / "live" / f"{tag}-structure.json").read_text())
        labels = final_labels(tag, folder)
        items = {item["id"]: item for item in json.loads((LOG / SETS[tag]).read_text())["items"]}
        for sid, row in rows.items():
            if row.get("missing") or sid not in labels:
                continue
            path = WORKTREES / trees[row["arm"]] / ".netzoo" / "sessions" / f"{sid}.json"
            session = json.loads(path.read_text())
            decision = (session.get("plan") or {}).get("decision") or {}
            check = decision.get("capability_check") or {}
            users = [m["content"] for m in session.get("messages", []) if m.get("role") == "user"]
            task = users[-1] if users else ""
            offered = set(row.get("candidates") or []) | ({decision.get("action")} - {"no_tool", None})
            status = row.get("status") or "none"
            results = [r for r in check.get("requirements") or [] if r.get("kind") == "result"]
            gold = items[row["item"]]["requirements"]
            label = labels[sid].get("R") or []
            if not results and offered and not check.get("full_gap"):
                for requirement, given in zip(gold, label):
                    right = bool({action(n) for n in requirement.get("by", [])} & offered)
                    key = ("positive: routing offer includes gold" if right else "positive: routing offer wrong")\
                        if requirement["expect"] != "not_supported" else "negative: any offer is wrong"
                    no_result[key] += 1
                    no_result_items[key].append(f"{tag}-{row['item']}")
            for requirement, given in zip(gold, label):
                best = max(results, key=lambda r: overlap(task, requirement["words"], r["quote"]), default=None)
                if best is None or not overlap(task, requirement["words"], best["quote"]):
                    continue
                credited = {entries[k].action for k in best.get("delivered_by") or [] if k in entries}
                if not credited or not offered or credited & offered:
                    continue
                gold_actions = {action(n) for n in requirement.get("by", [])}
                if requirement["expect"] == "not_supported":
                    verdict = "negative: both wrong"
                else:
                    verdict = ("check right" if credited & gold_actions else "check wrong") + " / " + (
                        "routing right" if offered & gold_actions else "routing wrong")
                conflict[status][verdict] += 1
    print("Routing offered workflows, the check credited only others (per requirement):")
    for status, counts in sorted(conflict.items()):
        print(f"  routing {status}: {dict(counts)}")
    print()
    print("The check found no result anywhere in the request, routing offered workflows (per gold requirement):")
    for key, count in no_result.most_common():
        print(f"  {count:3d}  {key}   e.g. {sorted(set(no_result_items[key]))[:10]}")


if __name__ == "__main__":
    main()
