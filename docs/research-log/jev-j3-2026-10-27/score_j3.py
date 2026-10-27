"""j3 two-arm scoring (PLAN-J3.md section 3): gates O1-O4, OV1-OV2, S0, S1, S4. No model calls.

Right = the final call's kind equals the final gold's kind (PARTIAL counted as DO; workflows not checked). Final gold:
`final_after_fact` when the fact reply was sent, `final_after_result` when the result reply was sent, else the opening
expected_call. The overlap reason is found in the final turn's reply text (stdout).

Usage: python3 score_j3.py > RESULTS-J3.txt   (also writes gates-j3.json)
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
OVERLAP = "none returns overlapping memberships"


def kind(call):
    return "DO" if call == "PARTIAL" else call


def events(turn: Path, name: str) -> list[dict]:
    return [json.loads(line)["payload"] for trace in sorted(turn.glob("trace-*.jsonl"))
            for line in trace.read_text().splitlines()
            if f'"{name}"' in line and json.loads(line).get("event_type") == name]


def membership_asked(core: dict) -> bool:
    return any(f.get("depends_on") == "group_membership" or "one group each" in f.get("question", "")
               for f in core.get("facts") or [])


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
        reply = (turns[-1] / "stdout.txt").read_text(errors="replace") if turns else ""
        rows[item["id"]] = {
            "id": item["id"], "group": item["category"], "gold": gold, "sent": job["sent"],
            "t1": f"{cores[0].get('kind')}/{cores[0].get('basis')}" if cores else "none",
            "final": cores[-1].get("kind") or "none", "final_basis": cores[-1].get("basis"),
            "overlap_reason": OVERLAP in reply, "membership_asked": any(membership_asked(c) for c in cores),
            "waiting": (cores[-1].get("kind") in ("ASK", "CLARIFY")) if cores else False,
            "jev": {name: [e for t in turns for e in events(t, f"core.{name}")]
                    for name in ("jev_guard", "jev_condition", "jev_answer", "jev_link", "jev_overlap")}}
    return rows


def main():
    items = {i["id"]: i for i in json.loads((HERE / "j3" / "items.json").read_text())["single"]}
    F, G = sessions("j3f", items), sessions("j3g", items)
    both = sorted(set(F) & set(G))
    sf = Counter(kind_of(F[k]["gold"], F[k]["final"]) for k in both)
    sg = Counter(kind_of(G[k]["gold"], G[k]["final"]) for k in both)
    by = lambda rows, g: [rows[k] for k in both if rows[k]["group"] == g]  # noqa: E731
    wrong_declines = [G[k]["id"] for k in both if G[k]["gold"] != "DECLINE"
                      and any(e.get("action") == "declined" for e in G[k]["jev"]["jev_answer"])]
    o4 = lambda rows: [r["id"] for r in rows.values() if r["group"] != "GO" and r["final"] == "DECLINE"  # noqa: E731
                       and r["overlap_reason"]]
    go = by(G, "GO")
    ov1_bad = [r["id"] for r in go if r["final"] != "DECLINE" or not r["overlap_reason"] or r["membership_asked"]]
    gt_f_refused = [k for k in both if F[k]["group"] == "GT" and F[k]["final"] == "DECLINE" and F[k]["overlap_reason"]]
    gt_do = [k for k in gt_f_refused if G[k]["final"] == "DO"]
    gt_wait = [k for k in gt_f_refused if G[k]["final"] != "DO" and G[k]["waiting"]]
    do_gold = [G[k] for k in both if G[k]["group"] in ("GT", "TC") or (G[k]["group"] == "N"
                                                                       and items[k]["expected_call"] == "DO")]
    s0 = [r["id"] for r in do_gold if any(e.get("action") in ("ask", "clarify") for e in r["jev"]["jev_guard"])]
    t_do = [r for r in by(G, "T") if any(e.get("kind_before") == "DO" for e in r["jev"]["jev_condition"])]
    t_asked = [r["id"] for r in t_do if any(e.get("action") == "ask" for e in r["jev"]["jev_condition"])]
    tc_asked = [r["id"] for r in by(G, "TC") if any(e.get("action") == "ask" for e in r["jev"]["jev_condition"])]
    v_links = [r["id"] for r in by(G, "V") if any(e.get("action") == "link" for e in r["jev"]["jev_link"])]
    gates = {
        "O1": sg["right"] >= sf["right"] + 4,
        "O2": all(sg[m] <= sf[m] for m in ("FA", "FR", "MA")),
        "O3": not wrong_declines,
        "O4": len(o4(G)) <= 1 and len(o4(G)) <= len(o4(F)),
        "OV1": not ov1_bad and len(go) == 6,
        "OV2": not gt_f_refused or (len(gt_do) + len(gt_wait)) * 3 >= 2 * len(gt_f_refused),
        "S0": len(s0) <= 2,
        "S1": (not t_do or len(t_asked) * 2 >= len(t_do)) and len(tc_asked) <= 1,
        "S4": len(v_links) <= 1,
    }
    print(f"j3: {len(both)} conversations in both arms (F {len(F)}, G {len(G)})")
    groups = ("GT", "GO", "GL", "T", "TC", "U", "N", "V")
    for name, rows, s in (("F flags off", F, sf), ("G flags on", G, sg)):
        print(f"  {name}: final right {s['right']}/{len(both)}  " + "  ".join(f"{m} {s[m]}" for m in MEASURES[1:])
              + "\n    by group " + str({g: f"{sum(kind_of(r['gold'], r['final']) == 'right' for r in by(rows, g))}"
                                         f"/{len(by(rows, g))}" for g in groups}))
    print(f"O1 G >= F + 4: {sg['right']} vs {sf['right']} -> {'PASS' if gates['O1'] else 'fail'}")
    print(f"O2 FA/FR/MA not up: {[(m, sf[m], sg[m]) for m in ('FA', 'FR', 'MA')]} -> {'PASS' if gates['O2'] else 'fail'}")
    print(f"O3 wrong jev_answer declines: {wrong_declines or 'none'} -> {'PASS' if gates['O3'] else 'fail'}")
    print(f"O4 overlap reason on non-GO finals: F {o4(F)} G {o4(G)} -> {'PASS' if gates['O4'] else 'fail'}")
    print(f"OV1 GO kept DECLINE + reason, never asked: bad {ov1_bad or 'none'} of {len(go)} -> "
          f"{'PASS' if gates['OV1'] else 'fail'}")
    print(f"OV2 GT refused by F with the overlap reason {gt_f_refused}: G DO {gt_do}, still waiting {gt_wait} -> "
          f"{'PASS' if gates['OV2'] else 'fail'}")
    print(f"S0 J-ask on gold-DO items: {s0} (<= 2) -> {'PASS' if gates['S0'] else 'fail'}")
    print(f"S1 T DO calls {[r['id'] for r in t_do]}, confirmed {t_asked}; TC confirmed {tc_asked} -> "
          f"{'PASS' if gates['S1'] else 'fail'}")
    print(f"S4 V links {v_links} (<= 1) -> {'PASS' if gates['S4'] else 'fail'}")
    print(f"-> {'ALL PASS' if all(gates.values()) else 'NOT PASSED: ' + ', '.join(k for k, v in gates.items() if not v)}")
    answers = [(r['id'], e.get('action')) for r in G.values() for e in r["jev"]["jev_answer"]
               if e.get("action") not in (None, "answer_not_on_do")]
    print(f"S3 (reported) answer reads acting: {answers}")
    print("\nid | group | gold | F t1 -> final [overlap reason] | G t1 -> final [overlap reason] | G Jev actions")
    skip = (None, "not_acting", "agrees_or_unsure", "no_violation", "not_clarify", "not_do", "answer_not_on_do", "no_pick")
    for k in sorted(both, key=lambda k: (groups.index(G[k]["group"]), k)):
        f, g = F[k], G[k]
        acts = [f"{n}:{e.get('action')}" for n, es in g["jev"].items() for e in es if e.get("action") not in skip]
        acts += [f"overlap:{'doubted' if r.get('doubted') else 'kept'}" for e in g["jev"]["jev_overlap"]
                 for r in e.get("reads") or []]
        print(f"  {k} | {g['group']} | {g['gold']} | {f['t1']} -> {f['final']}{' [OV]' if f['overlap_reason'] else ''} | "
              f"{g['t1']} -> {g['final']}/{g['final_basis']}{' [OV]' if g['overlap_reason'] else ''} | {' '.join(acts)}")
    (HERE / "gates-j3.json").write_text(json.dumps({"gates": gates, "F": sf, "G": sg, "wrong_declines": wrong_declines,
                                                    "o4": {"F": o4(F), "G": o4(G)}, "ov1_bad": ov1_bad,
                                                    "gt_f_refused": gt_f_refused, "gt_do": gt_do, "gt_wait": gt_wait,
                                                    "s0": s0, "t_asked": t_asked, "tc_asked": tc_asked,
                                                    "v_links": v_links}, indent=1) + "\n")


if __name__ == "__main__":
    main()
