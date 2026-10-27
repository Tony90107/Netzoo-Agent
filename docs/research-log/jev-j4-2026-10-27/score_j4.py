"""j4 two-arm scoring (PLAN-J4.md section 3): gates O1-O4, C1-C2, S0, S1, S4. No model calls.

Adapted from score_j3.py. Right = the final call's kind equals the final gold's kind (PARTIAL counted as DO; workflows
not checked). Final gold: `final_after_fact` when the fact reply was sent, `final_after_result` when the result reply
was sent, else the opening expected_call. Form reasons are found in the final turn's reply text (stdout).

Usage: python3 score_j4.py > RESULTS-J4.txt   (also writes gates-j4.json)
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
REASONS = {"group_membership": "none returns overlapping memberships",
           "time_model": "models how the system changes from one time point to the next",
           "spatial": "uses where samples sit in space or which samples are neighbours"}
FORMS = ("group_membership", "time_model", "spatial", "input_network")
CONTROLS = {"GO": "group_membership", "FD": "time_model", "FS": "spatial", "FG": None}
TRAPS = ("GT", "FT", "FSN", "FN")
GROUPS = ("GT", "GO", "FT", "FD", "FSN", "FS", "FN", "FG", "T", "TC", "U", "N", "V")


def kind(call):
    return "DO" if call == "PARTIAL" else call


def events(turn: Path, name: str) -> list[dict]:
    return [json.loads(line)["payload"] for trace in sorted(turn.glob("trace-*.jsonl"))
            for line in trace.read_text().splitlines()
            if f'"{name}"' in line and json.loads(line).get("event_type") == name]


def form_asked(core: dict) -> bool:
    return any(f.get("depends_on") in FORMS for f in core.get("facts") or [])


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
            "final": cores[-1].get("kind") or "none", "final_basis": cores[-1].get("basis") or "",
            "reasons": [name for name, words in REASONS.items() if words in reply],
            "form_asked": any(form_asked(c) for c in cores),
            "waiting": (cores[-1].get("kind") in ("ASK", "CLARIFY")) if cores else False,
            "jev": {name: [e for t in turns for e in events(t, f"core.{name}")]
                    for name in ("jev_guard", "jev_condition", "jev_answer", "jev_link", "jev_overlap", "jev_forms")}}
    return rows


def main():
    items = {i["id"]: i for i in json.loads((HERE / "j4" / "items.json").read_text())["single"]}
    F, G = sessions("j4f", items), sessions("j4g", items)
    both = sorted(set(F) & set(G))
    sf = Counter(kind_of(F[k]["gold"], F[k]["final"]) for k in both)
    sg = Counter(kind_of(G[k]["gold"], G[k]["final"]) for k in both)
    by = lambda rows, g: [rows[k] for k in both if rows[k]["group"] == g]  # noqa: E731
    jev_declines = [G[k]["id"] for k in both if G[k]["gold"] != "DECLINE" and G[k]["final"] == "DECLINE"
                    and G[k]["final_basis"].startswith("jev")]
    # O4: a form reason said on a final whose item did not ask for that form.
    o4 = lambda rows: [r["id"] for r in rows.values() if r["final"] == "DECLINE"  # noqa: E731
                       and any(reason != CONTROLS.get(r["group"]) for reason in r["reasons"])]
    controls = [r for g in CONTROLS for r in by(G, g)]
    c1_bad = [r["id"] for r in controls if r["final"] != "DECLINE" or r["form_asked"]]
    traps_f_wrong = [k for k in both if F[k]["group"] in TRAPS and kind_of(F[k]["gold"], F[k]["final"]) != "right"]
    traps_g_right = [k for k in traps_f_wrong if kind_of(G[k]["gold"], G[k]["final"]) == "right"]
    traps_g_wait = [k for k in traps_f_wrong if k not in traps_g_right and G[k]["waiting"]]
    do_gold = [G[k] for k in both if G[k]["group"] in (*TRAPS, "TC") or (G[k]["group"] == "N"
                                                                         and items[k]["expected_call"] == "DO")]
    s0 = [r["id"] for r in do_gold if any(e.get("action") in ("ask", "clarify") for e in r["jev"]["jev_guard"])]
    t_do = [r for r in by(G, "T") if any(e.get("kind_before") == "DO" for e in r["jev"]["jev_condition"])]
    t_asked = [r["id"] for r in t_do if any(e.get("action") == "ask" for e in r["jev"]["jev_condition"])]
    tc_asked = [r["id"] for r in by(G, "TC") if any(e.get("action") == "ask" for e in r["jev"]["jev_condition"])]
    v_links = [r["id"] for r in by(G, "V") if any(e.get("action") == "link" for e in r["jev"]["jev_link"])]
    gates = {
        "O1": sg["right"] >= sf["right"] + 4,
        "O2": all(sg[m] <= sf[m] for m in ("FA", "FR", "MA")),
        "O3": not jev_declines,
        "O4": len(o4(G)) <= 1 and len(o4(G)) <= len(o4(F)),
        "C1": not c1_bad and len(controls) == 11,
        "C2": not traps_f_wrong or (len(traps_g_right) + len(traps_g_wait)) * 3 >= 2 * len(traps_f_wrong),
        "S0": len(s0) <= 2,
        "S1": (not t_do or len(t_asked) * 2 >= len(t_do)) and len(tc_asked) <= 1,
        "S4": len(v_links) <= 1,
    }
    print(f"j4: {len(both)} conversations in both arms (F {len(F)}, G {len(G)})")
    for name, rows, s in (("F flags off", F, sf), ("G flags on", G, sg)):
        print(f"  {name}: final right {s['right']}/{len(both)}  " + "  ".join(f"{m} {s[m]}" for m in MEASURES[1:])
              + "\n    by group " + str({g: f"{sum(kind_of(r['gold'], r['final']) == 'right' for r in by(rows, g))}"
                                         f"/{len(by(rows, g))}" for g in GROUPS}))
    print(f"O1 G >= F + 4: {sg['right']} vs {sf['right']} -> {'PASS' if gates['O1'] else 'fail'}")
    print(f"O2 FA/FR/MA not up: {[(m, sf[m], sg[m]) for m in ('FA', 'FR', 'MA')]} -> {'PASS' if gates['O2'] else 'fail'}")
    print(f"O3 Jev-made declines on non-DECLINE golds: {jev_declines or 'none'} -> {'PASS' if gates['O3'] else 'fail'}")
    print(f"O4 form reasons the item did not ask for: F {o4(F)} G {o4(G)} -> {'PASS' if gates['O4'] else 'fail'}")
    print(f"C1 controls (GO FD FS FG) end DECLINE, never asked a form question: bad {c1_bad or 'none'} of "
          f"{len(controls)} -> {'PASS' if gates['C1'] else 'fail'}")
    print(f"C2 form traps wrong in F {traps_f_wrong}: right in G {traps_g_right}, still waiting {traps_g_wait} -> "
          f"{'PASS' if gates['C2'] else 'fail'}")
    print(f"S0 J-ask on gold-DO items: {s0} (<= 2) -> {'PASS' if gates['S0'] else 'fail'}")
    print(f"S1 T DO calls {[r['id'] for r in t_do]}, confirmed {t_asked}; TC confirmed {tc_asked} -> "
          f"{'PASS' if gates['S1'] else 'fail'}")
    print(f"S4 V links {v_links} (<= 1) -> {'PASS' if gates['S4'] else 'fail'}")
    print(f"-> {'ALL PASS' if all(gates.values()) else 'NOT PASSED: ' + ', '.join(k for k, v in gates.items() if not v)}")
    print("\nid | group | gold | F t1 -> final [reasons] | G t1 -> final [reasons] | G Jev actions")
    skip = (None, "not_acting", "agrees_or_unsure", "no_violation", "not_clarify", "not_do", "answer_not_on_do", "no_pick")
    for k in sorted(both, key=lambda k: (GROUPS.index(G[k]["group"]), k)):
        f, g = F[k], G[k]
        acts = [f"{n}:{e.get('action')}" for n, es in g["jev"].items() for e in es if e.get("action") not in skip]
        acts += [f"{(r.get('attr') or 'group_membership')[:5]}:{'doubted' if r.get('doubted') else 'kept'}"
                 for n in ("jev_overlap", "jev_forms") for e in g["jev"][n] for r in e.get("reads") or []]
        print(f"  {k} | {g['group']} | {g['gold']} | {f['t1']} -> {f['final']} {f['reasons'] or ''} | "
              f"{g['t1']} -> {g['final']}/{g['final_basis']} {g['reasons'] or ''} | {' '.join(acts)}")
    (HERE / "gates-j4.json").write_text(json.dumps({"gates": gates, "F": sf, "G": sg, "jev_declines": jev_declines,
                                                    "o4": {"F": o4(F), "G": o4(G)}, "c1_bad": c1_bad,
                                                    "traps_f_wrong": traps_f_wrong, "traps_g_right": traps_g_right,
                                                    "traps_g_wait": traps_g_wait, "s0": s0, "t_asked": t_asked,
                                                    "tc_asked": tc_asked, "v_links": v_links}, indent=1) + "\n")


if __name__ == "__main__":
    main()
