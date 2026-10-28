"""The app's check settings vs the test runners', replayed on recorded turns (no model calls).

Every recorded turn whose check ran on the own model `openai/gpt-4o-mini-2024-07-18` (the runners' setting since
2026-10-20). Its calls are replayed in their recorded order, with each call refused at preflight reinserted where it
was refused (its `consumed_tokens` equals the sum of the calls before it), under one set of budget rules:
  projected = consumed + input + reserved output; refused when projected > ceiling (budget - 1,500; the response
  call may use the 1,500). Allowance roles get turn budget + 30,000 (`with_reading_allowance`).
A call allowed here but refused in the recording runs with its role's median recorded output. A check-model output
over the app's 1,200-token cap would be cut off (counted; the replay keeps going).

Configs: rec = what the runners used (turn 30,000, own-model reserve 16,000, other calls 1,200, response 800);
app = docker compose (turn 20,000, no own model: every call on the router LLM, reserve and output cap 1,200).
Calibration: rec must reproduce the recorded refusals.

Usage: python3 simulate.py OUT.json
"""
from __future__ import annotations

import collections
import json
import statistics
import sys
from pathlib import Path

LOGS = Path(__file__).resolve().parent.parent
OWN = "openai/gpt-4o-mini-2024-07-18"
ALLOWANCE = {"capability_check", "capability_reread", "capability_second_opinion", "capability_condition_check",
             "hybrid_gate", "goal_read", "data_facts", "settings_read", "fact_check", "study_purpose"}
CONFIGS = {
    "rec": {"turn": 30000, "extra": 30000, "own_reserve": 16000, "other_reserve": 1200, "cap": None},
    "app": {"turn": 20000, "extra": 30000, "own_reserve": 1200, "other_reserve": 1200, "cap": 1200},
}


def turns():
    for trace in sorted(LOGS.rglob("trace-*.jsonl")):
        if "check-reserve-2026-10-28" in str(trace):  # ran with the 4,000 reserve already (not the rec settings)
            continue
        if OWN not in trace.read_text(errors="replace"):
            continue
        ledger, blocked = None, []
        for line in trace.read_text(errors="replace").splitlines():
            event = json.loads(line)
            kind, payload = event.get("event_type"), event.get("payload") or {}
            if kind == "run.finished":
                ledger = (payload.get("token_usage") or {}).get("calls") or []
            elif kind == "budget.blocked":
                blocked.append(payload)
        if ledger is None:
            continue
        calls = [{"role": c["role"], "model": c.get("model"), "input": c.get("input_tokens") or 0,
                  "output": c.get("output_tokens") or 0, "recorded": "ran"} for c in ledger]
        for block in blocked:  # put each refused call back where it was refused
            running, at = 0, len(calls)
            for index, call in enumerate(calls):
                if call["recorded"] == "ran" and running >= block["consumed_tokens"]:
                    at = index
                    break
                running += call["input"] + call["output"] if call["recorded"] == "ran" else 0
            calls.insert(at, {"role": block["role"], "model": block.get("model"), "input":
                              block["estimated_input_tokens"], "output": None, "recorded": "refused"})
        yield str(trace.parent.relative_to(LOGS)), calls


def replay(calls, config, medians):
    consumed, out = 0, []
    for call in calls:
        own = call["model"] == OWN
        budget = config["turn"] + (config["extra"] if call["role"] in ALLOWANCE else 0)
        ceiling = budget if call["role"] == "response" else budget - 1500
        reserve = 800 if call["role"] == "response" else (config["own_reserve"] if own else config["other_reserve"])
        refused = consumed + call["input"] + reserve > ceiling
        output = call["output"] if call["output"] is not None else medians.get(call["role"], 0)
        cut = bool(config["cap"] and own and output > config["cap"] and not refused)
        out.append({"role": call["role"], "recorded": call["recorded"], "sim": "refused" if refused else "ran",
                    "cut": cut})
        if not refused:
            consumed += call["input"] + output
    return out


rows = list(turns())
outputs = collections.defaultdict(list)
for _where, calls in rows:
    for call in calls:
        if call["output"] is not None:
            outputs[call["role"]].append(call["output"])
medians = {role: int(statistics.median(xs)) for role, xs in outputs.items()}
report = {"turns": len(rows), "configs": CONFIGS}
for name, config in CONFIGS.items():
    agree = collections.Counter()
    refused, cut, turns_hit = collections.Counter(), collections.Counter(), set()
    for where, calls in rows:
        for call in replay(calls, config, medians):
            agree[(call["recorded"], call["sim"])] += 1
            if call["sim"] == "refused":
                refused[call["role"]] += 1
                turns_hit.add(where)
            if call["cut"]:
                cut[call["role"]] += 1
                turns_hit.add(where)
    report[name] = {"recorded_vs_sim": {f"{a}->{b}": n for (a, b), n in agree.items()},
                    "refused_by_role": dict(refused), "cut_by_role": dict(cut), "turns_hit": len(turns_hit)}
Path(sys.argv[1]).write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1))
