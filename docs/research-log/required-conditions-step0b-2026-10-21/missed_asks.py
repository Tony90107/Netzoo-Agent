"""Why each DO turn whose blind gold is ASK did not ask (no model calls): the recorded fact agent's outcome on that
turn -- not run (recordings before phase 2 had no fact agent), blocked by the token budget, its question accepted but
settled by the input check (left to the files), rejected, or none proposed. Usage: python3 missed_asks.py MEASURE.json"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parents[2]
MAIN = WT.parents[1] / "netzoo_agent"


def why(where: str) -> tuple[str, str]:
    folder = next((p for root in (WT, MAIN) if (p := root / where).joinpath("events.jsonl").exists()), None)
    events = [json.loads(line) for line in open(folder / "events.jsonl") if line.strip()]
    fact = next((e["payload"] for e in reversed(events) if e["event_type"] == "core.fact_check"), None)
    if fact is None:
        return "no fact agent in this recording", ""
    if fact.get("status") == "blocked":
        return "fact agent blocked by the token budget", ""
    accepted = fact.get("accepted") or []
    if accepted and all(item.get("settled_by_input_check") for item in accepted):
        return "question found, left to the input file check", accepted[0].get("question", "")
    if accepted:
        return "question accepted, not asked", accepted[0].get("question", "")
    if fact.get("rejected"):
        return "every proposed question rejected", str(fact["rejected"][0])[:160]
    return "no question proposed", ""


def main(path):
    rows = json.loads(Path(path).read_text())["rows"]
    turns, items = Counter(), {}
    for row in rows:
        if row["gold"] != "ASK":
            continue
        reason, question = why(row["where"])
        turns[(row["gold_fact"], reason)] += 1
        items.setdefault((row["gold_fact"], reason), set()).add(row["item"])
        print(f"{row['item']:4} {row['gold_fact']:14} {reason:46} {row['where'].split('/live/')[-1][:34]} {question[:90]}")
    print()
    for (fact, reason), count in sorted(turns.items(), key=str):
        print(f"{fact:14} {reason:46} turns {count:2}  items {sorted(items[(fact, reason)])}")


if __name__ == "__main__":
    main(sys.argv[1])
