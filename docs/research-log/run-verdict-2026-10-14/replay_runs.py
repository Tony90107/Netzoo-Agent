"""Items 1-2 (2026-10-14): what the new run verdict does to every recorded run-path turn. No model is called.

Usage (repository root): python docs/research-log/run-verdict-2026-10-14/replay_runs.py

Reads the `routing.run_check_shadow` events of r17/r17b (run17 = heldout17 as run commands, worktree
`.worktrees/netzoo-rp-shadow`), rebuilds each turn's final check from the recorded result rows, and applies the
current `run_check_verdict`. Gold is heldout17's (Log 411): `neg` when every requirement is not_supported, `pos` when
none is, else `mixed`.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TREE = ROOT.parent / ".worktrees" / "netzoo-rp-shadow" / ".netzoo"
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.capability_sheet import sheet_entries  # noqa: E402
from netzoo_agent_core.contracts.capability_check import (  # noqa: E402
    APPROVING_RUN_VERDICTS, CapabilityCheck, CheckedRequirement,
)
from netzoo_agent_core.interpretation.run_check import run_check_verdict  # noqa: E402

GOLD = {item["id"]: item for item in json.loads((ROOT / "docs/research-log/rescore-2026-10-12/heldout17.json")
                                                .read_text())["items"]}
KEY = {}
for key, found in sheet_entries().items():
    if found.kind == "produces" and found.action:
        KEY.setdefault(found.action, key)


def gold_class(item):
    expects = {r["expect"] for r in item["requirements"]}
    return "neg" if expects == {"not_supported"} else "pos" if "not_supported" not in expects else "mixed"


def rebuilt(payload):
    rows = [CheckedRequirement(quote=row["quote"], kind="result", status=row["status"],
                               delivered_by=[KEY[action] for action in row["credited"]]) for row in payload["results"]]
    return CapabilityCheck(requirements=rows, unchecked=payload.get("unchecked") or [],
                           full_gap=bool(rows) and all(row.status == "not_available" for row in rows))


def main():
    sessions = {}
    for path in sorted((TREE / "sessions").glob("ve-r17*-shadow-*.json")):
        data = json.loads(path.read_text())
        sessions[data.get("session_id") or path.stem] = path.stem
    table = []
    for events in sorted((TREE / "traces").glob("*/events.jsonl")):
        session, shadow = None, None
        for line in events.read_text().splitlines():
            event = json.loads(line)
            if event.get("event_type") == "run.started":
                session = (event.get("payload") or {}).get("session_id")
            if event.get("event_type") == "routing.run_check_shadow":
                shadow = event["payload"]
        if shadow is None or session is None:
            continue
        item = session.split("-shadow-")[1].rsplit("-", 1)[0]
        check = None if shadow["check_status"] != "ok" else rebuilt(shadow)
        new = run_check_verdict(check, shadow["action"])["verdict"]
        old_runs = shadow["verdict"] != "gap"
        new_runs = new in APPROVING_RUN_VERDICTS
        table.append((session, gold_class(GOLD[item]), shadow["action"], shadow["verdict"], new, old_runs, new_runs))
    print(f"{'session':28} {'gold':5} {'action':20} {'3578b00':14} {'now':14} run(before→now)")
    for row in sorted(table):
        print(f"{row[0]:28} {row[1]:5} {row[2]:20} {row[3]:14} {row[4]:14} {row[5]}→{row[6]}")
    changed = [row for row in table if row[5] != row[6]]
    print(f"\n{len(table)} recorded run turns; {len(changed)} change: "
          + ", ".join(f"{row[0]} ({row[1]}, {row[3]}→{row[4]})" for row in changed))
    print("by gold:", dict(collections.Counter((row[1], row[6]) for row in table)))


if __name__ == "__main__":
    main()
