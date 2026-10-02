"""Pre-registered analysis for Log 302 (MS1: a tie-breaking method tag must be stated by its quote).

Written before any code change or live trial.
Usage: python analyze.py <candidate report> ... -- <baseline report> ...

Grades the FINAL decision of every traced trial (JSON or .json.gz); pure JSON.
MS1's effect (the recorded 2026-10-02 discriminator payload no longer picks
GIRAFFE) is checked offline; this round checks that nothing else moves.

- sanity: candidate trials where the discriminator was accepted although a
  witnessed tag it selected has no quote stating it = 0.
- positives (3 generic PANDA/OTTER/GIRAFFE prompts x 3 slots): candidate single
  picks among PANDA/OTTER/GIRAFFE <= baseline single picks.
- controls: exact expected workflow on gran-tf-agg-relaxed-en (OTTER),
  ms-ctl-message-passing (PANDA), ms-ctl-factorization (GIRAFFE) and blind
  case2-en (OTTER), each >= baseline - 1.
- blind: candidate blind-en final WRONG <= baseline + 3 (Log 98 noise band).
Any failed gate withdraws MS1. MS2 (typed comparison) is not exercised here.
"""
import collections
import gzip
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLIND = json.loads((HERE.parent / "blind" / "expectations.json").read_text(encoding="utf-8"))
POSITIVES = {"ms-lung-generic", "ms-generic-communication", "ms-generic-strengths"}
TRIO = {"run_panda", "run_otter", "run_giraffe"}
CONTROLS = {
    "gran-tf-agg-relaxed-en": "run_otter",
    "ms-ctl-message-passing": "run_panda",
    "ms-ctl-factorization": "run_giraffe",
    "case2-en": "run_otter",
}
# The MS1 table as pre-declared in Log 302 (copied, so the analysis does not
# depend on either arm's code).
WITNESSES = {
    "message_passing": r"message[- ]?passing|pass(?:es|ing)?\s+messages|iterat|訊息傳遞|消息傳遞|消息传递|信息傳遞|信息传递|迭代",
    "relaxed_graph_matching": (r"graph[- ]?matching|objective|loss|optimi[sz]|gradient|converge|convex|heuristic"
                               r"|圖匹配|图匹配|目標|目标|損失|损失|最佳化|最優化|优化|梯度|收斂|收敛|凸|啟發式|启发式"),
    "biologically_informed_matrix_factorization": r"factori[sz]|decompos|矩陣分解|矩阵分解|因子分解|分解",
    "linear_model_coefficients": r"linear|regression|coefficient|線性|线性|迴歸|回归|係數|系数",
    "signed_partial_regulatory_effects": r"\bsign(?:ed)?\b|activat|repress|inhibit|positive|negative|正負|正负|活化|抑制|促進|促进",
    "tfa": r"\bactiv(?:e|ity|ities)\b|活性|活躍|活跃",
    "joint_grn_tfa_inference": r"\bactiv(?:e|ity|ities)\b|活性|活躍|活跃",
    "tfa_covariate_regression": r"\bactiv(?:e|ity|ities)\b|活性|活躍|活跃",
    "lioness_base_compatibility": (r"\bLIONESS\b|base(?:line)?\s+network|per[- ]sample|sample[- ]specific|"
                                   r"each\s+(?:sample|patient|individual)|基礎網路|基础网络|每個樣本|每个样本|個體|个体"),
}


def load(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def blind_verdict(case, decision, reason_code):
    """score_blind.verdict applied to the final decision (as in Logs 290-300)."""
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


def unstated_acceptance(trace):
    """The discriminator was accepted with a witnessed tag no quote states."""
    events = [e for e in trace["events"] if e["type"].startswith("routing.semantic_discriminator_")]
    accepted = next((e["payload"] for e in events if e["type"].endswith("_accepted")), None)
    if not accepted:
        return False
    spans = collections.defaultdict(list)
    calls = [c for c in trace["calls"] if c.get("schema") == "SemanticDiscriminator"]
    args = ((calls[-1].get("raw_tool_calls") or [{}])[0].get("args") or {}) if calls else {}
    for item in args.get("evidence") or []:
        if isinstance(item, dict) and item.get("dimension") == "selection_tag":
            spans[item.get("value")].append(item.get("text_span") or "")
    for item in events:
        if item["type"].endswith("_recovered"):
            evidence = item["payload"].get("evidence") or {}
            spans[evidence.get("value")].append(evidence.get("text_span") or "")
    return any(
        tag in WITNESSES and not any(re.search(WITNESSES[tag], span, re.I) for span in spans.get(tag, []))
        for tag in accepted.get("selection_tags") or []
    )


def facts(row):
    trace = row["_trace"]
    decision = trace.get("decision") or {}
    matched = list(decision.get("matched_actions") or [])
    status = decision.get("capability_match_status")
    recommendation = decision.get("advisory_recommendation") or {}
    blind_key = row["id"].split("-")[0]
    single = (status in ("exact", "fallback") and len(matched) == 1 and matched[0] in TRIO) or (
        recommendation.get("action") in TRIO)
    return {
        "id": row["id"],
        "status": status,
        "reason": trace.get("reason_code"),
        "shown": matched or list(decision.get("hypothesis_actions") or []),
        "recommended": recommendation.get("action"),
        "exact": matched if status == "exact" else [],
        "single_trio_pick": single,
        "unstated_acceptance": unstated_acceptance(trace),
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
            + (" [UNSTATED]" if item["unstated_acceptance"] else "")
            for item in group
        )
        print(f"   {case:30s} {marks}")
    positives = [item for item in items if item["id"] in POSITIVES]
    blind = [item for item in items if item["blind"] is not None]
    result = {
        "trials": len(items),
        "provider_errors": sum(item["provider_error"] for item in items),
        "unstated_acceptances": sum(item["unstated_acceptance"] for item in items),
        "positive_trials": len(positives),
        "positive_single_picks": sum(item["single_trio_pick"] for item in positives),
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
        "validity (no provider errors in either arm)":
            candidate["provider_errors"] == 0 and baseline["provider_errors"] == 0,
        "sanity (candidate accepts no unstated method tag)": candidate["unstated_acceptances"] == 0,
        "positives (candidate single picks <= baseline)":
            candidate["positive_trials"] == 9 and candidate["positive_single_picks"] <= baseline["positive_single_picks"],
        **{f"control {case} exact {action} (>= baseline - 1)":
           candidate["controls_exact"][case] >= baseline["controls_exact"][case] - 1
           for case, action in CONTROLS.items()},
        "blind (candidate WRONG <= baseline + 3)": candidate["blind_wrong"] <= baseline["blind_wrong"] + 3,
    }
    print("== gates (MS1)")
    for name, ok in checks.items():
        print(f"   {'PASS' if ok else 'FAIL'}  {name}")
    print("   MS1 " + ("KEPT" if all(checks.values()) else "WITHDRAWN"))


def main():
    args = sys.argv[1:]
    split = args.index("--")
    candidate = summarize([Path(p) for p in args[:split]], "candidate")
    baseline = summarize([Path(p) for p in args[split + 1:]], "baseline")
    gates(candidate, baseline)


if __name__ == "__main__":
    main()
