"""ROUND-21 (R21-A) offline evaluation over the harness's readings (collab/ROUND-21-PLAN.md).

Usage:
  python3 evaluate.py triggers OUT.json     B2 with this checkout and no goal reads: the same calls as before (gate 1),
                                            and every reading that reaches the goal read -> triggers.json
  python3 evaluate.py b0 OUT.json           arm B0, code only: every triggered gap opens its goal (CLARIFY)
  python3 evaluate.py ask READS.json        one goal read per triggered request, gpt-4o-mini (model calls; announce)
  python3 evaluate.py a OUT.json READS.json arm A: the recorded reads applied
Compare any two runs with ../stability-round13-2026-10-21/harness.py compare OLD NEW.
"""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.path.insert(0, str(LOGS / "stability-round13-2026-10-21"))
import harness  # noqa: E402  (sets the import paths)

sys.path.insert(0, str(LOGS / "usage-fields-2026-10-21"))
import reask  # noqa: E402

replay_full = harness.replay_full
PRICE = reask.PRICE


def _run_tracking(out: str) -> list[dict]:
    """harness.run, noting each reading whose replay reached the goal read with no answer."""
    original, triggered = replay_full.replay, []

    def tracked(folder, task, payload, reread, found):
        before = len(replay_full.GOAL_TRIGGERED)
        call = original(folder, task, payload, reread, found)
        if len(replay_full.GOAL_TRIGGERED) > before:
            triggered.append({"where": str(folder), "task": task})
        return call

    replay_full.replay = tracked
    try:
        harness.run(out)
    finally:
        replay_full.replay = original
    rows = {row["where"]: row for row in json.loads(Path(out).read_text()).values()}
    return [{**item, "session": rows[item["where"]]["session"], "gold": rows[item["where"]]["gold"],
             "kind": rows[item["where"]]["kind"]} for item in triggered]


def triggers(out: str):
    found = _run_tracking(out)
    (HERE / "triggers.json").write_text(json.dumps(found, indent=1, ensure_ascii=False))
    from collections import Counter
    print(f"{len(found)} readings reach the goal read ({len({f['task'] for f in found})} requests); "
          f"gold {dict(Counter(f['gold'] for f in found))}")


def b0(out: str):
    from netzoo_agent_core.interpretation import goal_read

    def always_open(check, task, read):
        return check.model_copy(update={"open_goal_quote": check.results()[0].quote})

    goal_read.with_goal_read = always_open
    replay_full.GOAL_READS.update({item["task"]: {"asked_words": "", "result": "names_no_result"}
                                   for item in json.loads((HERE / "triggers.json").read_text())})
    harness.run(out)


def ask(out: str):
    reask._env()
    from netzoo_agent_core.graph.capability_check_call import _own_llm
    from netzoo_agent_core.graph.goal_read_call import GOAL_READ_MAX_TOKENS, invoke_goal_read
    from netzoo_agent_core.llm import _estimated_tokens

    model = os.environ["OPENROUTER_CAPABILITY_MODEL"]
    llm = _own_llm(model, GOAL_READ_MAX_TOKENS)
    tasks = list(dict.fromkeys(item["task"] for item in json.loads((HERE / "triggers.json").read_text())))

    def one(task):
        read, raw, input_text, output_text, error = invoke_goal_read(llm, task)
        usage = getattr(raw, "usage_metadata", None) or {}
        tokens = [usage.get("input_tokens") or _estimated_tokens(input_text),
                  usage.get("output_tokens") or _estimated_tokens(output_text)]
        return {"task": task, "read": read.model_dump() if read is not None else None,
                "error": f"{type(error).__name__}: {error}"[:300] if error else None, "tokens": tokens}

    with ThreadPoolExecutor(6) as pool:
        done = list(pool.map(one, tasks))
    tokens = [sum(d["tokens"][i] for d in done) for i in (0, 1)]
    usd = tokens[0] * PRICE["input"] + tokens[1] * PRICE["output"]
    Path(out).write_text(json.dumps({"model": model, "tokens": tokens, "usd": round(usd, 4), "reads": done},
                                    indent=1, ensure_ascii=False))
    print(f"{len(done)} requests read by {model}; failed {sum(d['read'] is None for d in done)}; US${usd:.4f}")


def arm_a(out: str, reads: str):
    replay_full.GOAL_READS.update({d["task"]: d["read"] for d in json.loads(Path(reads).read_text())["reads"]
                                   if d["read"] is not None})
    harness.run(out)


if __name__ == "__main__":
    args = sys.argv[1:]
    {"triggers": lambda: triggers(args[1]), "b0": lambda: b0(args[1]), "ask": lambda: ask(args[1]),
     "a": lambda: arm_a(args[1], args[2])}[args[0]]()
