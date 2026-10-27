"""ROUND-2 measurement: rebuild each several_groups reading's check from its recorded proposal and render every result
row's line (`_status_line`), noting the overlap reason and layer 2. No model call except Jev (cached).

Usage: NETZOO_JEV_OVERLAP=on NETZOO_JEV_OVERLAP_CACHE=... python3 measure_reasons.py OUT.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
OUT = sys.argv[1]
sys.argv = [sys.argv[0], "--scripts", str(HERE.parents[2] / "scripts")]
sys.path.insert(0, str(LOGS / "false-accept-replay-2026-10-21"))
import replay_full  # noqa: E402,F401  (sets the import paths)

sys.path.insert(0, str(LOGS / "count-scope-r09-2026-10-20"))
from replay import _fits, _proposal  # noqa: E402

from netzoo_agent_core.interpretation.capability_check import _status_line, build_capability_check  # noqa: E402
from netzoo_agent_core.interpretation.reason_layers import is_unmatched  # noqa: E402

WRONG = "none returns overlapping memberships"
OVERLAP = {"JN8", "ON5", "QN5", "SN1"}


def folders():
    frozen = json.loads((LOGS / "jev-guard-2026-10-27" / "replay-frozen.json").read_text())
    where = {(r["session"], r["turn"]): Path(r["where"]) for r in frozen.values()}
    for p in json.loads((HERE / "population.json").read_text()):
        folder = (where.get((p["session"], p["turn"])) if p["src"] == "replay"
                  else LOGS / "jev-guard-2026-10-27" / "live" / p["src"] / p["session"] / p["turn"])
        if folder is not None:
            yield p["src"], p["session"], p["turn"], folder
    for turn in sorted((HERE / "live" / "jo1").glob("*/t*")):
        if turn.is_dir():
            yield "jo1", turn.parent.name, turn.name, turn


def reading(folder: Path):
    found = [json.loads(line) for name in ("events.jsonl", "trace-*.jsonl") for trace in sorted(folder.glob(name))
             for line in open(trace) if line.strip()]
    payload = next((e["payload"]["proposal"] for e in found if e.get("event_type") == "routing.capability_checked"
                    and e["payload"].get("proposal")), None)
    if payload is None:
        return None, None
    users = [m["content"] for m in json.loads((folder / "session.json").read_text()).get("messages", [])
             if m["role"] == "user"]
    return next((t for t in reversed(users) if _fits(t, payload)), None), payload


rows, seen = [], set()
for src, session, turn, folder in folders():
    if (session, turn) in seen:
        continue
    seen.add((session, turn))
    task, payload = reading(folder)
    if task is None:
        continue
    proposal = _proposal(payload)
    if proposal is None:
        continue
    check, _ = build_capability_check(task, proposal)
    lines = [_status_line(row, check=check) for row in check.results()]
    typed = [row.attrs.get("group_membership") for row in check.results()]
    if "several_groups" not in typed:
        continue
    item = session.split("-")[2]
    rows.append({"src": src, "session": session, "turn": turn, "item": item, "overlap": item in OVERLAP,
                 "overlap_reason": any(WRONG in line for line in lines),
                 "layer2": [is_unmatched(line) for line in lines], "lines": lines,
                 "doubted": [getattr(row, "doubted_forms", []) for row in check.results()]})
Path(OUT).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
for row in rows:
    print(f"{row['src']:7} {row['session']:20} {row['turn']} overlap={row['overlap']!s:5} "
          f"reason={row['overlap_reason']!s:5} doubted={row['doubted']}")
print(len(rows), "readings;", sum(r["overlap_reason"] for r in rows), "print the overlap reason")
