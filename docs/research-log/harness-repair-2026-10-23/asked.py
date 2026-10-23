"""P1 (harness repair, 2026-10-23): what each recorded ASK turn asks, with this checkout's code or another's.

The B2 replay compares calls only; P1 changes which questions an agent turn asks (a wait on other words is asked beside
the agent's questions or queued). This records, per reading, the questions `decide_core` asks and P1's obligations.

Usage:
  python3 asked.py run OUT.json [--scripts DIR]     DIR: another checkout's scripts (the frozen 91a8c2d9)
  python3 asked.py compare OLD.json NEW.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "stability-round13-2026-10-21"))


def run(out: str):
    import harness  # noqa: E402  (sets the import paths; honours --scripts)
    import netzoo_agent_core.interpretation.core_decision as core_decision

    by_session, core = harness._gold()
    original, seen, rows = core_decision.decide_core, {}, {}

    def spy(decision, task="", **kwargs):
        seen["core"] = original(decision, task, **kwargs)
        return seen["core"]

    for key, folder, sid, task, payload, reread, found, _n in harness.readings():
        core_decision.decide_core = spy
        try:
            harness.replay_full.replay(folder, task, payload, reread, found)
        except Exception:  # noqa: BLE001 -- the three old-schema T01 readings (harness.py reports them)
            continue
        finally:
            core_decision.decide_core = original
        call = seen["core"]
        rows[key] = {"session": sid, "turn": folder.name, "gold": harness._label(sid, by_session, core),
                     "kind": call.kind, "basis": call.basis, "asked": [fact.question for fact in call.facts],
                     "obligations": call.evidence.get("obligations")}
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    print(f"{len(rows)} readings")


def compare(old_path: str, new_path: str):
    old, new = json.loads(Path(old_path).read_text()), json.loads(Path(new_path).read_text())
    shared = sorted(set(old) & set(new))
    counts, queued = Counter(), Counter()
    for key in shared:
        o, n = old[key], new[key]
        if n["obligations"]:
            for item in n["obligations"]:
                queued[item["status"] if not item["asked_as"] else "covered by an asked question"] += 1
        if (o["kind"], o["asked"]) == (n["kind"], n["asked"]):
            continue
        added = [q for q in n["asked"] if q not in o["asked"]]
        dropped = [q for q in o["asked"] if q not in n["asked"]]
        counts["kind changed" if o["kind"] != n["kind"] else "questions changed"] += 1
        print(f"{n['session']}/{n['turn']} gold {n['gold']}: {o['kind']}/{o['basis']} -> {n['kind']}/{n['basis']}")
        for q in added:
            print(f"   + {q}")
        for q in dropped:
            print(f"   - {q}")
    print(f"{len(shared)} readings; {dict(counts) or 'no change'}; obligations recorded: {dict(queued)}")


if __name__ == "__main__":
    {"run": lambda: run(sys.argv[2]), "compare": lambda: compare(sys.argv[2], sys.argv[3])}[sys.argv[1]]()
