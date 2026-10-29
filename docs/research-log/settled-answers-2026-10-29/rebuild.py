"""S2 (ROUND.md): the stated conditions recorded in j6 X06 t3's condition check, filtered with the task state the
turn started from (t2's session). No model calls. Usage (from docs/research-log): python3 settled-answers-2026-10-29/rebuild.py"""
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from netzoo_agent_core.interpretation.task_answers import settled_quotes, without_settled  # noqa: E402

folder = Path("jev-j6-2026-10-29/live/j6a/hb-j6a-X06-1")
trace = glob.glob(str(folder / "t3/trace-*.jsonl"))[0]
check = next(json.loads(line)["payload"] for line in open(trace) if '"routing.capability_condition_check"' in line)
stated = list(dict.fromkeys(pair[3] for pair in check["pairs"]))
state = json.loads((folder / "t2/session.json").read_text())["task_state"]
print("recorded answers:", check["answers"], "full_gap:", check["full_gap"])
print("recorded stated conditions:", stated)
print("settled answers (t2 state):", settled_quotes(state))
print("stated after the change:", without_settled(stated, state))
