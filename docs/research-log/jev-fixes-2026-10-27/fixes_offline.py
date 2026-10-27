"""FIXES.md offline test: gates B1-B3, A1-A2 on the recorded j2/j3 items and arm-G events. No model call.

Usage: python3 fixes_offline.py > FIXES-OFFLINE.txt
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.contracts.task_state import TaskState  # noqa: E402
from netzoo_agent_core.engine.task_updates import _pending, bind_answers  # noqa: E402
from netzoo_agent_core.graph import jev_guard_call as g  # noqa: E402

W = HERE.parents[3]
J2 = W / "netzoo-jev-guard/docs/research-log/jev-guard-2026-10-27"
J3 = W / "netzoo-jev-combined/docs/research-log/jev-j3-2026-10-27"
SETS = {"j2": (J2 / "j2/items.json", J2 / "live/j2g", "j2g"), "j3": (J3 / "j3/items.json", J3 / "live/j3g", "j3g")}


def items(name):
    return {i["id"]: i for i in json.loads(SETS[name][0].read_text())["single"]}


def events(turn: Path, kind: str) -> list[dict]:
    return [json.loads(line)["payload"] for trace in sorted(turn.glob("trace-*.jsonl"))
            for line in trace.read_text().splitlines()
            if f'"{kind}"' in line and json.loads(line).get("event_type") == kind]


def bind(reply: str, workflow: str = "PANDA", line: str = "PANDA incompatible_input_artifacts: mutation_matrix",
         sentence: str = "We only have the mutation matrix.") -> str | None:
    """The value `bind_answers` gives `reply` as the answer to a freshly asked data confirm (None: not bound)."""
    typed = {"violated": line, "workflow": workflow, "sentence": sentence, "data": ["mutation_matrix", 1.0]}
    asked, _ = g.conditioned_core(CoreDecision(kind="DO", basis="run", workflows=[workflow]), typed)
    [pending] = _pending(asked.model_dump(mode="json"))
    state = TaskState.model_validate({"task_id": "t", "goal": "g", "pending": [pending.model_dump()]})
    _state, bound, _ = bind_answers(state, reply)
    return bound[0].value if bound else None


def main():
    out = {}
    # B1, B2
    confirm, other, facts = [], Counter(), Counter()
    yes_other = []
    for name in SETS:
        for item in items(name).values():
            if item.get("reply_confirm"):
                confirm.append((f"{name}:{item['id']}", bind(item["reply_confirm"])))
            for field in ("reply_restate", "reply_membership", "reply_result"):
                if item.get(field):
                    value = bind(item[field])
                    other[value] += 1
                    if value == "yes":
                        yes_other.append(f"{name}:{item['id']}:{field}")
            if item.get("reply_fact"):
                facts[bind(item["reply_fact"])] += 1
    b1 = sum(v == "yes" for _, v in confirm)
    out["B1"] = b1 >= 14
    out["B2"] = len(yes_other) <= 1
    print(f"B1 confirm replies bound yes: {b1}/{len(confirm)} {[k for k, v in confirm if v != 'yes']} -> "
          f"{'PASS' if out['B1'] else 'fail'}")
    print(f"B2 non-confirm replies bound: {dict(other)}; bound yes {yes_other} (<= 1) -> {'PASS' if out['B2'] else 'fail'}")
    print(f"   reported apart, reply_fact (U items, never asked a data confirm): {dict(facts)}")

    # B3: the recorded confirm sessions, turn 2 replayed with the code binding
    rows = []
    for name, ids in (("j2", ("Q12", "Q33", "Q46", "Q48")), ("j3", ("R02", "R05", "R28"))):
        its, live, tag = items(name), SETS[name][1], SETS[name][2]
        for key in ids:
            folder = live / f"hb-{tag}-{key}-1"
            job = json.loads((folder / "job.json").read_text())
            t2 = (events(folder / "t2", "core.decision") or [{}])[-1] if (folder / "t2").exists() else {}
            sent = job["sent"][1] if len(job["sent"]) > 1 else None
            reply = its[key].get({"confirm": "reply_confirm", "restate": "reply_restate"}.get(sent, ""), "")
            value = bind(reply) if reply else None
            before = t2.get("kind")
            after = "DECLINE" if value == "yes" and before == "DO" else before
            gold = its[key]["expected_call"]
            rows.append((f"{name}:{key}", sent, value, before, after, gold))
    right = sum(a == g_ for *_, a, g_ in rows)
    wrong_decline = [r[0] for r in rows if r[4] == "DECLINE" and r[5] != "DECLINE"]
    out["B3"] = right >= 6 and not wrong_decline
    print("B3 recorded confirm sessions: id | reply sent | bound | recorded t2 -> with fix | gold")
    for r in rows:
        print(f"   {r[0]} | {r[1]} | {r[2]} | {r[3]} -> {r[4]} | {r[5]}")
    print(f"   right {right}/{len(rows)} (>= 6), wrong declines {wrong_decline or 'none'} -> {'PASS' if out['B3'] else 'fail'}")

    # A1, A2: every recorded unplaced violation now asks; none on a gold-DO call
    unplaced = []
    for name in SETS:
        its, live, tag = items(name), SETS[name][1], SETS[name][2]
        for folder in sorted(live.glob(f"hb-{tag}-*-1")):
            key = folder.name.split("-")[2]
            for turn in sorted(folder.glob("t*")):
                for e in events(turn, "core.jev_condition"):
                    typed = e.get("typed") or {}
                    if typed.get("unplaced") and e.get("kind_before") == "DO":
                        unplaced.append((f"{name}:{key}:{turn.name}", typed, its[key]["expected_call"]))
    offline = json.loads((W / "netzoo-jev-guard/docs/research-log/jev-guard-2026-10-27/conditions-offline-typed.json")
                         .read_text())
    for row in offline:
        if (row.get("jev") or {}).get("unplaced"):
            unplaced.append((f"offline:{row['set']}:{row['id']}", row["jev"] | {"workflow": row["workflows"][0]},
                             row["gold"]))
    asked, quotes_ok, gold_do = 0, True, []
    for key, typed, gold in unplaced:
        typed = {**typed, "violated": None}
        after, action = g.conditioned_core(CoreDecision(kind="DO", basis="run",
                                                        workflows=[typed.get("workflow") or "PANDA"]), typed)
        asked += action == "ask"
        if action == "ask":
            fact = after.facts[0]
            quotes_ok &= fact.user_quote == "" and fact.contract_quote == typed["unplaced"]
            if gold in ("DO", "PARTIAL"):
                gold_do.append(key)
    out["A1"] = asked == len(unplaced) and not gold_do
    out["A2"] = quotes_ok
    print(f"A1 unplaced violations: {len(unplaced)} {[(k, gd) for k, _, gd in unplaced]}; now asked {asked}; on gold DO "
          f"{gold_do or 'none'} -> {'PASS' if out['A1'] else 'fail'}")
    print(f"A2 no user quote, contract line verbatim: {'PASS' if out['A2'] else 'fail'}")
    print(f"-> {'ALL PASS' if all(out.values()) else 'NOT PASSED: ' + ', '.join(k for k, v in out.items() if not v)}")


if __name__ == "__main__":
    main()
