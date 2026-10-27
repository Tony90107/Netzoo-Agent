"""Steps 2/4 offline test (LINKS.md): Jev's `result` pick on the DECLINE and CLARIFY calls; gates L1-L3, K1-K2.

Usage: OPENROUTER_API_KEY=... python3 links_offline.py run    -> links-offline.json
       python3 links_offline.py score > LINKS-OFFLINE.txt
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from netzoo_agent_core.graph import jev_guard_call as g  # noqa: E402

RESULT_LEVEL = ("full_gap", "all_results_not_available", "routing_unsupported")


def run():
    rows = json.loads((HERE / "results-data.json").read_text())
    for row in rows:
        try:
            row["jev"] = g.check_result(row["request"])
        except Exception as exc:  # noqa: BLE001 -- recorded
            row["jev"] = {"error": repr(exc)}
    (HERE / "links-offline.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    print(f"{len(rows)} calls, errors {sum('error' in r['jev'] for r in rows)}, "
          f"cost US${sum(r['jev'].get('cost', 0) for r in rows):.4f}")


def picks(row) -> bool:
    j = row["jev"]
    return j.get("result") in g.result_menu() and j["result"] not in g.RESULT_NONE and j["confidence"] >= g.THRESHOLD


def score():
    rows = json.loads((HERE / "links-offline.json").read_text())
    declines = [r for r in rows if r["kind"] == "DECLINE" and r["basis"] in RESULT_LEVEL]
    clarifies = [r for r in rows if r["kind"] == "CLARIFY"]
    d = Counter(r["gold"] for r in declines if picks(r))
    dt = Counter(r["gold"] for r in declines)
    c = Counter(r["gold"] for r in clarifies if picks(r))
    ct = Counter(r["gold"] for r in clarifies)
    gates = {"L1": d["DECLINE"] <= 6, "L2": d["DO"] >= 4, "L3": d["DO"] + d["ASK"] >= 2 * (d["DECLINE"] + d["CLARIFY"]),
             "K1": c["CLARIFY"] <= 7, "K2": c["DO"] + c["ASK"] + c["DECLINE"] >= 8}
    print(f"step 2: result-level DECLINE calls {dict(dt)}; Jev picks a workflow on {dict(d)}")
    print(f"  L1 gold-DECLINE picks {d['DECLINE']}/{dt['DECLINE']} (<= 6): {'PASS' if gates['L1'] else 'fail'}")
    print(f"  L2 gold-DO picks {d['DO']}/{dt['DO']} (>= 4): {'PASS' if gates['L2'] else 'fail'}")
    print(f"  L3 fixes {d['DO'] + d['ASK']} >= 2 x {d['DECLINE'] + d['CLARIFY']}: {'PASS' if gates['L3'] else 'fail'}")
    print(f"step 4: CLARIFY calls {dict(ct)}; Jev picks a workflow on {dict(c)}")
    print(f"  K1 gold-CLARIFY picks {c['CLARIFY']}/{ct['CLARIFY']} (<= 7): {'PASS' if gates['K1'] else 'fail'}")
    print(f"  K2 other picks {c['DO'] + c['ASK'] + c['DECLINE']}/{ct['DO'] + ct['ASK'] + ct['DECLINE']} (>= 8): "
          f"{'PASS' if gates['K2'] else 'fail'}")
    print(f"step 2 {'PASSED' if all(gates[k] for k in ('L1', 'L2', 'L3')) else 'NOT PASSED'}; "
          f"step 4 {'PASSED' if gates['K1'] and gates['K2'] else 'NOT PASSED'}\n")
    for title, group in (("step 2", declines), ("step 4", clarifies)):
        print(f"{title} rows (gold != system kind, or picked):")
        for r in group:
            if r["gold"] != r["kind"] or picks(r):
                print(f"  [{r['gold']}] {r['set']}:{r['id']} {r['basis']} -> jev {r['jev'].get('result')} "
                      f"{r['jev'].get('confidence')} | {r['request'][:110]}")


if __name__ == "__main__":
    {"run": run, "score": score}[sys.argv[1]]()
