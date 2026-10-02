"""Pre-registered analysis for Log 309 (SW: a request naming no unit keeps no per-sample claim).

Written before any code change or live trial.
Usage: python analyze.py <candidate report> ... -- <baseline report> ...

Grades the FINAL decision of every traced trial (JSON or .json.gz); pure JSON.
The per-unit witness is copied from `scan_unit.py` (the prototype), independent
of either arm's code.

SW gates (any failure -> withdraw SW):
- sanity: candidate trials on prompts naming no unit (blind and targeted) where the
  final decision keeps a per-sample reading, picks a per-sample workflow (exact or
  fallback, not by workflow name) or recommends one, or where the discriminator
  accepted a per-sample tag = 0.
- effect: t1-en, t1-zh, ii-trap-held-modules: baseline per-sample picks >= 3 of 9.
  Below that the misreading did not occur live and the effect is judged by replay.
- unit-word controls (t2-en, ctl-per-sample-tf, ctl-individual-tf, sw-ctl-next-patient):
  candidate trials showing a per-sample workflow >= baseline - 1, each.
- aggregate control ms-ctl-message-passing: exact PANDA >= baseline - 1.
- DD3 control blind case7-en: OK >= baseline - 1.
- blind: candidate blind-en final WRONG <= baseline + 3.
Validity: no provider errors in either arm (Log 290 supplement 4).
"""
import collections
import gzip
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from scan_unit import per_unit_mention  # noqa: E402

BLIND = json.loads((HERE.parent / "blind" / "expectations.json").read_text(encoding="utf-8"))
PER_SAMPLE_ACTIONS = {"run_lioness_panda", "run_lioness_puma", "run_lioness_coexpression",
                      "run_lioness_dragon", "run_bonobo"}
PER_SAMPLE_TAGS = {"sample_specific", "leave_one_out_network_inference"}
POSITIVES = {"t1-en", "t1-zh", "ii-trap-held-modules"}
UNIT_CONTROLS = ("t2-en", "ctl-per-sample-tf", "ctl-individual-tf", "sw-ctl-next-patient")


def load(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def blind_verdict(case, decision, reason_code):
    """score_blind.verdict applied to the final decision (as in Logs 290-307)."""
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
    status = decision.get("capability_match_status")
    matched = list(decision.get("matched_actions") or [])
    shown = set(matched) | set(decision.get("hypothesis_actions") or [])
    recommended = (decision.get("advisory_recommendation") or {}).get("action")
    readings = decision.get("outcome_hypotheses") or []
    per_sample_reading = any(
        item["outcome"].get("granularity") == "sample_specific"
        or set(item["outcome"].get("selection_tags") or []) & PER_SAMPLE_TAGS
        for item in readings
    )
    per_sample_pick = (
        (status in ("exact", "fallback") and bool(set(matched) & PER_SAMPLE_ACTIONS)
         and decision.get("match_basis") != "workflow_name")
        or recommended in PER_SAMPLE_ACTIONS
    )
    discriminator_tag = any(
        event["type"] == "routing.semantic_discriminator_accepted"
        and set(event["payload"].get("selection_tags") or []) & PER_SAMPLE_TAGS
        for event in trace["events"]
    )
    blind_key = row["id"].split("-")[0]
    return {
        "id": row["id"],
        "status": status,
        "reason": trace.get("reason_code"),
        "shown": matched or list(decision.get("hypothesis_actions") or []),
        "recommended": recommended,
        "exact": matched if status == "exact" else [],
        "unnamed": per_unit_mention(trace.get("prompt", "")) is None,
        "per_sample_reading": per_sample_reading,
        "per_sample_pick": per_sample_pick,
        "discriminator_tag": discriminator_tag,
        "shows_per_sample": bool(shown & PER_SAMPLE_ACTIONS) or recommended in PER_SAMPLE_ACTIONS,
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
            + (f" rec={item['recommended']}" if item["recommended"] else "")
            + (" [fallback]" if item["reason"] == "semantic_fallback" else "")
            + (" [PS-READING]" if item["unnamed"] and item["per_sample_reading"] else "")
            + (" [PS-PICK]" if item["unnamed"] and item["per_sample_pick"] else "")
            + (" [PS-TAG]" if item["unnamed"] and item["discriminator_tag"] else "")
            for item in group
        )
        print(f"   {case:24s} {'(no unit) ' if group[0]['unnamed'] else ''}{marks}")
    blind = [item for item in items if item["blind"] is not None]
    result = {
        "trials": len(items),
        "provider_errors": sum(item["provider_error"] for item in items),
        "unnamed_violations": sum(item["unnamed"] and (item["per_sample_reading"] or item["per_sample_pick"]
                                                       or item["discriminator_tag"]) for item in items),
        "positive_trials": sum(item["id"] in POSITIVES for item in items),
        "positive_per_sample_picks": sum(item["id"] in POSITIVES and item["per_sample_pick"] for item in items),
        "unit_controls": {case: sum(item["shows_per_sample"] for item in by_case.get(case, []))
                          for case in UNIT_CONTROLS},
        "message_passing_panda": sum(item["exact"] == ["run_panda"] for item in by_case.get("ms-ctl-message-passing", [])),
        "case7_ok": sum(item["blind"] == "OK" for item in by_case.get("case7-en", [])),
        "blind_trials": len(blind),
        "blind_wrong": sum(item["blind"] == "WRONG" for item in blind),
        "blind_verdicts": dict(collections.Counter(item["blind"] for item in blind)),
    }
    print("   " + json.dumps(result))
    return result


def gates(candidate, baseline):
    validity = candidate["provider_errors"] == 0 and baseline["provider_errors"] == 0
    checks = {
        "sanity (no per-sample claim survives on a prompt naming no unit)": candidate["unnamed_violations"] == 0,
        "effect (baseline per-sample picks on t1-en/t1-zh/ii-trap >= 3 of 9)":
            baseline["positive_trials"] == 9 and baseline["positive_per_sample_picks"] >= 3,
        **{f"unit control {case} shows a per-sample workflow (>= baseline - 1)":
           candidate["unit_controls"][case] >= baseline["unit_controls"][case] - 1 for case in UNIT_CONTROLS},
        "aggregate control ms-ctl-message-passing exact PANDA (>= baseline - 1)":
            candidate["message_passing_panda"] >= baseline["message_passing_panda"] - 1,
        "DD3 control blind case7-en OK (>= baseline - 1)": candidate["case7_ok"] >= baseline["case7_ok"] - 1,
        "blind (candidate WRONG <= baseline + 3)": candidate["blind_wrong"] <= baseline["blind_wrong"] + 3,
    }
    print(f"== validity (no provider errors): {'PASS' if validity else 'FAIL -> void and rerun'}")
    print("== gates (SW)")
    for label, ok in checks.items():
        print(f"   {'PASS' if ok else 'FAIL'}  {label}")
    effect_only = [label for label, ok in checks.items() if not ok] == [
        "effect (baseline per-sample picks on t1-en/t1-zh/ii-trap >= 3 of 9)"]
    verdict = ("KEPT" if validity and all(checks.values()) else
               "EFFECT NOT OBSERVED LIVE -> judge by replay" if validity and effect_only else
               "WITHDRAWN" if validity else "VOID")
    print(f"   SW {verdict}")


def main():
    args = sys.argv[1:]
    split = args.index("--")
    candidate = summarize([Path(p) for p in args[:split]], "candidate")
    baseline = summarize([Path(p) for p in args[split + 1:]], "baseline")
    gates(candidate, baseline)


if __name__ == "__main__":
    main()
