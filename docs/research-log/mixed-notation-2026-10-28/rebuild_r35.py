"""M2 (ROUND.md): rebuild R35's recorded first readings (fc1 and the j3 arms) with this checkout's code. No model
calls. Usage (from docs/research-log): python3 mixed-notation-2026-10-28/rebuild_r35.py"""
import glob
import json
import sys

sys.path.insert(0, "false-accept-replay-2026-10-21")
import replay_full  # noqa: E402,F401  (sets the import paths)
from replay import _proposal  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402

TASK = next(i["prompt"] for i in json.load(open("jev-j3-2026-10-27/j3/items.json"))["single"] if i["id"] == "R35")
paths = (sorted(glob.glob("feature-count-doubts-2026-10-28/live/fc1/hb-fc1-R35-1/t1/trace-*.jsonl"))
         + sorted(glob.glob("jev-j3-2026-10-27/live/*/hb-j3*-R35-1/t1/trace-*.jsonl")))
for path in paths:
    payload = next(json.loads(line)["payload"] for line in open(path)
                   if '"routing.capability_checked"' in line)
    check, _ = build_capability_check(TASK, _proposal(payload["proposal"]), {})
    print("==", path.split("/")[-3])
    for row in check.results():
        print("  row:", row.quote[:70], "|", row.status, row.delivered_by, "| method", json.dumps(row.method),
              "| waits on", getattr(row, "depends_on", None), getattr(row, "outcomes", None))
    print("  unsure:", [(fact.property, fact.values, fact.quote[:40]) for fact in check.facts if fact.state == "unsure"])
