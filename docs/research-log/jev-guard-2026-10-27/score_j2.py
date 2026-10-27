"""j2 two-arm scoring (PLAN-J2.md section 3): gates O1-O3 and S0, S1, S3, S4. No model calls.

Right = the final call's kind equals the final gold's kind (PARTIAL counted as DO; workflows not checked). Final gold:
`final_after_fact` when the fact reply was sent, `final_after_result` when the result reply was sent, else the opening
expected_call (a T item's confirm leaves it DECLINE).

Usage: python3 score_j2.py > RESULTS-J2.txt   (also writes gates-j2.json)
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "harness-repair-2026-10-23"))
from score import kind_of  # noqa: E402

MEASURES = ("right", "FA", "FR", "MA", "wrong question kind", "extra questions", "UNCHECKED")


def kind(call):
    return "DO" if call == "PARTIAL" else call


def events(turn: Path, name: str) -> list[dict]:
    return [json.loads(line)["payload"] for trace in sorted(turn.glob("trace-*.jsonl"))
            for line in trace.read_text().splitlines()
            if f'"{name}"' in line and json.loads(line).get("event_type") == name]


def sessions(tag: str, items: dict) -> dict:
    rows = {}
    for folder in sorted((HERE / "live" / tag).glob(f"hb-{tag}-*-1")):
        item = items[folder.name.split("-")[2]]
        job = json.loads((folder / "job.json").read_text())
        turns = sorted(folder.glob("t*"), key=lambda p: int(p.name[1:]))
        cores = [(events(t, "core.decision") or [{}])[-1] for t in turns]
        if "fact" in job["sent"]:
            gold = kind(item["final_after_fact"]["call"])
        elif "result" in job["sent"]:
            gold = kind(item["final_after_result"]["call"])
        else:
            gold = kind(item["expected_call"])
        jev = {name: [events(t, f"core.{name}") for t in turns] for name in ("jev_guard", "jev_condition",
                                                                           "jev_answer", "jev_link")}
        rows[item["id"]] = {"id": item["id"], "group": item["category"], "dragon": bool(item.get("dragon_control")),
                            "sent": job["sent"], "end": job["end"], "gold": gold,
                            "t1": cores[0].get("kind") or "none", "t1_basis": cores[0].get("basis"),
                            "final": cores[-1].get("kind") or "none", "final_basis": cores[-1].get("basis"),
                            "jev": jev}
    return rows


def acted(row, name, turn=0, action=None):
    found = row["jev"][name][turn] if len(row["jev"][name]) > turn else []
    return [e for e in found if action is None or e.get("action") == action]


def main():
    items = {i["id"]: i for i in json.loads((HERE / "j2" / "items.json").read_text())["single"]}
    F, G = sessions("j2f", items), sessions("j2g", items)
    both = sorted(set(F) & set(G))
    sf = Counter(kind_of(F[k]["gold"], F[k]["final"]) for k in both)
    sg = Counter(kind_of(G[k]["gold"], G[k]["final"]) for k in both)
    declines = [G[k] for k in both if any(e.get("action") == "declined" for turn in G[k]["jev"]["jev_answer"]
                                          for e in turn)]
    wrong_declines = [r["id"] for r in declines if r["gold"] != "DECLINE"]
    t_do = [G[k] for k in both if G[k]["group"] == "T" and (acted(G[k], "jev_condition") or [{}])[0].get("kind_before") == "DO"]
    t_asked = [r["id"] for r in t_do if acted(r, "jev_condition", 0, "ask")]
    tc_asked = [G[k]["id"] for k in both if G[k]["group"] == "TC" and acted(G[k], "jev_condition", 0, "ask")]
    asked = [G[k] for k in both if G[k]["t1_basis"] in ("jev_fact", "jev_condition")]
    asked_fails = [r for r in asked if r["gold"] == "DECLINE" and len(r["sent"]) > 1]
    caught = [r["id"] for r in asked_fails if r["final_basis"] == "jev_answer"]
    v_links = [G[k]["id"] for k in both if G[k]["group"] == "V" and acted(G[k], "jev_link", 0, "link")]
    n_clarify = [G[k] for k in both if G[k]["group"] == "N"
                 and (acted(G[k], "jev_link") or [{}])[0].get("kind_before") == "CLARIFY"]
    n_links = [r["id"] for r in n_clarify if acted(r, "jev_link", 0, "link")]
    guard_false = [G[k]["id"] for k in both if G[k]["group"] in ("TC", "N") and items[k]["expected_call"] in ("DO", "PARTIAL")
                   and any(e.get("action") in ("ask", "clarify") for e in acted(G[k], "jev_guard"))]
    gates = {
        "O1": sg["right"] >= sf["right"] + 3,
        "O2": all(sg[m] <= sf[m] for m in ("FA", "FR", "MA")),
        "O3": not wrong_declines,
        "S0": len(guard_false) <= 2,
        "S1": len(t_asked) >= 4 and len(tc_asked) <= 1,
        "S3": not wrong_declines and (not asked_fails or len(caught) * 2 >= len(asked_fails)),
        "S4": len(v_links) <= 1 and (len(n_clarify) < 2 or len(n_links) * 2 >= len(n_clarify)),
    }
    print(f"j2: {len(both)} conversations in both arms (F {len(F)}, G {len(G)})")
    for name, rows, s in (("F guard off", F, sf), ("G guard on", G, sg)):
        print(f"  {name}: final right {s['right']}/{len(both)}  " + "  ".join(f"{m} {s[m]}" for m in MEASURES[1:])
              + "  | by group " + str({g: f"{sum(kind_of(rows[k]['gold'], rows[k]['final']) == 'right' for k in both if rows[k]['group'] == g)}"
                                       f"/{sum(rows[k]['group'] == g for k in both)}" for g in ("T", "TC", "U", "N", "V")}))
    print(f"O1 G right >= F right + 3: {sg['right']} vs {sf['right']} -> {'PASS' if gates['O1'] else 'fail'}")
    print(f"O2 FA/FR/MA not up: {[(m, sf[m], sg[m]) for m in ('FA', 'FR', 'MA')]} -> {'PASS' if gates['O2'] else 'fail'}")
    print(f"O3 wrong jev_answer declines: {wrong_declines or 'none'} -> {'PASS' if gates['O3'] else 'fail'}")
    print(f"S0 guard asks on TC/N gold-DO: {guard_false} (<= 2) -> {'PASS' if gates['S0'] else 'fail'}")
    print(f"S1 T items with a DO: {len(t_do)}, confirm asked {t_asked} (>= 4); TC asked {tc_asked} (<= 1) -> "
          f"{'PASS' if gates['S1'] else 'fail'}")
    print(f"S3 Jev-asked items whose reply fails: {[r['id'] for r in asked_fails]}, declined by the answer {caught} -> "
          f"{'PASS' if gates['S3'] else 'fail'}")
    print(f"S4 links on V {v_links} (<= 1); N CLARIFY {[r['id'] for r in n_clarify]}, linked {n_links} -> "
          f"{'PASS' if gates['S4'] else 'fail'}")
    print(f"-> {'ALL PASS' if all(gates.values()) else 'NOT PASSED: ' + ', '.join(k for k, v in gates.items() if not v)}")
    print("\nid | group | gold final | F t1 -> final | G t1 -> final | G Jev actions")
    for k in sorted(both, key=lambda k: (G[k]["group"], k)):
        f, g = F[k], G[k]
        actions = [f"{n}:{e.get('action')}" for n in ("jev_guard", "jev_condition", "jev_answer", "jev_link")
                   for turn in g["jev"][n] for e in turn if e.get("action") not in (None, "not_acting", "agrees_or_unsure",
                                                                                    "no_violation", "not_clarify", "not_do",
                                                                                    "answer_not_on_do", "no_pick")]
        print(f"  {k} | {g['group']}{'D' if g['dragon'] else ''} | {g['gold']} | {f['t1']}/{f['t1_basis']} -> {f['final']} | "
              f"{g['t1']}/{g['t1_basis']} -> {g['final']}/{g['final_basis']} | {' '.join(actions)}")
    (HERE / "gates-j2.json").write_text(json.dumps({"gates": gates, "F": sf, "G": sg, "wrong_declines": wrong_declines,
                                                    "t_asked": t_asked, "tc_asked": tc_asked, "caught": caught,
                                                    "v_links": v_links, "n_links": n_links, "guard_false": guard_false},
                                                   indent=1) + "\n")


if __name__ == "__main__":
    main()
