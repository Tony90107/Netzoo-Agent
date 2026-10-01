"""Pre-registered analysis for Log 292 (EE: scale witness). Written before any code change or live trial.

Usage: python analyze.py <candidate report> ... -- <baseline report> ...

Grades the FINAL decision of every traced trial (JSON or .json.gz); pure JSON.
Gates (Log 292):

- EE-b validity: baseline positives (2 prompts x 3 slots) exact run_lioness_dragon = 0.
- EE-c effect: candidate positives exact run_lioness_dragon >= 4 of 6.
- EE-d no hijack: outside the positives and pe-undecided-scale (blind 30 + 5
  targeted prompts x 3), candidate selections of run_lioness_dragon (exact
  match or recommendation) = 0.
- EE-d2 undecided (decides EE1b only): candidate pe-undecided-scale trials that
  end ambiguous with both run_dragon and run_lioness_dragon as candidates >= 2 of 3.
- EE-e controls: exact DRAGON on the two aggregate controls >= baseline - 1;
  exact LIONESS-PANDA on ctl-individual-tf >= baseline - 1.
- EE-f blind: candidate blind-en final WRONG <= baseline + 3 (Log 98 noise band).
- Report only: rep-individual-communities statuses; pe-undecided-scale recommendations.
"""
import collections
import gzip
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLIND = json.loads((HERE.parent / "blind" / "expectations.json").read_text(encoding="utf-8"))
TARGET = "run_lioness_dragon"
POSITIVES = {"ld-individual-networks", "pe-person-specific-multiomic"}
UNDECIDED = "pe-undecided-scale"
AGGREGATE_CONTROLS = {"ctl-individual-genes-aggregate", "ctl-dragon-aggregate"}
TF_CONTROL = "ctl-individual-tf"


def load(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def blind_verdict(case, decision, reason_code):
    """score_blind.verdict applied to the final decision (as in Log 290's analyze.py)."""
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
    status = decision.get("capability_match_status")
    blind_key = row["id"].split("-")[0]
    return {
        "id": row["id"],
        "status": status,
        "shown": matched or tie,
        "recommended": recommended,
        "selected": (status in ("exact", "fallback") and TARGET in matched) or recommended == TARGET,
        "exact_target": status == "exact" and matched == [TARGET],
        "exact_dragon": status == "exact" and matched == ["run_dragon"],
        "exact_lioness_panda": status == "exact" and matched == ["run_lioness_panda"],
        "undecided_both": status == "ambiguous" and {"run_dragon", TARGET} <= set(tie),
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
            f"{item['status']}:{','.join(item['shown'])}" + ("*" if item["selected"] else "")
            + (f" rec={item['recommended']}" if item["recommended"] else "")
            for item in group
        )
        print(f"   {case:32s} {marks}")
    positives = [item for item in items if item["id"] in POSITIVES]
    others = [item for item in items if item["id"] not in POSITIVES | {UNDECIDED}]
    blind = [item for item in items if item["blind"] is not None]
    result = {
        "positive_trials": len(positives),
        "positive_exact_target": sum(item["exact_target"] for item in positives),
        "hijack_trials": len(others),
        "hijack_selected": sum(item["selected"] for item in others),
        "undecided_trials": len(by_case.get(UNDECIDED, [])),
        "undecided_both": sum(item["undecided_both"] for item in by_case.get(UNDECIDED, [])),
        "aggregate_controls_exact_dragon": sum(
            item["exact_dragon"] for case in AGGREGATE_CONTROLS for item in by_case.get(case, [])),
        "tf_control_exact_lioness_panda": sum(item["exact_lioness_panda"] for item in by_case.get(TF_CONTROL, [])),
        "blind_trials": len(blind),
        "blind_wrong": sum(item["blind"] == "WRONG" for item in blind),
        "blind_verdicts": dict(collections.Counter(item["blind"] for item in blind)),
    }
    print("   " + json.dumps(result))
    return result


def gates(candidate, baseline):
    checks = {
        "EE-b validity (baseline positives exact LIONESS-DRAGON = 0)":
            baseline["positive_trials"] == 6 and baseline["positive_exact_target"] == 0,
        "EE-c effect (>= 4 of 6 positives exact LIONESS-DRAGON)":
            candidate["positive_trials"] == 6 and candidate["positive_exact_target"] >= 4,
        "EE-d no hijack (0 selections outside positives and the undecided prompt)":
            candidate["hijack_trials"] == 45 and candidate["hijack_selected"] == 0,
        "EE-e aggregate controls (exact DRAGON >= baseline - 1)":
            candidate["aggregate_controls_exact_dragon"] >= baseline["aggregate_controls_exact_dragon"] - 1,
        "EE-e TF control (exact LIONESS-PANDA >= baseline - 1)":
            candidate["tf_control_exact_lioness_panda"] >= baseline["tf_control_exact_lioness_panda"] - 1,
        "EE-f blind (WRONG <= baseline + 3)": candidate["blind_wrong"] <= baseline["blind_wrong"] + 3,
    }
    for name, ok in checks.items():
        print(f"   {'PASS' if ok else 'FAIL'}  {name}")
    undecided = candidate["undecided_trials"] == 3 and candidate["undecided_both"] >= 2
    print(f"   {'PASS' if undecided else 'FAIL'}  EE-d2 undecided (>= 2 of 3 ambiguous with DRAGON and LIONESS-DRAGON) -> EE1b")
    return all(checks.values()), undecided


if __name__ == "__main__":
    args = sys.argv[1:]
    split = args.index("--") if "--" in args else len(args)
    candidate = summarize([Path(p) for p in args[:split]], "candidate")
    if split < len(args):
        baseline = summarize([Path(p) for p in args[split + 1:]], "baseline")
        print("== gates")
        keep, keep_b = gates(candidate, baseline)
        print("   " + ("EE1a KEPT" if keep else "SOME GATE FAILED -> withdraw EE1 per Log 292")
              + ("; EE1b KEPT" if keep and keep_b else "; EE1b WITHDRAWN" if keep else ""))
