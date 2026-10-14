"""Item 4 (2026-10-14): the unread stretches after a sentence's first quote, and which hold a gold requirement.

Usage (repository root): python docs/research-log/coverage-2026-10-14/stretches.py

For every recorded first check (sessions from 2026-10-11 on) of a single-turn held-out item, each sentence where a
result was quoted is cut into the stretches no quote covers, after its first quote; each stretch's letter-run count
(any script) is compared with whether a gold requirement the check did not read lies in it. This calibrates the
re-read trigger: how many stretches each threshold would send (cost), and how many missed requirements it reaches.
No model is called.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from coverage import WORKTREES, gold_items, overlaps  # noqa: E402
from recent_misses import SINCE  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import _span  # noqa: E402
from netzoo_agent_core.interpretation.reread import unread_stretches, letter_runs  # noqa: E402


def main():
    gold = gold_items()
    by_count = collections.defaultdict(lambda: [0, 0])  # tokens -> [stretches, holding a missed requirement]
    sessions, triggered = 0, collections.Counter()
    holding = []
    seen = set()
    for session in sorted(WORKTREES.glob("*/.netzoo/sessions/*.json")):
        try:
            data = json.loads(session.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if float(data.get("created_at") or 0) < SINCE:
            continue
        users = [m["content"] for m in data.get("messages", []) if m.get("role") == "user"]
        item = gold.get(" ".join(users[0].split())) if len(users) == 1 else None
        path = session.parents[1] / "traces" / str(data.get("run_id")) / "events.jsonl"
        if item is None or not path.exists():
            continue
        first = next((json.loads(line)["payload"]["check"] for line in path.read_text().splitlines()
                      if '"routing.capability_checked"' in line), None)
        if first is None:
            continue
        task = users[0]
        check = CapabilityCheck.model_validate(first)
        key = (" ".join(task.split()), tuple(r.quote for r in check.requirements))
        if key in seen:
            continue
        seen.add(key)
        sessions += 1
        results = [_span(task, r.quote) for r in check.results()]
        missed = [_span(task, r["words"]) for r in item["requirements"]]
        missed = [span for span in missed if span and not any(overlaps(span, r) for r in results)]
        most = 0
        for start, end in unread_stretches(task, check):
            tokens = letter_runs(task[start:end])
            most = max(most, tokens)
            hit = any(overlaps((start, end), span) for span in missed)
            by_count[min(tokens, 10)][0] += 1
            by_count[min(tokens, 10)][1] += hit
            if hit:
                holding.append((tokens, item["id"], task[start:end]))
        for threshold in range(1, 8):
            triggered[threshold] += most >= threshold
    print(f"{sessions} distinct recorded first checks")
    print("tokens  stretches  holding a missed requirement")
    for tokens in sorted(by_count):
        print(f"{tokens:6} {by_count[tokens][0]:10} {by_count[tokens][1]:6}")
    for threshold in range(1, 8):
        reached = sum(1 for tokens, _, _ in holding if tokens >= threshold)
        print(f"threshold {threshold}: re-read in {triggered[threshold]}/{sessions} checks, reaches {reached}/{len(holding)}")
    for row in holding:
        print("  ", row)


if __name__ == "__main__":
    main()
