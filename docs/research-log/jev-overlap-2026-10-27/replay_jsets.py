"""G1-G4 on the j1/j2 live readings in population.json (the harness replays only events.jsonl, not these traces).

Usage: NETZOO_JEV_OVERLAP=off|on python3 replay_jsets.py OUT.json
Each reading is replayed with this checkout's code (B2, `replay_full.replay`); no model call except Jev (cached in
jev-cache.json when NETZOO_JEV_OVERLAP_CACHE points there).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
SCRIPTS = HERE.parents[2] / "scripts"
OUT = sys.argv[1]
sys.argv = [sys.argv[0], "--scripts", str(SCRIPTS)]
sys.path.insert(0, str(LOGS / "false-accept-replay-2026-10-21"))
import replay_full  # noqa: E402

sys.path.insert(0, str(LOGS / "count-scope-r09-2026-10-20"))
from replay import _fits  # noqa: E402

LIVE = LOGS / "jev-guard-2026-10-27" / "live"
OVERLAP = {"JN8", "ON5", "QN5", "SN1"}


def readings():
    population = json.loads((HERE / "population.json").read_text())
    wanted = {(p["src"], p["session"], p["turn"]) for p in population if p["src"] != "replay"}
    for src, session, turn in sorted(wanted):
        folder = LIVE / src / session / turn
        found = [json.loads(line) for trace in sorted(folder.glob("trace-*.jsonl")) for line in open(trace)
                 if line.strip()]
        checks = [i for i, e in enumerate(found)
                  if e.get("event_type") == "routing.capability_checked" and e["payload"].get("proposal")]
        if not checks:
            continue
        payload = found[checks[0]]["payload"]["proposal"]
        reread = next((e["payload"] for e in found[checks[0] + 1:] if e.get("event_type") == "routing.capability_reread"),
                      None)
        users = [m["content"] for m in json.loads((folder / "session.json").read_text()).get("messages", [])
                 if m["role"] == "user"]
        task = next((t for t in reversed(users) if _fits(t, payload)), None)
        if task is not None:
            yield src, session, turn, folder, task, payload, reread, found


rows = []
for src, session, turn, folder, task, payload, reread, found in readings():
    try:
        call = replay_full.replay(folder, task, payload, reread, found)
    except Exception as error:  # noqa: BLE001 -- reported, never hidden
        call = {"kind": "error", "error": f"{type(error).__name__}: {error}"[:300]}
    recorded = next((e["payload"] for e in reversed(found) if e.get("event_type") == "core.decision"), {})
    item = session.split("-")[2]
    rows.append({"src": src, "session": session, "turn": turn, "item": item, "overlap": item in OVERLAP,
                 "recorded": recorded.get("kind"), "kind": call["kind"], "basis": call.get("basis"),
                 "error": call.get("error")})
Path(OUT).write_text(json.dumps(rows, indent=1))
for row in rows:
    print(f"{row['src']:5} {row['session']:18} {row['turn']} recorded {row['recorded']} -> {row['kind']}/{row['basis']}"
          + (f"  ERROR {row['error']}" if row["error"] else ""))
