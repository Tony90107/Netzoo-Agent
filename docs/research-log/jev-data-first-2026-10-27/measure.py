"""E1-E3 offline: the data-first step on each recorded form-only ASK (cases.json), with the guard's real typed read."""
import json
import glob
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.graph.jev_forms_call import data_first_core  # noqa: E402

RULED_OUT = {("j4g", "hb-j4g-S32-1", "t2"), ("ja1", "hb-ja1-S32-1", "t2"), ("jo1", "hb-jo1-Q18-1", "t1"),
             ("j4g", "hb-j4g-S10-1", "t2"), ("j4g", "hb-j4g-S10-1", "t3")}
ROOTS = {"j4g": "jev-j4-2026-10-27/live/j4g", "j3g": "jev-j3-2026-10-27/live/j3g", "jo1": "jev-overlap-2026-10-27/live/jo1",
         "jf1": "jev-forms-2026-10-27/live/jf1", "jfsmoke": "jev-forms-2026-10-27/live/jfsmoke",
         "ja1": "jev-answers-2026-10-27/live/ja1", "jasmoke": "jev-answers-2026-10-27/live/jasmoke"}

rows = []
for case in json.loads((HERE / "cases.json").read_text()):
    turn = HERE.parent / ROOTS[case["root"]] / case["session"] / case["turn"]
    payload = [json.loads(l)["payload"] for trace in sorted(turn.glob("trace-*.jsonl")) for l in open(trace)
               if '"core.decision"' in l and json.loads(l)["event_type"] == "core.decision"][-1]
    core = CoreDecision.model_validate(payload)
    after, action, typed = data_first_core(core, case["task"], None)
    ruled = (case["root"], case["session"], case["turn"]) in RULED_OUT
    rows.append({"case": f"{case['root']}/{case['session']}/{case['turn']}", "ruled_out": ruled, "action": action,
                 "after": f"{after.kind}/{after.basis}", "data": (typed or {}).get("data"),
                 "rules": {k: v for k, v in ((typed or {}).get("ruled_out") or {}).items()},
                 "kind_before": (after.evidence.get("jev_condition") or {}).get("kind_before"),
                 "cost": (typed or {}).get("cost", 0)})
(HERE / "measure.json").write_text(json.dumps(rows, indent=1))
for r in rows:
    print(f"{r['case']:28} {'RULED' if r['ruled_out'] else 'ok   '} -> {r['action']:14} {r['after']:22} data {r['data']}")
acceptable = [r for r in rows if not r["ruled_out"]]
ruled = [r for r in rows if r["ruled_out"]]
print("E1 data-acceptable converted:", [r["case"] for r in acceptable if r["action"] == "ask"], "of", len(acceptable))
print("E2 ruled-out converted:", sum(r["action"] == "ask" for r in ruled), "of", len(ruled))
print("E3 shapes:", {r["after"] for r in rows if r["action"] == "ask"}, "kind_before", {r["kind_before"] for r in rows if r["action"] == "ask"})
print("cost", round(sum(r["cost"] or 0 for r in rows), 5))
