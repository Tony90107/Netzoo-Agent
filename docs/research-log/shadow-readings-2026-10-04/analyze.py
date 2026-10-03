"""Pre-registered analysis for Log 337 (SR: shadow readings).

Usage (repository root): python docs/research-log/shadow-readings-2026-10-04/analyze.py

Reads live-sr-{base,cand}-{a,b,blind}.json(.gz). Gates as declared in Log 337.
"""
import collections
import gzip
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(HERE), str(ROOT / "scripts"), str(ROOT / "docs" / "research-log" / "preference-witness-2026-10-03")]

from replay_pw import BLIND, verdict  # noqa: E402
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis  # noqa: E402
from scan_shadow import shadowed_by  # noqa: E402  (SR was withdrawn, Log 338; the prototype defines a shadow)


def load(arm, part):
    path = HERE / f"live-sr-{arm}-{part}.json.gz"
    return json.load(gzip.open(path, "rt"))["results"] if path.exists() else []


def shadows(task, decision):
    readings = [OutcomeHypothesis.model_validate(h) for h in decision.get("outcome_hypotheses") or []]
    return sum(1 for r in readings for o in readings
               if o is not r and shadowed_by(task, r, o) and not shadowed_by(task, o, r))


def offered(decision):
    return set(decision.get("hypothesis_actions") or []) | set(decision.get("matched_actions") or [])


def main():
    summary = {}
    for arm in ("base", "cand"):
        a, b, blind = load(arm, "a"), load(arm, "b"), load(arm, "blind")
        rows = a + b + blind
        errors = sum(any(c.get("exception") for c in r["_trace"]["calls"]) for r in rows)
        shadow_total = sum(shadows(r["_trace"]["prompt"], r["_trace"]["decision"]) > 0 for r in rows)
        t7 = [r["_trace"] for r in a if r["id"] == "test7-en"]
        t2 = [r["_trace"] for r in a if r["id"] == "test2-en"]
        prepare_kept = sum(any(h["outcome"]["operation"] == "prepare" for h in t["decision"]["outcome_hypotheses"] or [])
                           and t["decision"].get("capability_match_status") != "ambiguous" for t in t7)
        shadow_tie = sum(shadows(t["prompt"], t["decision"]) > 0 and t["decision"].get("capability_match_status") == "ambiguous"
                         for t in t7)
        giraffe = sum("run_giraffe" in offered(t["decision"]) for t in t2)
        controls = collections.Counter()
        for r in b:
            d = r["_trace"]["decision"]
            ok = {"gran-mirna-unstated-control": {"run_puma", "run_lioness_puma"} <= offered(d),
                  "test1-en": d.get("capability_match_status") == "ambiguous" and "run_panda" in offered(d),
                  "test4-en": d.get("capability_match_status") == "ambiguous" and "run_panda" in offered(d)}[r["id"]]
            controls[r["id"]] += ok
        verdicts = collections.Counter(
            verdict(BLIND[r["id"].split("-")[0]], r["_trace"]["decision"], r["_trace"].get("reason_code"))
            for r in blind if r["id"].split("-")[0] in BLIND)
        fired = sum(any(e["type"] == "routing.shadow_readings_dropped" for e in r["_trace"]["events"]) for r in rows)
        summary[arm] = dict(trials=len(rows), errors=errors, final_shadows=shadow_total, sr_fired=fired,
                            t7_prepare_kept=f"{prepare_kept}/{len(t7)}", t7_shadow_tie=shadow_tie,
                            t2_giraffe=f"{giraffe}/{len(t2)}", controls=dict(controls), blind=dict(verdicts))
        print(arm, json.dumps(summary[arm]))
        for t in t7:
            d = t["decision"]
            print("   test7", d.get("capability_match_status"),
                  [(h["outcome"]["operation"], h["outcome"]["artifact_type"]) for h in d["outcome_hypotheses"] or []])
    base, cand = summary["base"], summary["cand"]
    num = lambda text: int(text.split("/")[0])
    gates = {
        "validity": base["errors"] == 0 and cand["errors"] == 0,
        "soundness": cand["final_shadows"] == 0,
        "effect_t7": (num(cand["t7_prepare_kept"]) >= num(base["t7_prepare_kept"])
                      and (base["t7_shadow_tie"] == 0 or cand["t7_shadow_tie"] == 0)),
        "effect_by_replay": base["t7_shadow_tie"] == 0,
        "t2_giraffe": num(cand["t2_giraffe"]) <= num(base["t2_giraffe"]),
        "controls": all(cand["controls"].get(k, 0) >= base["controls"].get(k, 0) - 1
                        for k in ("gran-mirna-unstated-control", "test1-en", "test4-en")),
        "blind": (cand["blind"].get("OK", 0) >= base["blind"].get("OK", 0) - 1
                  and cand["blind"].get("WRONG", 0) <= base["blind"].get("WRONG", 0) + 1),
    }
    print("gates", json.dumps(gates))


if __name__ == "__main__":
    main()
