"""Log 413: rebuild every recorded c18 candidate check from its recorded proposal with one checkout's code.

Usage (repository root):
  REPLAY_CODE_ROOT=<checkout> python docs/research-log/overlap-groups-2026-10-12/replay413.py <out.json>

Each heldout18 (c18) session of the Log 412 candidate arm recorded the check model's proposal (trace
`routing.capability_checked`). Rebuilding the check from it with the checkout's code shows what the code
alone decides -- no model is called. Run with a1bb3b3 (Log 412) and with the candidate; the rows that differ
are the change. Re-reads and second opinions are not replayed; the rows say whether the recording had one.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CODE_ROOT = Path(os.environ.get("REPLAY_CODE_ROOT") or ROOT)
sys.path.insert(0, str(CODE_ROOT / "scripts"))
TREE = ROOT.parent / ".worktrees" / "netzoo-rc-cand" / ".netzoo"

from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402


def main() -> None:
    rows = []
    for path in sorted((TREE / "sessions").glob("ve-c18-cand-*.json")):
        session = json.loads(path.read_text())
        events = [json.loads(line) for line in (TREE / "traces" / session["run_id"] / "events.jsonl").read_text().splitlines()]
        checked = [e for e in events if e["event_type"] == "routing.capability_checked"]
        if not checked:
            continue
        task = [m["content"] for m in session["messages"] if m["role"] == "user"][-1]
        raw = checked[-1]["payload"]["proposal"]
        count = sum(1 for key in raw if key[1:].isdigit())
        check, _ = build_capability_check(task, proposal_model(count).model_validate(raw))
        rows.append({"session": path.stem, "full_gap": check.full_gap, "conditions": check.conditions,
                     "results": [(r.quote, r.status) for r in check.results()],
                     "later_steps": sorted({e["event_type"] for e in events
                                            if e["event_type"] in ("routing.capability_reread",
                                                                   "routing.capability_second_opinion")})})
    Path(sys.argv[1]).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    print(f"{len(rows)} rows")


if __name__ == "__main__":
    main()
