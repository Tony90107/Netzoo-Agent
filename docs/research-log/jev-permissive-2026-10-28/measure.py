"""ROUND.md measurement, adapted from jev-forms-r2/measure.py: rebuild each population reading's check from its recorded
proposal with the readers the flags give (overlap, forms), and record each result row's status, wait and Jev's
input_network reads. No model call except Jev (cached: NETZOO_JEV_OVERLAP_CACHE, NETZOO_JEV_FORMS_CACHE).

Usage: [NETZOO_JEV_OVERLAP=on] [NETZOO_JEV_FORMS=on] python3 measure.py OUT.json
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

from netzoo_agent_core.graph.jev_forms_call import forms_reader, take_reads  # noqa: E402
from netzoo_agent_core.graph.jev_overlap_call import overlap_reader  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import _status_line, build_capability_check  # noqa: E402


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
for p in json.loads((HERE / "population.json").read_text()):
    key = (p["session"], p["turn"])
    if key in seen:
        continue
    seen.add(key)
    task, payload = reading(LOGS / p["where"])
    proposal = _proposal(payload) if task else None
    if proposal is None:
        rows.append({"session": p["session"], "turn": p["turn"], "item": p["item"], "label": p["label"],
                     "error": "unreadable"})
        continue
    check, _ = build_capability_check(task, proposal, overlap_reader=overlap_reader(), forms_reader=forms_reader())
    reads = [r for r in take_reads(task) if r["attr"] == "input_network"]
    rows.append({"session": p["session"], "turn": p["turn"], "item": p["item"], "label": p["label"],
                 "rows": [{"quote": r.quote, "status": r.status, "depends_on": r.depends_on,
                           "delivered": r.delivered_by, "line": _status_line(r, check=check)}
                          for r in check.results()],
                 "network_reads": [{"options": r["options"], "choice": r["read"].get("choice"),
                                    "probabilities": r["read"].get("probabilities"), "doubted": r["doubted"]}
                                   for r in reads]})
Path(OUT).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
for row in rows:
    if "error" in row:
        print(row["session"], row["turn"], row["error"])
        continue
    waits = [r["depends_on"] for r in row["rows"]]
    reads = [(r["choice"], r["doubted"]) for r in row["network_reads"]]
    print(f"{row['session']:28} {row['turn']} {row['label']:15} " + " | ".join(
        f"{r['status']}/{r["depends_on"]}" for r in row["rows"]) + f"  reads={reads}")
