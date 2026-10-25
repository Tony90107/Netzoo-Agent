"""M-hold pilot (PLAN-M-SHADOW.md, 36-item version): the declared gates on the h10 round. No model calls.

turn1: S's first-turn call is the call each turn would have made (`shadow.m_hold.would_have`; the live call when the
       turn was not held), M's flag is a held turn. Gates D1-D4 (36-item version: D1 >= 4 errors on >= 4 items);
       writes h10-gates-d.json, which `run_h10.py followup` requires to pass.
final: each conversation's final call (the last turn's `core.decision`) beside S's, against the final gold the replies
       actually sent lead to (`reply_fact` -> final_after_fact, `reply_result` -> final_after_result, else the opening
       gold). Gates T1-T3, T4 described; writes held-questions.json for the blind labeller (gates Q1-Q2).

Usage: python3 score_h10.py turn1 > score-h10-turn1.txt
       python3 score_h10.py final > score-h10-final.txt
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "harness-repair-2026-10-23"))
from score import kind_of  # noqa: E402

ACTING = ("DO", "DECLINE")
MEASURES = ("right", "FA", "FR", "MA", "wrong question kind", "extra questions", "wrong workflow", "UNCHECKED")


def as_kind(call: str) -> str:
    return "DO" if call == "PARTIAL" else call


def events(turn: Path, kind: str) -> list[dict]:
    found = []
    for trace in sorted(turn.glob("trace-*.jsonl")):
        for line in trace.read_text().splitlines():
            if f'"{kind}"' in line and (row := json.loads(line)).get("event_type") == kind:
                found.append(row["payload"])
    return found


def reply_text(turn: Path) -> str:
    session = json.loads((turn / "session.json").read_text()) if (turn / "session.json").exists() else {}
    replies = [m["content"] for m in session.get("messages", []) if m["role"] == "assistant"]
    return replies[-1] if replies else ""


def right(call: dict | None, gold_call: str, also: list[str], workflows: list[str]) -> bool:
    if not call:
        return False
    kind = call.get("kind")
    if kind not in {as_kind(gold_call), *map(as_kind, also)}:
        return False
    return kind != "DO" or not workflows or bool(set(call.get("workflows") or []) & set(workflows))


def sessions() -> list[dict]:
    items = {i["id"]: i for i in json.loads((HERE / "h10" / "items.json").read_text())["single"]}
    rows = []
    for folder in sorted((HERE / "live" / "h10").glob("hb-h10-*-1")):
        key, item = folder.name.split("-")[2], None
        item = items[key]
        job = json.loads((folder / "job.json").read_text())
        turns = sorted(folder.glob("t*"), key=lambda p: int(p.name[1:]))
        calls = [(events(t, "core.decision") or [None])[-1] for t in turns]
        shadow = (events(turns[0], "shadow.m_hold") or [{}])[-1]
        live1 = calls[0] or {}
        s1 = ({**shadow["would_have"]} if shadow.get("would_have") else
              {"kind": live1.get("kind"), "basis": live1.get("basis"), "workflows": live1.get("workflows") or []})
        rows.append({"id": key, "group": item["category"], "sub": item["sub"], "dragon": item.get("dragon_control"),
                     "item": item, "sent": job.get("sent", []), "end": job.get("end"), "turns": turns,
                     "calls": calls, "shadow": shadow, "status": shadow.get("status", "no_event"), "s1": s1,
                     "held": shadow.get("status") == "held"})
    return rows


def opening_right(row) -> bool:
    item = row["item"]
    return right(row["s1"], item["expected_call"], item.get("also_acceptable") or [], item.get("workflows") or [])


def turn1():
    rows = sessions()
    for row in rows:
        row["s1_right"] = opening_right(row)
    acting = [r for r in rows if r["s1"].get("kind") in ACTING]
    errors = [r for r in acting if not r["s1_right"]]
    hits = [r for r in errors if r["held"]]
    false = [r for r in acting if r["s1_right"] and r["held"]]
    k_false = [r for r in false if r["group"] in ("K1", "K2")]
    dragon_false = [r for r in false if r["dragon"]]
    def outcome(call, item) -> str:
        """right (kind and workflow), wrong workflow (kind right, no gold workflow), else `kind_of`'s error."""
        if right(call, item["expected_call"], item.get("also_acceptable") or [], item.get("workflows") or []):
            return "right"
        found = kind_of(as_kind(item["expected_call"]), (call or {}).get("kind"))
        return "wrong workflow" if found == "right" else found

    before = Counter(outcome(r["s1"], r["item"]) for r in rows)
    after = Counter(outcome(r["calls"][0], r["item"]) for r in rows)
    simulated = {m: [before[m], after[m]] for m in MEASURES}
    gates = {
        "D1": len(hits) >= 4 and len({r["id"] for r in hits}) >= 4,
        "D2": bool(hits) and len(hits) >= len(false),
        "D3": len(k_false) <= 4 and len(dragon_false) <= 2,
        "D4": all(simulated[m][1] <= simulated[m][0] for m in ("FA", "FR", "MA"))
              and simulated["wrong question kind"][1] - simulated["wrong question kind"][0]
              <= simulated["MA"][0] - simulated["MA"][1]}
    passed = all(gates.values())
    print(f"h10 turn 1: {len(rows)} sessions; shadow events {dict(Counter(r['status'] for r in rows))}")
    print(f"S (frozen) first-turn right {sum(r['s1_right'] for r in rows)}/{len(rows)}; by group "
          f"{ {g: f'{sum(r['s1_right'] for r in rows if r['group'] == g)}/{sum(r['group'] == g for r in rows)}' for g in ('V', 'U', 'K1', 'K2')} }")
    print(f"S acting {len(acting)}: errors {[r['id'] for r in errors]}")
    print(f"M hits {[r['id'] for r in hits]}; false alarms {[r['id'] for r in false]} "
          f"(K {[r['id'] for r in k_false]}, DRAGON {[r['id'] for r in dragon_false]})")
    print(f"precision {len(hits)}/{len(hits) + len(false)}")
    print("simulated first turn (S -> C): " + "  ".join(f"{m} {a}->{b}" for m, (a, b) in simulated.items()))
    print(f"gates {gates} -> {'PASSED' if passed else 'NOT PASSED: turns 2-3 are not run'}")
    print("\nsession | group/sub | dragon | expected | S call | right | m_hold | C turn-1 call")
    for r in sorted(rows, key=lambda r: (r["group"], r["id"])):
        print(f"  {r['id']} | {r['group']}/{r['sub']} | {'D' if r['dragon'] else '-'} | {r['item']['expected_call']} | "
              f"{r['s1'].get('kind')}/{r['s1'].get('basis')} | {'Y' if r['s1_right'] else 'n'} | {r['status']}"
              f"{'/' + (r['shadow'].get('held') or {}).get('source', '') if r['held'] else ''} | "
              f"{(r['calls'][0] or {}).get('kind')}/{(r['calls'][0] or {}).get('basis')}")
    result = {"passed": passed, "gates": gates, "hits": [r["id"] for r in hits], "false_alarms": [r["id"] for r in false],
              "k_false": [r["id"] for r in k_false], "dragon_false": [r["id"] for r in dragon_false],
              "simulated": simulated, "errors": [r["id"] for r in errors]}
    (HERE / "h10-gates-d.json").write_text(json.dumps(result, indent=1) + "\n")


def final_gold(row) -> tuple[str, list[str], list[str], str]:
    item, sent = row["item"], row["sent"]
    if "fact" in sent and item.get("final_after_fact"):
        found = item["final_after_fact"]
        return found["call"], [], found.get("workflows") or [], "after_fact"
    if "result" in sent and item.get("final_after_result"):
        found = item["final_after_result"]
        return found["call"], [], found.get("workflows") or [], "after_result"
    return item["expected_call"], item.get("also_acceptable") or [], item.get("workflows") or [], "opening"


def final():
    rows = sessions()
    for row in rows:
        gold, also, workflows, which = final_gold(row)
        last = next((c for c in reversed(row["calls"]) if c), None)
        row.update(c_final=last, c_gold=(gold, which), c_right=right(last, gold, also, workflows),
                   c_kind=kind_of(as_kind(gold), (last or {}).get("kind")) if last else "no_call")
        if row["held"]:  # S would have acted on turn 1 and stopped there
            row.update(s_final=row["s1"], s_right=opening_right(row),
                       s_kind=kind_of(as_kind(row["item"]["expected_call"]), row["s1"]["kind"]))
        else:
            row.update(s_final=last, s_right=row["c_right"], s_kind=row["c_kind"])
        for side in ("c", "s"):
            if row[f"{side}_right"]:
                row[f"{side}_kind"] = "right"
    c, s = Counter(r["c_kind"] for r in rows), Counter(r["s_kind"] for r in rows)
    fixes = [r["id"] for r in rows if r["c_right"] and not r["s_right"]]
    breaks = [r["id"] for r in rows if r["s_right"] and not r["c_right"]]
    needless = [r["id"] for r in rows if r["held"] and opening_right(r)]
    gates = {"T1": len(fixes) - len(breaks) >= 3,
             "T2": all(c[m] <= s[m] for m in ("FA", "FR", "MA")),
             "T3": len(breaks) <= 1}
    asked_by_s = [r for r in rows if not r["held"] and r["s1"].get("kind") in ("ASK", "CLARIFY")]
    print(f"h10 final: {len(rows)} conversations; ends {dict(Counter(r['end'] for r in rows))}")
    print(f"final right: C {sum(r['c_right'] for r in rows)} vs S {sum(r['s_right'] for r in rows)}; "
          f"fixes {fixes}; breaks {breaks}; held on right openings (needless questions) {needless}")
    print("final measures (S -> C): " + "  ".join(f"{m} {s[m]}->{c[m]}" for m in MEASURES))
    print(f"gates {gates}")
    print(f"T4 (described): S asked on its own in {len(asked_by_s)} conversations; right at the end "
          f"{sum(r['s_right'] for r in asked_by_s)}: {[(r['id'], r['s_kind']) for r in asked_by_s]}")
    print("\nsession | group | held | sent | final gold | C final | C | S final | S")
    for r in sorted(rows, key=lambda r: (r["group"], r["id"])):
        print(f"  {r['id']} | {r['group']} | {'H' if r['held'] else '-'} | {'/'.join(r['sent'])} | "
              f"{r['c_gold'][0]} ({r['c_gold'][1]}) | {(r['c_final'] or {}).get('kind')} "
              f"{(r['c_final'] or {}).get('workflows')} | {r['c_kind']} | {(r['s_final'] or {}).get('kind')} | {r['s_kind']}")
    packet = []
    for r in rows:
        if not r["held"]:
            continue
        item = r["item"]
        packet.append({"id": r["id"], "request": item["prompt"], "expected_call": item["expected_call"],
                       "deciding_fact": item.get("deciding_fact", ""), "missing_core": item.get("missing_core", ""),
                       "gold_reason": item.get("reason", ""), "held_reply": reply_text(r["turns"][0])})
    (HERE / "held-questions.json").write_text(json.dumps(packet, indent=1, ensure_ascii=False) + "\n")
    (HERE / "score-h10-final.json").write_text(json.dumps(
        {"gates": gates, "fixes": fixes, "breaks": breaks, "needless": needless,
         "c": dict(c), "s": dict(s)}, indent=1) + "\n")
    print(f"\nheld-questions.json: {len(packet)} held replies for the blind labeller")


if __name__ == "__main__":
    {"turn1": turn1, "final": final}[sys.argv[1]]()
