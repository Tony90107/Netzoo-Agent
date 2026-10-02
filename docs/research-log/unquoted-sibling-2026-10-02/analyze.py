"""Pre-registered analysis for Log 313 (MW: a multi-omic reading needs a second layer named in the request).

Written before any code change or live trial.
Usage: python analyze.py <candidate report> ... -- <baseline report> ...

Grades the FINAL decision of every traced trial (JSON or .json.gz); pure JSON.
The layer witness is `scan_multiomic.LAYER` (the prototype), independent of
either arm's code.

MW gates (any failure -> withdraw MW):
- sanity: candidate trials on prompts naming no second layer (blind and targeted)
  whose final decision keeps a multi_omic_network reading beside another
  reading = 0.
- effect: positives (t2-en, t2-follow-has-priors, ms-lung-generic,
  ms-generic-communication): baseline trials showing DRAGON or LIONESS-DRAGON
  >= 3 of 12, and candidate <= 1. With baseline < 3 the misreading did not occur
  live and the effect is judged by replay.
- layer controls (ctl-dragon-aggregate, ld-per-patient-methylation,
  pe-person-specific-multiomic, ld-sample-specific-multiomic): candidate trials
  showing DRAGON or LIONESS-DRAGON >= baseline - 1, each.
- other controls: t2-follow-expression-only showing LIONESS-COEXPRESSION or
  BONOBO >= baseline - 1; ms-ctl-message-passing exact PANDA >= baseline - 1.
- blind case7-en OK >= baseline - 1; blind WRONG <= baseline + 3.
Validity: no provider errors in either arm (Log 290 supplement 4).
"""
import collections
import gzip
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from scan_multiomic import LAYER  # noqa: E402

BLIND = json.loads((HERE.parent / "blind" / "expectations.json").read_text(encoding="utf-8"))
DRAGONS = {"run_dragon", "run_lioness_dragon"}
COEXPRESSION = {"run_lioness_coexpression", "run_bonobo"}
POSITIVES = ("t2-en", "t2-follow-has-priors", "ms-lung-generic", "ms-generic-communication")
LAYER_CONTROLS = ("ctl-dragon-aggregate", "ld-per-patient-methylation", "pe-person-specific-multiomic",
                  "ld-sample-specific-multiomic")


def load(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def blind_verdict(case, decision, reason_code):
    """score_blind.verdict applied to the final decision (as in Logs 290-310)."""
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
    recommended = (decision.get("advisory_recommendation") or {}).get("action")
    shown = set(matched) | set(decision.get("hypothesis_actions") or []) | ({recommended} if recommended else set())
    readings = [item["outcome"]["artifact_type"] for item in decision.get("outcome_hypotheses") or []]
    blind_key = row["id"].split("-")[0]
    return {
        "id": row["id"],
        "status": status,
        "reason": trace.get("reason_code"),
        "shown_list": matched or list(decision.get("hypothesis_actions") or []),
        "recommended": recommended,
        "exact": matched if status == "exact" else [],
        "unnamed": LAYER.search(trace.get("prompt", "")) is None,
        "multiomic_sibling": len(readings) >= 2 and "multi_omic_network" in readings,
        "dragon": bool(shown & DRAGONS),
        "coexpression": bool(shown & COEXPRESSION),
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
            f"{item['status']}:{','.join(item['shown_list'])}"
            + (f" rec={item['recommended']}" if item["recommended"] else "")
            + (" [fallback]" if item["reason"] == "semantic_fallback" else "")
            + (" [MULTIOMIC-SIBLING]" if item["unnamed"] and item["multiomic_sibling"] else "")
            for item in group
        )
        print(f"   {case:30s} {'(no layer) ' if group[0]['unnamed'] else ''}{marks}")
    blind = [item for item in items if item["blind"] is not None]
    result = {
        "trials": len(items),
        "provider_errors": sum(item["provider_error"] for item in items),
        "unnamed_siblings": sum(item["unnamed"] and item["multiomic_sibling"] for item in items),
        "positive_trials": sum(item["id"] in POSITIVES for item in items),
        "positive_dragon": sum(item["id"] in POSITIVES and item["dragon"] for item in items),
        "layer_controls": {case: sum(item["dragon"] for item in by_case.get(case, [])) for case in LAYER_CONTROLS},
        "expression_only_coexpression": sum(item["coexpression"] for item in by_case.get("t2-follow-expression-only", [])),
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
    effect_label = "effect (baseline DRAGON-family on positives >= 3 of 12, candidate <= 1)"
    checks = {
        "sanity (no multi-omic sibling reading survives on a prompt naming no second layer)":
            candidate["unnamed_siblings"] == 0,
        effect_label: baseline["positive_trials"] == 12 and baseline["positive_dragon"] >= 3
                      and candidate["positive_dragon"] <= 1,
        **{f"layer control {case} shows DRAGON-family (>= baseline - 1)":
           candidate["layer_controls"][case] >= baseline["layer_controls"][case] - 1 for case in LAYER_CONTROLS},
        "t2-follow-expression-only shows LIONESS-COEXPRESSION/BONOBO (>= baseline - 1)":
            candidate["expression_only_coexpression"] >= baseline["expression_only_coexpression"] - 1,
        "ms-ctl-message-passing exact PANDA (>= baseline - 1)":
            candidate["message_passing_panda"] >= baseline["message_passing_panda"] - 1,
        "blind case7-en OK (>= baseline - 1)": candidate["case7_ok"] >= baseline["case7_ok"] - 1,
        "blind (candidate WRONG <= baseline + 3)": candidate["blind_wrong"] <= baseline["blind_wrong"] + 3,
    }
    print(f"== validity (no provider errors): {'PASS' if validity else 'FAIL -> void and rerun'}")
    print("== gates (MW)")
    for label, ok in checks.items():
        print(f"   {'PASS' if ok else 'FAIL'}  {label}")
    failed = [label for label, ok in checks.items() if not ok]
    effect_unobserved = failed == [effect_label] and baseline["positive_dragon"] < 3 and candidate["positive_dragon"] <= 1
    verdict = ("KEPT" if validity and not failed else
               "EFFECT NOT OBSERVED LIVE -> judge by replay" if validity and effect_unobserved else
               "WITHDRAWN" if validity else "VOID")
    print(f"   MW {verdict}")


def main():
    args = sys.argv[1:]
    split = args.index("--")
    candidate = summarize([Path(p) for p in args[:split]], "candidate")
    baseline = summarize([Path(p) for p in args[split + 1:]], "baseline")
    gates(candidate, baseline)


if __name__ == "__main__":
    main()
