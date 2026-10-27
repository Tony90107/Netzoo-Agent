"""RESULTS-J2.md user decision: the j2 arm-G answer turns re-judged offline with the fixed refuses_input quote. Jev calls
only (no agent run). Every recorded `core.jev_answer` is judged again with its line (the input_check's own text where
the recorded line was the field key) and the recorded reply; `answered_core` is applied to the recorded turn-2 call.

Usage: OPENROUTER_API_KEY=... python3 rejudge_j2.py > REJUDGE-J2.txt
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.graph import jev_guard_call as g  # noqa: E402

OLD_KEY = "LIONESS-PANDA input_checks refuses_input: coexpression_matrix"


def events(turn: Path, name: str) -> list[dict]:
    return [json.loads(line)["payload"] for trace in sorted(turn.glob("trace-*.jsonl"))
            for line in trace.read_text().splitlines()
            if f'"{name}"' in line and json.loads(line).get("event_type") == name]


def main():
    items = {i["id"]: i for i in json.loads((HERE / "j2/items.json").read_text())["single"]}
    replies = {"fact": "reply_fact", "confirm": "reply_confirm", "restate": "reply_restate", "result": "reply_result"}
    fixed = g.ruled_out("LIONESS-PANDA", ("coexpression_network", 1.0), None)
    print(f"fixed line: {fixed!r}\n")
    print("id | gold final | line changed | recorded judge -> action | re-judged -> action")
    rows = []
    for folder in sorted((HERE / "live/j2g").glob("hb-j2g-*-1")):
        item = items[folder.name.split("-")[2]]
        job = json.loads((folder / "job.json").read_text())
        if len(job["sent"]) < 2 or not (folder / "t2").exists():
            continue
        answer_events = events(folder / "t2", "core.jev_answer")
        if not answer_events:
            continue
        recorded = answer_events[-1]
        asked = (events(folder / "t1", "core.decision") or [{}])[-1]
        fact = (asked.get("facts") or [{}])[0]
        line = fixed if recorded["contract"] == OLD_KEY else recorded["contract"]
        reply = item[replies[job["sent"][1]]]
        judged = g.judge_answer(line, fact.get("user_quote", ""), fact.get("question", ""), reply)
        before = CoreDecision(kind=recorded["kind_before"], basis=recorded["basis_before"] or "x",
                              workflows=list(fact.get("workflows") or []))
        question = {"user_quote": fact.get("user_quote", ""), "workflows": fact.get("workflows") or [],
                    "labels": {"contract": line}}
        after, action = g.answered_core(before, question, reply, judged)
        gold = (item["final_after_fact"] or {}).get("call") if job["sent"][1] == "fact" else item["expected_call"]
        rows.append({"id": item["id"], "gold": gold, "changed": line != recorded["contract"],
                     "recorded": [recorded["judged"]["answer"], round(recorded["judged"]["confidence"], 2),
                                  recorded["action"]],
                     "now": [judged["answer"], round(judged["confidence"], 2), action], "final_now": after.kind})
        r = rows[-1]
        print(f"  {r['id']} | {gold} | {'yes' if r['changed'] else '-'} | {r['recorded']} | {r['now']} -> {r['final_now']}")
    wrong = [r["id"] for r in rows if r["now"][2] == "declined" and r["gold"] not in ("DECLINE",)]
    caught = [r["id"] for r in rows if r["now"][2] == "declined" and r["gold"] == "DECLINE"]
    print(f"\nwrong declines now: {wrong or 'none'}; declines now: {caught}")
    (HERE / "rejudge-j2.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
