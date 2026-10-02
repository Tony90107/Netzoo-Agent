"""Pre-registered analysis for Log 315 (CS: "a handful" or "dozens" must be the user's own words).

Written before any code change or live trial.
Usage: python analyze.py <candidate report> ... -- <baseline report> ...

Grades the FINAL decision of every traced trial (JSON or .json.gz); pure JSON.
The witness is `replay_cs.COHORT_WITNESS` (the prototype), independent of
either arm's code.

CS gates (any failure -> withdraw CS):
- sanity: candidate trials (blind and targeted) whose recommendation rests on a
  cohort_size condition the request does not state in words = 0.
- effect: count-only prompts (t2-follow-expression-only,
  trap-individual-coexpression, cs-count-tumours, cs-count-cohort): baseline
  recommendations resting on cohort_size >= 3 of 12, and candidate 0. With
  baseline < 3 the mapping did not occur live and the effect is judged by replay.
- word controls: cs-ctl-few recommends BONOBO; cs-ctl-hundreds and
  cs-ctl-dozens recommend LIONESS-COEXPRESSION; blind case3-en OK;
  mirna-degradation-en recommends PUMA -- each >= baseline - 1.
- blind: candidate WRONG <= baseline + 3.
Validity: no provider errors in either arm (Log 290 supplement 4).
"""
import collections
import gzip
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from replay_cs import COHORT_WITNESS  # noqa: E402

BLIND = json.loads((HERE.parent / "blind" / "expectations.json").read_text(encoding="utf-8"))
COUNT_ONLY = ("t2-follow-expression-only", "trap-individual-coexpression", "cs-count-tumours", "cs-count-cohort")
WORD_CONTROLS = {
    "cs-ctl-few": "run_bonobo",
    "cs-ctl-hundreds": "run_lioness_coexpression",
    "cs-ctl-dozens": "run_lioness_coexpression",
    "mirna-degradation-en": "run_puma",
}


def load(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def blind_verdict(case, decision, reason_code):
    """score_blind.verdict applied to the final decision (as in Logs 290-314)."""
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
    prompt = trace.get("prompt", "")
    decision = trace.get("decision") or {}
    recommendation = decision.get("advisory_recommendation") or {}
    cohort = [c for c in recommendation.get("conditions") or [] if c.get("axis") == "cohort_size"]
    blind_key = row["id"].split("-")[0]
    return {
        "id": row["id"],
        "status": decision.get("capability_match_status"),
        "reason": trace.get("reason_code"),
        "shown": list(decision.get("matched_actions") or decision.get("hypothesis_actions") or []),
        "recommended": recommendation.get("action"),
        "cohort_rec": bool(cohort),
        "unstated_cohort": any(not re.search(COHORT_WITNESS.get(c.get("value"), r"(?!)"), prompt, re.I) for c in cohort),
        "question": decision.get("clarification_question") or "",
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
            + (" [cohort]" if item["cohort_rec"] else "")
            + (" [UNSTATED-COHORT]" if item["unstated_cohort"] else "")
            + (" [asks size]" if "how many samples" in item["question"] else "")
            + (" [fallback]" if item["reason"] == "semantic_fallback" else "")
            for item in group
        )
        print(f"   {case:30s} {marks}")
    blind = [item for item in items if item["blind"] is not None]
    result = {
        "trials": len(items),
        "provider_errors": sum(item["provider_error"] for item in items),
        "unstated_cohort": sum(item["unstated_cohort"] for item in items),
        "count_only_trials": sum(item["id"] in COUNT_ONLY for item in items),
        "count_only_cohort_recs": sum(item["id"] in COUNT_ONLY and item["cohort_rec"] for item in items),
        "word_controls": {case: sum(item["recommended"] == action for item in by_case.get(case, []))
                          for case, action in WORD_CONTROLS.items()},
        "case3_ok": sum(item["blind"] == "OK" for item in by_case.get("case3-en", [])),
        "blind_trials": len(blind),
        "blind_wrong": sum(item["blind"] == "WRONG" for item in blind),
        "blind_verdicts": dict(collections.Counter(item["blind"] for item in blind)),
    }
    print("   " + json.dumps(result))
    return result


def gates(candidate, baseline):
    validity = candidate["provider_errors"] == 0 and baseline["provider_errors"] == 0
    effect_label = "effect (baseline cohort-size recommendations on count-only prompts >= 3 of 12, candidate 0)"
    checks = {
        "sanity (no recommendation rests on a cohort size the request does not state in words)":
            candidate["unstated_cohort"] == 0,
        effect_label: baseline["count_only_trials"] == 12 and baseline["count_only_cohort_recs"] >= 3
                      and candidate["count_only_cohort_recs"] == 0,
        **{f"word control {case} recommends {action} (>= baseline - 1)":
           candidate["word_controls"][case] >= baseline["word_controls"][case] - 1
           for case, action in WORD_CONTROLS.items()},
        "blind case3-en OK (>= baseline - 1)": candidate["case3_ok"] >= baseline["case3_ok"] - 1,
        "blind (candidate WRONG <= baseline + 3)": candidate["blind_wrong"] <= baseline["blind_wrong"] + 3,
    }
    print(f"== validity (no provider errors): {'PASS' if validity else 'FAIL -> void and rerun'}")
    print("== gates (CS)")
    for label, ok in checks.items():
        print(f"   {'PASS' if ok else 'FAIL'}  {label}")
    failed = [label for label, ok in checks.items() if not ok]
    effect_unobserved = (failed == [effect_label] and baseline["count_only_cohort_recs"] < 3
                         and candidate["count_only_cohort_recs"] == 0)
    verdict = ("KEPT" if validity and not failed else
               "EFFECT NOT OBSERVED LIVE -> judge by replay" if validity and effect_unobserved else
               "WITHDRAWN" if validity else "VOID")
    print(f"   CS {verdict}")


def main():
    args = sys.argv[1:]
    split = args.index("--")
    candidate = summarize([Path(p) for p in args[:split]], "candidate")
    baseline = summarize([Path(p) for p in args[split + 1:]], "baseline")
    gates(candidate, baseline)


if __name__ == "__main__":
    main()
