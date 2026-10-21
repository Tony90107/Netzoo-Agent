"""ROUND-23 sizing: the R21-A goal read asked on every current-shape labelled reading decided by goal_unclear (CLARIFY)
or results_given (DO), to see whether it agrees with the right calls and disagrees with the wrong ones.

Usage: python3 size.py READS.json    (one gpt-4o-mini call per distinct request; announce first)
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.path.insert(0, str(LOGS / "stability-round13-2026-10-21"))
import harness  # noqa: E402

sys.path.insert(0, str(LOGS / "usage-fields-2026-10-21"))
import reask  # noqa: E402


def era(session: str) -> str:
    m = re.match(r"cj-([^-]+)-", session)
    if m:
        return "current" if m.group(1) in ("p4b", "p4c", "p5", "p5r", "g4o1", "g4o2") else "old"
    return "current" if session.startswith("hb-h") else "other"


def main(out: str):
    rows = json.loads((LOGS / "input-constraints-2026-10-21/harness-r4.json").read_text())
    want = {r["where"]: r for r in rows.values() if r["gold"] and era(r["session"]) == "current"
            and r["basis"] in ("goal_unclear", "results_given")}
    readings = []
    for key, folder, sid, task, payload, reread, found, _n in harness.readings():
        if str(folder) in want:
            r = want[str(folder)]
            readings.append({"session": sid, "task": task, "gold": r["gold"], "kind": r["kind"], "basis": r["basis"]})
    reask._env()
    from netzoo_agent_core.graph.capability_check_call import _own_llm
    from netzoo_agent_core.graph.goal_read_call import GOAL_READ_MAX_TOKENS, invoke_goal_read
    from netzoo_agent_core.llm import _estimated_tokens

    model = os.environ["OPENROUTER_CAPABILITY_MODEL"]
    llm = _own_llm(model, GOAL_READ_MAX_TOKENS)
    tasks = list(dict.fromkeys(r["task"] for r in readings))

    def one(task):
        read, raw, input_text, output_text, error = invoke_goal_read(llm, task)
        usage = getattr(raw, "usage_metadata", None) or {}
        return task, (read.model_dump() if read else None), [usage.get("input_tokens") or _estimated_tokens(input_text),
                                                              usage.get("output_tokens") or _estimated_tokens(output_text)]

    with ThreadPoolExecutor(6) as pool:
        done = list(pool.map(one, tasks))
    reads = {task: read for task, read, _t in done}
    tokens = [sum(t[i] for *_r, t in done) for i in (0, 1)]
    usd = tokens[0] * reask.PRICE["input"] + tokens[1] * reask.PRICE["output"]
    for r in readings:
        r["read"] = reads.get(r["task"])
    Path(out).write_text(json.dumps({"model": model, "usd": round(usd, 4), "readings": readings}, indent=1,
                                    ensure_ascii=False))
    print(f"{len(tasks)} requests read; US${usd:.4f}")
    table = Counter((r["basis"], r["gold"], (r["read"] or {}).get("result")) for r in readings)
    for k, v in sorted(table.items(), key=str):
        print(f"  {v:3} {k[0]:14} gold {k[1]:8} read {k[2]}")


if __name__ == "__main__":
    main(sys.argv[1])
