"""ROUND.md measurement: J01's rows (before/after by the git checkout the script runs in) and the 3 written controls
through `condition_doubts` with the real readers. Flags from the environment; Jev reads cached in this folder.

Usage: python3 measure.py OUT.json
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
import replay_full  # noqa: E402,F401

sys.path.insert(0, str(LOGS / "count-scope-r09-2026-10-20"))
from replay import _fits, _proposal  # noqa: E402

from netzoo_agent_core.contracts.capability_check import CheckedRequirement  # noqa: E402
from netzoo_agent_core.graph.jev_forms_call import forms_reader, take_reads  # noqa: E402
from netzoo_agent_core.graph.jev_overlap_call import overlap_reader  # noqa: E402
from netzoo_agent_core.interpretation import jev_forms  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import _status_line, build_capability_check  # noqa: E402

out = {"readings": [], "controls": []}
for p in json.loads((HERE / "population-raw.json").read_text()):
    folder = LOGS / p["where"]
    found = [json.loads(line) for line in open(folder / "events.jsonl") if line.strip()]
    payload = next(e["payload"]["proposal"] for e in found if e.get("event_type") == "routing.capability_checked"
                   and e["payload"].get("proposal"))
    users = [m["content"] for m in json.loads((folder / "session.json").read_text())["messages"] if m["role"] == "user"]
    task = next(t for t in reversed(users) if _fits(t, payload))
    check, _ = build_capability_check(task, _proposal(payload), overlap_reader=overlap_reader(),
                                      forms_reader=forms_reader())
    out["readings"].append({"session": p["session"], "turn": p["turn"],
                            "rows": [{"quote": r.quote, "status": r.status, "delivered": r.delivered_by,
                                      "doubted": r.doubted_forms, "line": _status_line(r, check=check)}
                                     for r in check.results()],
                            "reads": [{k: r[k] for k in ("quote", "attr", "doubted")}
                                      | {"p": r["read"].get("probabilities")} for r in take_reads(task)]})
if hasattr(jev_forms, "condition_doubts"):
    for c in json.loads((HERE / "controls.json").read_text()):
        row = CheckedRequirement(quote=c["quote"], kind="result", status="not_available", attrs={c["attr"]: c["value"]})
        [after] = jev_forms.condition_doubts(c["task"], [row], forms_reader(), overlap_reader())
        out["controls"].append({**c, "doubted": after.doubted_forms,
                                "reads": [{k: r[k] for k in ("attr", "doubted")} | {"p": r["read"].get("probabilities")}
                                          for r in take_reads(c["task"])]})
Path(OUT).write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(json.dumps(out, indent=1, ensure_ascii=False))
