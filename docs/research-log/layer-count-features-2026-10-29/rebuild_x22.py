"""Rebuild j6 X22's recorded first readings (j6a, ao1) with this checkout's code. No model calls.
Usage (from docs/research-log): python3 layer-count-features-2026-10-29/rebuild_x22.py"""
import glob
import json
import sys

sys.path.insert(0, "false-accept-replay-2026-10-21")
import replay_full  # noqa: E402,F401  (sets the import paths)
from replay import _proposal  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402

TASK = next(i["prompt"] for i in json.load(open("jev-j6-2026-10-29/j6/items.json"))["single"] if i["id"] == "X22")
for path in sorted(glob.glob("jev-j6-2026-10-29/live/j6a/hb-j6a-X22-1/t1/trace-*.jsonl")
                   + glob.glob("jev-agent-once-2026-10-29/live/ao1/hb-ao1-X22-1/t1/trace-*.jsonl")):
    payload = next(json.loads(line)["payload"] for line in open(path) if '"routing.capability_checked"' in line)
    check, _ = build_capability_check(TASK, _proposal(payload["proposal"]), {})
    print("==", path.split("/")[-3])
    for row in check.results():
        print("  row:", row.quote[:60], "|", row.status, row.delivered_by, "| waits on",
              getattr(row, "depends_on", None), getattr(row, "outcomes", None))
