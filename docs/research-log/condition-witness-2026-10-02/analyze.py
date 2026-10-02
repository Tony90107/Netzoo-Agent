"""Pre-registered analysis for Log 304 (CR1: three axes need their evidence words in the request).

Written before any code change or live trial.
Usage: python analyze.py <candidate report> ... -- <baseline report> ...

Grades the FINAL decision of every traced trial (JSON or .json.gz); pure JSON.
A "CR recommendation" is an advisory recommendation with a condition on
established_method, compute_constraints or tf_activity_vs_expression.

- validity: no provider errors in either arm.
- effect: candidate positives (4 prompts x 3 slots) with a CR recommendation = 0.
  The baseline count is reported; if it is 0 the live round shows no effect and
  the effect rests on the offline replay (Log 304).
- controls, each >= baseline - 1:
  t1-panda -> PANDA on established_method; t1-otter -> OTTER on compute_constraints;
  t1-giraffe -> GIRAFFE on tf_activity_vs_expression; mirna-degradation-en -> PUMA on
  regulator_class (the restored whole-request check of II-B).
- blind: candidate blind-en final WRONG <= baseline + 3 (Log 98 noise band).
Any failed gate withdraws CR1.
"""
import collections
import gzip
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLIND = json.loads((HERE.parent / "blind" / "expectations.json").read_text(encoding="utf-8"))
POSITIVES = {"ms-lung-generic", "ms-generic-communication", "ms-generic-strengths", "cr-generic-standard"}
CR_AXES = {"established_method", "compute_constraints", "tf_activity_vs_expression"}
CONTROLS = {
    "t1-panda": ("run_panda", "established_method"),
    "t1-otter": ("run_otter", "compute_constraints"),
    "t1-giraffe": ("run_giraffe", "tf_activity_vs_expression"),
    "mirna-degradation-en": ("run_puma", "regulator_class"),
}


def load(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def blind_verdict(case, decision, reason_code):
    """score_blind.verdict applied to the final decision (as in Logs 290-302)."""
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
    recommendation = decision.get("advisory_recommendation") or {}
    axes = {item.get("axis") for item in recommendation.get("conditions") or []}
    blind_key = row["id"].split("-")[0]
    return {
        "id": row["id"],
        "status": decision.get("capability_match_status"),
        "reason": trace.get("reason_code"),
        "shown": list(decision.get("matched_actions") or decision.get("hypothesis_actions") or []),
        "recommended": recommendation.get("action"),
        "axes": sorted(a for a in axes if a),
        "cr_recommendation": bool(axes & CR_AXES),
        "provider_error": any(call.get("exception") for call in trace["calls"]),
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
            f"{item['status']}:{','.join(item['shown'])}"
            + (f" rec={item['recommended']}{item['axes']}" if item["recommended"] else "")
            + (" [fallback]" if item["reason"] == "semantic_fallback" else "")
            for item in group
        )
        print(f"   {case:26s} {marks}")
    positives = [item for item in items if item["id"] in POSITIVES]
    blind = [item for item in items if item["blind"] is not None]
    result = {
        "trials": len(items),
        "provider_errors": sum(item["provider_error"] for item in items),
        "positive_trials": len(positives),
        "positive_cr_recommendations": sum(item["cr_recommendation"] for item in positives),
        "controls": {case: sum(item["recommended"] == action and axis in item["axes"] for item in by_case.get(case, []))
                     for case, (action, axis) in CONTROLS.items()},
        "blind_trials": len(blind),
        "blind_wrong": sum(item["blind"] == "WRONG" for item in blind),
        "blind_verdicts": dict(collections.Counter(item["blind"] for item in blind)),
    }
    print("   " + json.dumps(result))
    return result


def gates(candidate, baseline):
    checks = {
        "validity (no provider errors in either arm)":
            candidate["provider_errors"] == 0 and baseline["provider_errors"] == 0,
        "effect (candidate positives with a CR recommendation = 0)":
            candidate["positive_trials"] == 12 and candidate["positive_cr_recommendations"] == 0,
        **{f"control {case} -> {action} on {axis} (>= baseline - 1)":
           candidate["controls"][case] >= baseline["controls"][case] - 1
           for case, (action, axis) in CONTROLS.items()},
        "blind (candidate WRONG <= baseline + 3)": candidate["blind_wrong"] <= baseline["blind_wrong"] + 3,
    }
    print(f"== live effect visible: baseline positives with a CR recommendation = {baseline['positive_cr_recommendations']}")
    print("== gates (CR1)")
    for name, ok in checks.items():
        print(f"   {'PASS' if ok else 'FAIL'}  {name}")
    print("   CR1 " + ("KEPT" if all(checks.values()) else "WITHDRAWN"))


def main():
    args = sys.argv[1:]
    split = args.index("--")
    candidate = summarize([Path(p) for p in args[:split]], "candidate")
    baseline = summarize([Path(p) for p in args[split + 1:]], "baseline")
    gates(candidate, baseline)


if __name__ == "__main__":
    main()
