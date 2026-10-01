"""Pre-registered analysis for Log 290 (DD: LIONESS-DRAGON). Written before any live trial.

Usage: python analyze.py <candidate report> ... -- <baseline report> ...

Reads the traced harness reports (JSON or .json.gz) and grades the FINAL
decision of every trial; pure JSON, runs anywhere. Gates (Log 290):

- DD-c effect: of the 9 candidate positive trials (3 prompts x 3 slots), at
  least 6 end exact on run_lioness_dragon.
- DD-d no hijack: no candidate trial outside the positives selects
  run_lioness_dragon (exact match or recommendation). Appearing inside a tie
  is reported, not gated. The aggregate control keeps exact DRAGON in at least
  (baseline count - 1) trials.
- DD-e blind regression: candidate blind-en final WRONG <= baseline + 3
  (Log 98 noise band).
- DD2 (report only): ld-otter-per-sample trials whose decision carries a method
  gap on relaxed_graph_matching, so the LIONESS-OTTER reference is shown.
"""
import collections
import gzip
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLIND = json.loads((HERE.parent / "blind" / "expectations.json").read_text(encoding="utf-8"))
TARGET = "run_lioness_dragon"
POSITIVES = {"ld-per-patient-methylation", "ld-sample-specific-multiomic", "ld-individual-networks"}


def load(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def blind_verdict(case, decision, reason_code):
    """score_blind.verdict applied to the final decision."""
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
    tie = list(decision.get("hypothesis_actions") or [])
    recommended = (decision.get("advisory_recommendation") or {}).get("action")
    stated = [h.get("basis") for h in decision.get("stated_hypotheses") or []]
    status = decision.get("capability_match_status")
    gap = decision.get("advisory_capability_gap") or {}
    blind_key = row["id"].split("-")[0]
    return {
        "id": row["id"],
        "status": status,
        "shown": matched or tie,
        "selected": (status in ("exact", "fallback") and TARGET in matched) or recommended == TARGET,
        "in_tie": TARGET in tie or TARGET in stated,
        "exact_target": status == "exact" and matched == [TARGET],
        "exact_dragon": status == "exact" and matched == ["run_dragon"],
        "blind": blind_verdict(BLIND[blind_key], decision, trace.get("reason_code")) if blind_key in BLIND else None,
        "otter_gap": "relaxed_graph_matching" in (gap.get("selection_tags") or []),
    }


def summarize(paths, label):
    rows = [row for path in paths for row in load(path).get("results", []) if row.get("_trace")]
    items = [facts(row) for row in rows]
    by_case = collections.defaultdict(list)
    for item in items:
        by_case[item["id"]].append(item)
    print(f"== {label}: {len(items)} trials from {len(paths)} report(s)")
    for case, group in sorted(by_case.items()):
        marks = " | ".join(f"{item['status']}:{','.join(item['shown'])}" + ("*" if item["selected"] else "") for item in group)
        print(f"   {case:30s} {marks}")
    positives = [item for item in items if item["id"] in POSITIVES]
    others = [item for item in items if item["id"] not in POSITIVES]
    blind = [item for item in items if item["blind"] is not None]
    result = {
        "positive_trials": len(positives),
        "positive_exact_target": sum(item["exact_target"] for item in positives),
        "hijack_selected": sum(item["selected"] for item in others),
        "hijack_in_tie": sum(item["in_tie"] for item in others),
        "aggregate_control_exact_dragon": sum(item["exact_dragon"] for item in by_case.get("ctl-dragon-aggregate", [])),
        "blind_trials": len(blind),
        "blind_wrong": sum(item["blind"] == "WRONG" for item in blind),
        "blind_verdicts": dict(collections.Counter(item["blind"] for item in blind)),
        "otter_gap": sum(item["otter_gap"] for item in by_case.get("ld-otter-per-sample", [])),
    }
    print("   " + json.dumps(result))
    return result


def gates(candidate, baseline):
    checks = {
        "DD-c effect (>= 6 of 9 positives exact LIONESS-DRAGON)":
            candidate["positive_trials"] == 9 and candidate["positive_exact_target"] >= 6,
        "DD-d no hijack (0 selections outside positives)": candidate["hijack_selected"] == 0,
        "DD-d aggregate control (exact DRAGON >= baseline - 1)":
            candidate["aggregate_control_exact_dragon"] >= baseline["aggregate_control_exact_dragon"] - 1,
        "DD-e blind (WRONG <= baseline + 3)": candidate["blind_wrong"] <= baseline["blind_wrong"] + 3,
        "validity (baseline never names LIONESS-DRAGON)":
            baseline["positive_exact_target"] == 0 and baseline["hijack_selected"] == 0 and baseline["hijack_in_tie"] == 0,
    }
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
        print("   ALL PASS" if gates(candidate, baseline) else "   SOME GATE FAILED -> withdraw per Log 290")
