"""Item 4 (2026-10-14): gold requirements missed by sessions recorded on or after 2026-10-11 (Log 406 re-read live),
with what the re-read trigger did on each.

Usage (repository root): python docs/research-log/coverage-2026-10-14/recent_misses.py
"""
from __future__ import annotations

import collections
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from coverage import WORKTREES, gold_items, place  # noqa: E402
from netzoo_agent_core.interpretation.reread import _covered  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import request_sentences  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck  # noqa: E402


_WORD = re.compile(r"[A-Za-z][A-Za-z-]{3,}")  # the re-read trigger before item 4 (Log 406)
SINCE = datetime(2026, 10, 11, tzinfo=timezone(timedelta(hours=8))).timestamp()


def events_of(path: Path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    gold = gold_items()
    counts = collections.Counter()
    rows = []
    for session in sorted(WORKTREES.glob("*/.netzoo/sessions/*.json")):
        try:
            data = json.loads(session.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if float(data.get("created_at") or 0) < SINCE:
            continue
        users = [m["content"] for m in data.get("messages", []) if m.get("role") == "user"]
        if len(users) != 1 or not data.get("run_id"):
            continue
        item = gold.get(" ".join(users[0].split()))
        path = session.parents[1] / "traces" / str(data["run_id"]) / "events.jsonl"
        if item is None or not path.exists():
            continue
        events = events_of(path)
        first = next((e["payload"]["check"] for e in events if e["event_type"] == "routing.capability_checked"), None)
        reread = [e["payload"] for e in events if e["event_type"] == "routing.capability_reread"]
        last = reread[-1]["check"] if reread else first
        if last is None:
            continue
        counts["sessions"] += 1
        task = users[0]
        for requirement in item["requirements"]:
            where = place(task, requirement["words"], last)
            counts[(requirement["expect"], where)] += 1
            if where == "read":
                continue
            # The unquoted rest of the requirement's sentence, as the trigger counts it.
            check = CapabilityCheck.model_validate(first)
            covered = _covered(task, check)
            sentence = next(((s, e) for s, e in request_sentences(task) if task.find(requirement["words"]) in range(s, e)),
                            None)
            rest = ("".join(" " if covered[sentence[0] + i] else ch for i, ch in enumerate(task[sentence[0]:sentence[1]]))
                    if sentence else "")
            rows.append((item["set"], item["id"], session.parents[2].name, requirement["expect"], where,
                         requirement["words"], len(_WORD.findall(rest)), bool(reread),
                         reread[-1]["passages"] if reread else None, " ".join(rest.split())))
    print("sessions:", counts.pop("sessions"))
    for expect in ("supported", "with_step", "needs_input", "not_supported"):
        row = {where: n for (e, where), n in counts.items() if e == expect}
        total = sum(row.values())
        if total:
            print(f"{expect:14} n={total:4} read={row.get('read', 0) / total:.0%}",
                  {k: v for k, v in sorted(row.items()) if k != "read"})
    for row in rows:
        print(f"- {row[0]} {row[1]} ({row[2]}) [{row[3]}] {row[4]}: {row[5]!r}\n    unquoted words={row[6]} "
              f"reread={row[7]} passages={row[8]}\n    rest={row[9]!r}")


if __name__ == "__main__":
    main()
