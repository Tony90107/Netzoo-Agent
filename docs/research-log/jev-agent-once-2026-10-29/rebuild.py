"""O1 (ROUND.md): `agreed_fact_core` on recorded turns with the task state the turn started from (the previous turn's
session.json). No model calls. Usage: python3 rebuild.py > REBUILD.txt"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from netzoo_agent_core.cli.bootstrap import load_project_policy  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck  # noqa: E402
from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.contracts.fact_check import FactCheck  # noqa: E402
from netzoo_agent_core.graph.jev_guard_call import agent_doubts, agreed_fact_core, asked_sentences  # noqa: E402

CASES = [("jev-j6-2026-10-29/live/j6a/hb-j6a-X02-1", "t2", "j6", "X02"),
         ("jev-j6-2026-10-29/live/j6a/hb-j6a-X02-1", "t3", "j6", "X02"),
         ("jev-j6-2026-10-29/live/j6a/hb-j6a-X22-1", "t2", "j6", "X22"),
         ("jev-j6-2026-10-29/live/j6a/hb-j6a-X22-1", "t3", "j6", "X22"),
         ("r1-jev-agreement-2026-10-28/live/ra2/hb-ra2-W40-1", "t1", "j5", "W40"),
         ("r1-jev-agreement-2026-10-28/live/ra2/hb-ra2-J46-1", "t1", "j1", "J46")]
ITEMS = {"j6": LOGS / "jev-j6-2026-10-29/j6/items.json"}
APP = HERE.parents[4] / "netzoo_agent/docs/research-log"
ITEMS |= {"j5": APP / "jev-j5-2026-10-28/j5/items.json", "j1": APP / "jev-guard-2026-10-27/j1/items.json"}


def main():
    policy = load_project_policy()
    for folder, turn, name, item in CASES:
        path = LOGS / folder
        check = facts = jev = core = None
        for trace in glob.glob(str(path / turn / "trace-*.jsonl")):
            for line in open(trace):
                event = json.loads(line)
                kind, payload = event["event_type"], event.get("payload") or {}
                if kind == "routing.capability_checked" and check is None:
                    check = payload["check"]
                elif kind == "core.fact_check":
                    facts = payload
                elif kind == "core.jev_guard" or (kind == "core.jev_agent" and jev is None):
                    jev = payload.get("jev") or jev
                elif kind == "core.decision":
                    core = payload
        previous = path / f"t{int(turn[1:]) - 1}" / "session.json"
        state = json.loads(previous.read_text()).get("task_state") if previous.exists() else None
        before = core.get("evidence", {}).get("jev_agent") or core.get("evidence", {}).get("jev_guard") or {}
        start = CoreDecision(kind=before.get("kind_before", core["kind"]), basis=before.get("basis_before", core["basis"]),
                             workflows=core.get("workflows") or [])
        prompt = next(i["prompt"] for i in json.loads(ITEMS[name].read_text())["single"] if i["id"] == item)
        task = prompt if turn == "t1" else json.loads((path / turn / "session.json").read_text())["messages"][-2]["content"]
        decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.5, reason="r",
                                capability_check=CapabilityCheck.model_validate(check),
                                fact_check=FactCheck.model_validate({k: v for k, v in facts.items()
                                                                     if k in FactCheck.model_fields}))
        read = jev or {"kind": "ASK", "sentence": before.get("sentence"), "confidence": before.get("confidence", 0)}
        if before.get("sentence"):
            read = {**read, "kind": "ASK", "sentence": before["sentence"]}
        _, action = agreed_fact_core(start, read, task, decision, policy, asked_sentences(state), agent_doubts(state))
        print(f"{item} {turn}: recorded {core['kind']}/{core['basis']} -> rule now: {action}")


if __name__ == "__main__":
    main()
