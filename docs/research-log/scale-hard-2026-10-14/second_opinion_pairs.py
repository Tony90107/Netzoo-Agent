"""Item 3 (2026-10-14): recorded second-opinion pairs a stated scale now drops, and what they had answered.

Usage (repository root): python docs/research-log/scale-hard-2026-10-14/second_opinion_pairs.py

A second opinion (Logs 390, 397, 404) shows a workflow with its produces entries that fit the ask; a workflow the
ask's typed attributes rule out entirely is never asked about. With a hard scale, a workflow of the other scale is
now ruled out, so a recorded pair is dropped when none of its workflow's entries fits the requirement's scale. A
dropped pair answered `all` or `named` credited that workflow, so the outcome changes. No model is called.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from scale_empties import KNOWN, WORKTREES, gold_items  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import _fitting  # noqa: E402


def main():
    gold = gold_items()
    seen, dropped, total = set(), [], 0
    for session in sorted(WORKTREES.glob("*/.netzoo/sessions/*.json")):
        try:
            data = json.loads(session.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        users = [m["content"] for m in data.get("messages", []) if m.get("role") == "user"]
        events = session.parents[1] / "traces" / str(data.get("run_id")) / "events.jsonl"
        if len(users) != 1 or not events.exists():
            continue
        check = None
        for line in events.read_text().splitlines():
            event = json.loads(line)
            if event.get("event_type") in ("routing.capability_checked", "routing.capability_reread"):
                check = event["payload"].get("check") or check
            if event.get("event_type") != "routing.capability_second_opinion" or check is None:
                continue
            answers = event["payload"].get("answers") or []
            for pair, answer in zip(event["payload"]["pairs"], answers):
                if len(pair) != 3:  # recordings from before Log 390's (index, action, keys) pairs
                    continue
                index, action, _keys = pair
                requirement = check["requirements"][index] if index < len(check["requirements"]) else None
                if not requirement or not requirement.get("attrs"):
                    continue
                key = (" ".join(users[0].split()), requirement["quote"], action)
                if key in seen:
                    continue
                seen.add(key)
                total += 1
                produces = [k for k, found in KNOWN.items() if found.kind == "produces" and found.action == action]
                if not _fitting(produces, SimpleNamespace(**requirement["attrs"])):
                    found = gold.get(" ".join(users[0].split()))
                    dropped.append((action, answer, requirement["attrs"].get("scale"), requirement["quote"],
                                    users[0], found))
    print(f"{total} distinct recorded second-opinion pairs; {len(dropped)} now dropped")
    for action, answer, scale, quote, task, found in dropped:
        print(f"- {action} answered {answer!r}, scale {scale}: {quote!r}\n    task={task[:200]!r}"
              + (f"\n    gold={[(r['words'], r['expect'], r.get('by')) for r in found['requirements']]}" if found else ""))


if __name__ == "__main__":
    main()
