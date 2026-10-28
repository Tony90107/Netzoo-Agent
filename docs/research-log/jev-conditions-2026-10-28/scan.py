"""Population scan (ROUND.md): every recorded reading whose request-level result-form condition (time_model=dynamic,
spatial=uses_neighbors, group_membership=several_groups) is quoted outside every ask's words, so the check gives it a
row of its own (`requirement_split.condition_requirements`). Approximation of the span test: the condition's quote is
in the request and inside no ask quote. One row per (session, turn, condition); copies kept once.

Usage: python3 scan.py OUT.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
LIMITS = {"time_model": "dynamic", "spatial": "uses_neighbors", "group_membership": "several_groups"}


def proposal(folder: Path):
    for name in ("events.jsonl", "trace-*.jsonl"):
        for trace in sorted(folder.glob(name)):
            for line in open(trace, errors="replace"):
                if '"routing.capability_checked"' in line:
                    event = json.loads(line)
                    if event.get("event_type") == "routing.capability_checked" and event["payload"].get("proposal"):
                        return event["payload"]["proposal"]
    return None


rows, seen = [], set()
folders = {trace.parent for name in ("events.jsonl", "trace-*.jsonl") for trace in LOGS.rglob(name)}
for folder in sorted(folders):
    if HERE in folder.parents or not (folder / "session.json").exists():
        continue
    payload = proposal(folder)
    if not payload:
        continue
    conditions = payload.get("conditions") or {}
    asks = [ask.get("quote", "") for part in ("s1", "s2", "s3") for ask in (payload.get(part) or {}).get("asks", [])]
    users = [m["content"] for m in json.loads((folder / "session.json").read_text()).get("messages", [])
             if m["role"] == "user"]
    session, turn = (folder.parent.name, folder.name) if folder.name[:1] == "t" and folder.name[1:].isdigit() \
        else (folder.name, "t1")
    for name, value in LIMITS.items():
        quote = (conditions.get(f"{name}_quote") or "").strip()
        if conditions.get(name) != value or not quote or any(quote in ask for ask in asks):
            continue
        if not any(quote in text for text in users):
            continue
        key = (session, turn, name)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"session": session, "turn": turn, "where": str(folder.relative_to(LOGS)), "attr": name,
                     "quote": quote, "asks": asks, "request": users[-1]})
Path(sys.argv[1]).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
print(len(rows), "readings;", len({r["session"] for r in rows}), "sessions")
