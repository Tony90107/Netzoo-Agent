"""B4: rebuild the recorded checks of j4g S32 t2, S39 t1 and j3g R18 t2 with both readers, and count the questions per
dimension `_facts` gives (before: one per row)."""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.argv = [sys.argv[0], "--scripts", str(HERE.parents[2] / "scripts")]
sys.path.insert(0, str(LOGS / "false-accept-replay-2026-10-21"))
import replay_full  # noqa: E402,F401
sys.path.insert(0, str(LOGS / "count-scope-r09-2026-10-20"))
from replay import _fits, _proposal  # noqa: E402

from netzoo_agent_core.graph.jev_forms_call import forms_reader  # noqa: E402
from netzoo_agent_core.graph.jev_overlap_call import overlap_reader  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402
from netzoo_agent_core.interpretation.core_decision import _facts  # noqa: E402

out = {}
for path in ("jev-j4-2026-10-27/live/j4g/hb-j4g-S32-1/t2", "jev-j4-2026-10-27/live/j4g/hb-j4g-S39-1/t1",
             "jev-j3-2026-10-27/live/j3g/hb-j3g-R18-1/t2"):
    folder = LOGS / path
    found = [json.loads(line) for trace in sorted(folder.glob("trace-*.jsonl")) for line in open(trace)]
    payload = next(e["payload"]["proposal"] for e in found if e["event_type"] == "routing.capability_checked"
                   and e["payload"].get("proposal"))
    recorded = [e["payload"] for e in found if e["event_type"] == "core.decision"][-1]
    users = [m["content"] for m in json.loads((folder / "session.json").read_text())["messages"] if m["role"] == "user"]
    task = next(t for t in reversed(users) if _fits(t, payload))
    check, _ = build_capability_check(task, _proposal(payload), overlap_reader=overlap_reader(),
                                      forms_reader=forms_reader())
    before = Counter(f.get("depends_on") for f in recorded.get("facts") or [])
    after = Counter(f.depends_on for f in _facts(check, task=task))
    out[path] = {"recorded": dict(before), "rebuilt": dict(after)}
    print(path, "recorded", dict(before), "-> rebuilt", dict(after))
(HERE / "merge.json").write_text(json.dumps(out, indent=1))
