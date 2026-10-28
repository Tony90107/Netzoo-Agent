"""A2 (ROUND.md): `answered_check` on ad1's recorded turn-2 checks with the task state the turn started from and the
turn's own request text. No model calls. Usage (from docs/research-log): python3 answered-counts-2026-10-29/rebuild.py"""
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from netzoo_agent_core.contracts.capability_check import CapabilityCheck  # noqa: E402
from netzoo_agent_core.interpretation.task_answers import answered_check  # noqa: E402

for item in ("X22", "X02"):
    folder = Path(f"asked-doubts-2026-10-29/live/ad1/hb-ad1-{item}-1")
    trace = glob.glob(str(folder / "t2/trace-*.jsonl"))[0]
    check = next(json.loads(line)["payload"]["check"] for line in open(trace) if '"routing.capability_checked"' in line)
    session = json.loads((folder / "t2/session.json").read_text())
    task = [m["content"] for m in session["messages"] if m["role"] == "user"][-1]
    state = session["task_state"]  # after turn 2's binding: the answered fact is known
    after = answered_check(CapabilityCheck.model_validate(check), state, task)
    for row in after.results():
        print(item, "t2:", row.status, row.delivered_by, json.dumps(row.method)[:120], [l[:90] for l in row.limits])
