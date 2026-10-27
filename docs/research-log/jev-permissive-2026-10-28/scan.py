"""Population scan (ROUND.md): every recorded reading with a result ask credited to an entry that takes one network kind
(the CONDOR entries) while its typed input_network is permissive (none / not_stated / missing).

Walks every recorded session folder under docs/research-log (events.jsonl or trace-*.jsonl with a
routing.capability_checked proposal). One row per (session, turn, quote); duplicates of the same session copied into
several logs are kept once (by session name + turn + quote).

Usage: python3 scan.py OUT.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from netzoo_agent_core.capability_sheet import sheet_entries  # noqa: E402

TAKES = {k for k, e in sheet_entries().items() if getattr(e, "input_network", None) is not None}
PERMISSIVE = (None, "none", "not_stated")


def proposal(folder: Path):
    for name in ("events.jsonl", "trace-*.jsonl"):
        for trace in sorted(folder.glob(name)):
            for line in open(trace, errors="replace"):
                if '"routing.capability_checked"' not in line:
                    continue
                event = json.loads(line)
                if event.get("event_type") == "routing.capability_checked" and event["payload"].get("proposal"):
                    return event["payload"]["proposal"]
    return None


rows, seen = [], set()
folders = {trace.parent for name in ("events.jsonl", "trace-*.jsonl") for trace in LOGS.rglob(name)}
for folder in sorted(folders):
    if HERE in folder.parents:
        continue
    payload = proposal(folder)
    if not payload:
        continue
    session, turn = (folder.parent.name, folder.name) if folder.name.startswith("t") and folder.name[1:].isdigit() \
        else (folder.name, "t1")
    users = [m["content"] for m in json.loads((folder / "session.json").read_text()).get("messages", [])
             if m["role"] == "user"] if (folder / "session.json").exists() else []
    for part in ("s1", "s2", "s3"):
        for ask in (payload.get(part) or {}).get("asks", []):
            credited = [k for k in ask.get("delivered_by", []) if k in TAKES]
            if not credited or ask.get("input_network") not in PERMISSIVE:
                continue
            key = (session, turn, ask.get("quote"))
            if key in seen:
                continue
            seen.add(key)
            rows.append({"session": session, "turn": turn, "where": str(folder.relative_to(LOGS)),
                         "typed": ask.get("input_network"), "credited": ask.get("delivered_by"),
                         "quote": ask.get("quote"), "has": [h for p in ("s1", "s2", "s3")
                                                            for h in (payload.get(p) or {}).get("has", [])],
                         "request": users[-1] if users else None})
Path(sys.argv[1]).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
print(len(folders), "folders;", len(rows), "readings;", len({r["session"].rsplit("-", 1)[0] for r in rows}), "sessions")
