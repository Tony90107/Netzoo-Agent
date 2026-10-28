"""G1/G2 (ROUND.md): run `agreed_fact_core` on every recorded labelled t1 session (j1-j5, h9, h10) that has a Jev ASK
read and a fact check, from the recorded check, fact check, Jev read and call. No model calls.
Usage: python3 rebuild.py > REBUILD.txt"""
from __future__ import annotations

import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from netzoo_agent_core.cli.bootstrap import load_project_policy  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck  # noqa: E402
from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.contracts.fact_check import FactCheck  # noqa: E402
from netzoo_agent_core.graph.jev_guard_call import agreed_fact_core  # noqa: E402

TOP = HERE.parents[4]
APP = TOP / "netzoo_agent/docs/research-log"
MIS = TOP / ".worktrees/netzoo-misread/docs/research-log"
FILES = {"j1": APP / "jev-guard-2026-10-27/j1/items.json", "j2": APP / "jev-guard-2026-10-27/j2/items.json",
         "j3": APP / "jev-j3-2026-10-27/j3/items.json", "j4": APP / "jev-j4-2026-10-27/j4/items.json",
         "j5": APP / "jev-j5-2026-10-28/j5/items.json", "h9": MIS / "misread-detection-2026-10-25/h9/items.json",
         "h10": MIS / "misread-detection-2026-10-25/h10/items.json"}
SESSION = re.compile(r"hb-(?P<tag>[a-z0-9]+)-(?P<item>[A-Z]+\d+)-\d+/t1/")


def set_of(tag):
    return next((n for n in ("h10", "h9", "j1", "j2", "j3", "j4", "j5") if tag.startswith(n)), None)


def main():
    items = {(n, i["id"]): i for n, p in FILES.items() for i in json.loads(p.read_text())["single"]}
    policy = load_project_policy()
    seen, counts, changed = set(), Counter(), []
    for root in (APP, MIS, HERE.parents[1]):
        for path in sorted(glob.glob(str(root / "**/trace-*.jsonl"), recursive=True)
                           + glob.glob(str(root / "**/events.jsonl"), recursive=True)):
            found = SESSION.search(path)
            if not found or (name := set_of(found["tag"])) is None or (name, found["item"]) not in items:
                continue
            key = (name, found["item"], found["tag"])
            if key in seen:
                continue
            check = facts = jev = core = action = None
            for line in open(path, errors="replace"):
                event = json.loads(line)
                kind, payload = event.get("event_type"), event.get("payload") or {}
                if kind == "routing.capability_checked" and check is None:
                    check = payload["check"]
                elif kind == "core.fact_check":
                    facts = payload
                elif kind == "core.jev_guard":
                    jev = payload.get("jev")
                elif kind == "core.decision":
                    core = payload
                elif kind == "decision.recorded":
                    action = payload.get("action")
            if not (check and facts and jev and core and jev.get("kind") == "ASK"):
                continue
            seen.add(key)
            before = CoreDecision.model_validate({k: v for k, v in core.items() if k in CoreDecision.model_fields})
            if (core.get("evidence") or {}).get("jev_guard"):  # the guard acted: take the call it acted on
                before = before.model_copy(update={"kind": core["evidence"]["jev_guard"]["kind_before"],
                                                   "basis": core["evidence"]["jev_guard"]["basis_before"]})
            decision = TaskDecision(action=action or "no_tool", in_scope=True, should_execute=False, confidence=0.5,
                                    reason="r", capability_check=CapabilityCheck.model_validate(check),
                                    fact_check=FactCheck.model_validate(
                                        {k: v for k, v in facts.items() if k in FactCheck.model_fields}))
            item = items[(name, found["item"])]
            after, what = agreed_fact_core(before, jev, item["prompt"], decision, policy)
            counts[(item["expected_call"] == "ASK", what)] += 1
            if what == "ask":
                changed.append((name, found["item"], found["tag"], item["expected_call"], before.kind,
                                after.facts[0].question))
    print("sessions with a Jev ASK read:", len(seen))
    for (gold_ask, what), n in sorted(counts.items(), key=str):
        print(f"  gold {'ASK' if gold_ask else 'not ASK'} | {what}: {n}")
    print("changed to ASK:")
    for row in changed:
        print("  ", row)
    bad = [row for row in changed if row[3] != "ASK"]
    print(f"G1 non-ASK items changed: {len(bad)} -> {'PASS' if not bad else 'fail'}")
    print(f"G2 W40 / J46 changed: {sorted({r[1] for r in changed if r[1] in ('W40', 'J46')})}")


if __name__ == "__main__":
    main()
