"""ROUND.md measurement: rebuild each population reading's check from its recorded proposal with the readers the flags
give (overlap, forms), and record each result row's status, wait, doubted forms and rendered line. No model call except
Jev (cached: NETZOO_JEV_OVERLAP_CACHE, NETZOO_JEV_FORMS_CACHE).

Usage: [NETZOO_JEV_OVERLAP=on] [NETZOO_JEV_FORMS=on] python3 measure_forms.py OUT.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
OUT = sys.argv[1]
POP = sys.argv[2] if len(sys.argv) > 2 else "population.json"
sys.argv = [sys.argv[0], "--scripts", str(HERE.parents[2] / "scripts")]
sys.path.insert(0, str(LOGS / "false-accept-replay-2026-10-21"))
import replay_full  # noqa: E402,F401  (sets the import paths)

sys.path.insert(0, str(LOGS / "count-scope-r09-2026-10-20"))
from replay import _fits, _proposal  # noqa: E402

from netzoo_agent_core.graph.jev_forms_call import forms_reader  # noqa: E402
from netzoo_agent_core.graph.jev_overlap_call import overlap_reader  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import _status_line, build_capability_check  # noqa: E402

CONTROLS = {"HN2", "NN7", "QN8", "RN1", "SN5", "QN10", "SN8", "Q18", "Q34", "C16"}


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
for p in json.loads((HERE / POP).read_text()):
    key = (p["session"], p["turn"])
    if key in seen:
        continue
    seen.add(key)
    task, payload = reading(Path(p["where"]))
    proposal = _proposal(payload) if task else None
    if proposal is None:
        rows.append({"session": p["session"], "turn": p["turn"], "error": "unreadable"})
        continue
    check, _ = build_capability_check(task, proposal, overlap_reader=overlap_reader(), forms_reader=forms_reader())
    results = check.results()
    item = p["session"].split("-")[2]
    rows.append({"session": p["session"], "turn": p["turn"], "src": p["src"], "item": item, "attrs": p["attrs"],
                 "control": item in CONTROLS, "credited": bool(p["credited"]),
                 "rows": [{"status": r.status, "depends_on": r.depends_on, "doubted": r.doubted_forms,
                           "line": _status_line(r, check=check)} for r in results]})
Path(OUT).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
for row in rows:
    if "error" in row:
        print(row["session"], row["turn"], row["error"])
        continue
    print(f"{row['session']:22} {row['turn']} {'CONTROL' if row['control'] else 'misread'} {row['attrs']} "
          f"credited={row['credited']!s:5} " + " | ".join(f"{r['status']}/{r['depends_on']}/{r['doubted']}"
                                                          for r in row["rows"]))
