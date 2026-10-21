"""ROUND-22 (R22-B) offline evaluation over the harness's readings.

Usage:
  python3 evaluate_settings.py triggers OUT.json      B2 with no settings reads: the same calls as R22-A (gate), and
                                                      every (request, workflow) that reaches the read -> settings-triggers.json
  python3 evaluate_settings.py ask READS.json         one settings read per trigger, gpt-4o-mini (model calls; announce)
  python3 evaluate_settings.py apply OUT.json READS.json   the reads applied
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
import harness  # noqa: E402

sys.path.insert(0, str(LOGS / "usage-fields-2026-10-21"))
import reask  # noqa: E402

replay_full = harness.replay_full
replay_full.GOAL_READS.update({d["task"]: d["read"] for d in json.loads(
    (LOGS / "goal-read-2026-10-21/reads.json").read_text())["reads"] if d["read"]})


def triggers(out: str):
    original, found = replay_full.replay, []

    def tracked(folder, task, payload, reread, events):
        before = len(replay_full.SETTINGS_TRIGGERED)
        call = original(folder, task, payload, reread, events)
        found.extend({"where": str(folder), "task": t, "workflow": w} for t, w in replay_full.SETTINGS_TRIGGERED[before:])
        return call

    replay_full.replay = tracked
    try:
        harness.run(out)
    finally:
        replay_full.replay = original
    rows = {row["where"]: row for row in json.loads(Path(out).read_text()).values()}
    found = [{**item, "session": rows[item["where"]]["session"], "gold": rows[item["where"]]["gold"],
              "kind": rows[item["where"]]["kind"]} for item in found]
    (HERE / "settings-triggers.json").write_text(json.dumps(found, indent=1, ensure_ascii=False))
    print(f"{len(found)} readings reach the settings read ({len({(f['task'], f['workflow']) for f in found})} requests)")
    for item in found:
        print(f"  {item['gold']!s:8} {item['kind']:9} {item['session']:20} {item['workflow']:8} {item['task'][:70]}")


def ask(out: str):
    reask._env()
    from netzoo_agent_core.graph.capability_check_call import _own_llm
    from netzoo_agent_core.graph.settings_read_call import invoke_settings_read
    from netzoo_agent_core.llm import _estimated_tokens

    model = os.environ["OPENROUTER_CAPABILITY_MODEL"]
    llm = _own_llm(model, 400)
    pairs = list(dict.fromkeys((t["task"], t["workflow"]) for t in json.loads((HERE / "settings-triggers.json").read_text())))

    def one(pair):
        read, raw, input_text, output_text, error = invoke_settings_read(llm, *pair)
        usage = getattr(raw, "usage_metadata", None) or {}
        tokens = [usage.get("input_tokens") or _estimated_tokens(input_text),
                  usage.get("output_tokens") or _estimated_tokens(output_text)]
        return {"task": pair[0], "workflow": pair[1], "read": read.model_dump() if read is not None else None,
                "error": f"{type(error).__name__}: {error}"[:300] if error else None, "tokens": tokens}

    with ThreadPoolExecutor(6) as pool:
        done = list(pool.map(one, pairs))
    tokens = [sum(d["tokens"][i] for d in done) for i in (0, 1)]
    usd = tokens[0] * reask.PRICE["input"] + tokens[1] * reask.PRICE["output"]
    Path(out).write_text(json.dumps({"model": model, "tokens": tokens, "usd": round(usd, 4), "reads": done},
                                    indent=1, ensure_ascii=False))
    print(f"{len(done)} requests read by {model}; failed {sum(d['read'] is None for d in done)}; US${usd:.4f}")
    for d in done:
        print(f"  {d['workflow']:8} {d['read']} | {d['task'][:60]}")


def apply(out: str, reads: str):
    replay_full.SETTINGS_READS.update({f"{d['task']}\x00{d['workflow']}": d["read"]
                                       for d in json.loads(Path(reads).read_text())["reads"] if d["read"]})
    harness.run(out)


if __name__ == "__main__":
    args = sys.argv[1:]
    {"triggers": lambda: triggers(args[1]), "ask": lambda: ask(args[1]),
     "apply": lambda: apply(args[1], args[2])}[args[0]]()
