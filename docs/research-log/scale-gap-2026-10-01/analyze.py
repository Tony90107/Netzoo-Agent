"""Pre-registered analysis for Log 294 (FF: stated-scale gap). Written before any code change or live trial.

Usage: python analyze.py <candidate report> ... -- <baseline report> ...

Grades the FINAL decision of every traced trial (JSON or .json.gz); pure JSON.
The scale gap is the decision shape FF2 introduces: status `unsupported`,
mismatch_dimensions == ["granularity"], run_condor among alternative_actions.
Gates (Log 294):

- FF-b validity: baseline positives (3 prompts x 3 slots) ending in the scale gap = 0.
- FF-c effect: candidate positives ending in the scale gap >= 6 of 9.
- FF-d no spread: candidate trials outside the positives (blind 30 + 4 prompts x 3)
  whose decision has mismatch_dimensions == ["granularity"] with no matched action = 0.
- FF-e controls: exact CONDOR, exact LIONESS-PUMA (role-both-ss-en) and exact
  LIONESS-PANDA each >= baseline - 1.
- FF-f blind: candidate blind-en final WRONG <= baseline + 3 (Log 98 noise band).
- Report only: rep-communities-each-patient-unstated; semantic fallbacks on positives.
"""
import collections
import gzip
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLIND = json.loads((HERE.parent / "blind" / "expectations.json").read_text(encoding="utf-8"))
POSITIVES = {"rep-individual-communities", "pf-patient-specific-modules", "pf-per-patient-communities"}
CONTROLS = {"ctl-condor-aggregate": "run_condor", "role-both-ss-en": "run_lioness_puma",
            "ctl-per-sample-tf": "run_lioness_panda"}


def load(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def blind_verdict(case, decision, reason_code):
    """score_blind.verdict applied to the final decision (as in Logs 290 and 292)."""
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
    blind_key = row["id"].split("-")[0]
    return {
        "id": row["id"],
        "status": status,
        "reason": trace.get("reason_code"),
        "shown": matched or list(decision.get("hypothesis_actions") or []),
        "alternatives": alternatives,
        "scale_gap": status == "unsupported" and mismatch == ["granularity"] and "run_condor" in alternatives,
        "granularity_gap": mismatch == ["granularity"] and not matched,
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
            f"{item['status']}:{','.join(item['shown'])}" + (f" alt={','.join(item['alternatives'])}" if item["alternatives"] else "")
            + ("*" if item["scale_gap"] else "") + (" [fallback]" if item["reason"] == "semantic_fallback" else "")
            for item in group
        )
        print(f"   {case:40s} {marks}")
    positives = [item for item in items if item["id"] in POSITIVES]
    others = [item for item in items if item["id"] not in POSITIVES]
    blind = [item for item in items if item["blind"] is not None]
    result = {
        "positive_trials": len(positives),
        "positive_scale_gap": sum(item["scale_gap"] for item in positives),
        "positive_semantic_fallback": sum(item["reason"] == "semantic_fallback" for item in positives),
        "other_trials": len(others),
        "other_granularity_gap": sum(item["granularity_gap"] for item in others),
        "controls_exact": {case: sum(item["exact"] == [action] for item in by_case.get(case, []))
                           for case, action in CONTROLS.items()},
        "blind_trials": len(blind),
        "blind_wrong": sum(item["blind"] == "WRONG" for item in blind),
        "blind_verdicts": dict(collections.Counter(item["blind"] for item in blind)),
    }
    print("   " + json.dumps(result))
    return result


def gates(candidate, baseline):
    checks = {
        "FF-b validity (baseline positives in the scale gap = 0)":
            baseline["positive_trials"] == 9 and baseline["positive_scale_gap"] == 0,
        "FF-c effect (>= 6 of 9 positives end in the scale gap)":
            candidate["positive_trials"] == 9 and candidate["positive_scale_gap"] >= 6,
        "FF-d no spread (0 granularity gaps outside the positives)":
            candidate["other_trials"] == 42 and candidate["other_granularity_gap"] == 0,
        "FF-f blind (WRONG <= baseline + 3)": candidate["blind_wrong"] <= baseline["blind_wrong"] + 3,
    }
    for case in CONTROLS:
        checks[f"FF-e control {case} (exact >= baseline - 1)"] = (
            candidate["controls_exact"][case] >= baseline["controls_exact"][case] - 1)
    for name, ok in checks.items():
        print(f"   {'PASS' if ok else 'FAIL'}  {name}")
    return all(checks.values())


if __name__ == "__main__":
    args = sys.argv[1:]
    split = args.index("--") if "--" in args else len(args)
    candidate = summarize([Path(p) for p in args[:split]], "candidate")
    if split < len(args):
        baseline = summarize([Path(p) for p in args[split + 1:]], "baseline")
        print("== gates")
        print("   ALL PASS" if gates(candidate, baseline) else "   SOME GATE FAILED -> withdraw FF per Log 294")
