"""Pre-registered analysis for Log 300 (II: duplicate readings, condition witness, stated modules).

Written before any code change or live trial.
Usage: python analyze.py <candidate report> ... -- <baseline report> ...

Grades the FINAL decision of every traced trial (JSON or .json.gz); pure JSON.
The scale gap: status `unsupported`, mismatch_dimensions == ["granularity"],
run_condor among alternative_actions (Log 294). Each change has its own gates and
is withdrawn alone (Log 297's lesson); a blind regression withdraws all three.

II-C (stated modules):
- validity: baseline fresh positives (3 prompts x 3 slots) in the scale gap = 0.
- effect: candidate fresh positives in the scale gap >= 6 of 9 and >= baseline + 3.
- no spread: outside the positives and the two report prompts, candidate trials with
  mismatch_dimensions == ["granularity"] and no matched action = 0.
- trap: ii-trap-held-modules selects CONDOR or ends in the scale gap in 0 candidate trials.
- controls: exact CONDOR on ii-ctl-modules-aggregate and ctl-condor-aggregate, each
  >= baseline - 1.
II-B (condition witness): mirna-degradation-en trials recommending with a
regulator_class condition >= baseline - 1 (its effect is checked offline).
II-A (duplicate readings): blind case7-en trials selecting run_lioness_dragon
<= baseline (its effect is checked offline).
Blind: candidate blind-en final WRONG <= baseline + 3 (Log 98 noise band).
Report only: gg-modules-within-each-patient, pf-patient-specific-modules.
"""
import collections
import gzip
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLIND = json.loads((HERE.parent / "blind" / "expectations.json").read_text(encoding="utf-8"))
POSITIVES = {"ii-modules-for-each-patient", "ii-per-patient-modules", "ii-patient-specific-modules"}
REPORTS = {"gg-modules-within-each-patient", "pf-patient-specific-modules"}
CONDOR_CONTROLS = ("ii-ctl-modules-aggregate", "ctl-condor-aggregate")
TRAP = "ii-trap-held-modules"
MIRNA = "mirna-degradation-en"


def load(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def blind_verdict(case, decision, reason_code):
    """score_blind.verdict applied to the final decision (as in Logs 290-298)."""
    accept, forbid = set(case.get("accept", [])), set(case.get("forbid", []))
    status = decision.get("capability_match_status")
    matched = set(decision.get("matched_actions") or [])
    candidates = set(decision.get("hypothesis_actions") or [])
    recommended = (decision.get("advisory_recommendation") or {}).get("action")
    if reason_code == "semantic_fallback":
        return "FALLBACK"
    if matched & forbid or recommended in forbid:
        return "WRONG"
    if case.get("no_tool"):
        return "OK" if not matched and decision.get("action") == "no_tool" else "WRONG"
    if status in ("exact", "fallback") and matched & accept:
        return "OK"
    if recommended in accept:
        return "OK"
    if status == "ambiguous" and candidates & accept:
        return "PARTIAL"
    return "WRONG"


def facts(row):
    trace = row["_trace"]
    decision = trace.get("decision") or {}
    matched = list(decision.get("matched_actions") or [])
    status = decision.get("capability_match_status")
    mismatch = list(decision.get("mismatch_dimensions") or [])
    alternatives = list(decision.get("alternative_actions") or [])
    recommendation = decision.get("advisory_recommendation") or {}
    blind_key = row["id"].split("-")[0]
    return {
        "id": row["id"],
        "status": status,
        "reason": trace.get("reason_code"),
        "shown": matched or list(decision.get("hypothesis_actions") or []),
        "recommended": recommendation.get("action"),
        "scale_gap": status == "unsupported" and mismatch == ["granularity"] and "run_condor" in alternatives,
        "granularity_gap": mismatch == ["granularity"] and not matched,
        "selects_condor": (status in ("exact", "fallback") and "run_condor" in matched) or recommendation.get("action") == "run_condor",
        "selects_lioness_dragon": (status in ("exact", "fallback") and "run_lioness_dragon" in matched)
                                   or recommendation.get("action") == "run_lioness_dragon",
        "regulator_condition": any(item.get("axis") == "regulator_class" for item in recommendation.get("conditions") or []),
        "exact": matched if status == "exact" else [],
        "blind": blind_verdict(BLIND[blind_key], decision, trace.get("reason_code")) if blind_key in BLIND else None,
    }


def summarize(paths, label):
    rows = [row for path in paths for row in load(path).get("results", []) if row.get("_trace")]
    items = [facts(row) for row in rows]
    by_case = collections.defaultdict(list)
    for item in items:
        by_case[item["id"]].append(item)
    print(f"== {label}: {len(items)} trials from {len(paths)} report(s)")
    for case, group in sorted(by_case.items()):
        marks = " | ".join(
            f"{item['status']}:{','.join(item['shown'])}" + ("*" if item["scale_gap"] else "")
            + (f" rec={item['recommended']}" if item["recommended"] else "")
            + (" [fallback]" if item["reason"] == "semantic_fallback" else "")
            for item in group
        )
        print(f"   {case:34s} {marks}")
    positives = [item for item in items if item["id"] in POSITIVES]
    others = [item for item in items if item["id"] not in POSITIVES | REPORTS]
    blind = [item for item in items if item["blind"] is not None]
    result = {
        "positive_trials": len(positives),
        "positive_scale_gap": sum(item["scale_gap"] for item in positives),
        "other_trials": len(others),
        "other_granularity_gap": sum(item["granularity_gap"] for item in others),
        "trap_trials": len(by_case.get(TRAP, [])),
        "trap_community": sum(item["selects_condor"] or item["scale_gap"] for item in by_case.get(TRAP, [])),
        "condor_controls_exact": {case: sum(item["exact"] == ["run_condor"] for item in by_case.get(case, []))
                                  for case in CONDOR_CONTROLS},
        "mirna_regulator_recommendations": sum(item["regulator_condition"] for item in by_case.get(MIRNA, [])),
        "case7_lioness_dragon": sum(item["selects_lioness_dragon"] for item in by_case.get("case7-en", [])),
        "report_scale_gap": {case: sum(item["scale_gap"] for item in by_case.get(case, [])) for case in sorted(REPORTS)},
        "blind_trials": len(blind),
        "blind_wrong": sum(item["blind"] == "WRONG" for item in blind),
        "blind_verdicts": dict(collections.Counter(item["blind"] for item in blind)),
    }
    print("   " + json.dumps(result))
    return result


def gates(candidate, baseline):
    groups = {
        "II-C": {
            "validity (baseline positives in the scale gap = 0)":
                baseline["positive_trials"] == 9 and baseline["positive_scale_gap"] == 0,
            "effect (>= 6 of 9 and >= baseline + 3 in the scale gap)":
                candidate["positive_trials"] == 9 and candidate["positive_scale_gap"] >= 6
                and candidate["positive_scale_gap"] >= baseline["positive_scale_gap"] + 3,
            "no spread (0 granularity gaps outside positives and reports)":
                candidate["other_trials"] == 42 and candidate["other_granularity_gap"] == 0,
            "trap (held modules never become communities)":
                candidate["trap_trials"] == 3 and candidate["trap_community"] == 0,
            **{f"control {case} exact CONDOR (>= baseline - 1)":
               candidate["condor_controls_exact"][case] >= baseline["condor_controls_exact"][case] - 1
               for case in CONDOR_CONTROLS},
        },
        "II-B": {
            "mirna-degradation-en keeps its regulator condition (>= baseline - 1)":
                candidate["mirna_regulator_recommendations"] >= baseline["mirna_regulator_recommendations"] - 1,
        },
        "II-A": {
            "case7 never newly selects LIONESS-DRAGON (<= baseline)":
                candidate["case7_lioness_dragon"] <= baseline["case7_lioness_dragon"],
        },
        "all": {
            "blind (WRONG <= baseline + 3)": candidate["blind_wrong"] <= baseline["blind_wrong"] + 3,
        },
    }
    verdict = {}
    for group, checks in groups.items():
        for name, ok in checks.items():
            print(f"   {'PASS' if ok else 'FAIL'}  {group}: {name}")
        verdict[group] = all(checks.values())
    keep = {change: verdict[change] and verdict["all"] for change in ("II-A", "II-B", "II-C")}
    print("   " + "; ".join(f"{change} {'KEPT' if ok else 'WITHDRAWN'}" for change, ok in keep.items()))
    return keep


if __name__ == "__main__":
    args = sys.argv[1:]
    split = args.index("--") if "--" in args else len(args)
    candidate = summarize([Path(p) for p in args[:split]], "candidate")
    if split < len(args):
        baseline = summarize([Path(p) for p in args[split + 1:]], "baseline")
        print("== gates")
        gates(candidate, baseline)
