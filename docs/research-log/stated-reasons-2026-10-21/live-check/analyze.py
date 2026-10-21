"""ROUND-20 live check (no model calls): per session the core call against the expectation written before the round,
whether the same-run hold fired and on which rows, the capability model's calls, any execution, the full reply, and the
provider-reported cost.

Usage: python3 analyze.py > analysis.txt
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    items = {item["id"]: item for item in json.loads((HERE / "items.json").read_text())["items"]}
    total, matched = 0.0, 0
    for job in sorted((HERE / "live").glob("*/job.json")):
        meta = json.loads(job.read_text())
        folder = job.parent / "t1"
        events = [json.loads(line) for line in (folder / "events.jsonl").read_text().splitlines() if line.strip()]
        session = json.loads((folder / "session.json").read_text())
        latest = {e["event_type"]: e["payload"] for e in events}
        calls = (session.get("token_usage") or {}).get("calls", [])
        replies = [m["content"] for m in session.get("messages", []) if m["role"] == "assistant"]
        decision = latest.get("core.decision", {})
        usd = sum((c.get("cost_micro_usd") or 0) for c in calls) / 1e6
        total += usd
        expected = items[meta["item"]]["expected"][0]
        matched += decision.get("kind") == expected
        print(f"===== {meta['item']}: expected {expected} | live {decision.get('kind')} ({decision.get('basis')}) "
              f"{'MATCH' if decision.get('kind') == expected else 'DIFFERS'} | US${usd:.4f}")
        print(f"same-run hold: {latest.get('core.same_run_held', {}).get('held', 'not fired')}")
        print(f"capability calls: {[(c['role'], c['model'].split('/')[-1], c['status']) for c in calls if c['role'].startswith('capability')]}")
        print(f"executed: {any(e['event_type'].startswith('tool.') for e in events)}")
        print(f"Request: {items[meta['item']]['prompt']}\n")
        print((replies[-1] if replies else "(no reply)") + "\n")
    print(f"{matched}/{len(items)} as expected; provider-reported cost US${total:.4f}")


if __name__ == "__main__":
    main()
