"""Pre-registered analysis for Log 306 (WT1: first-pass method tags; WT2: miRNA scope of a preference).

Written before any code change or live trial.
Usage: python analyze.py <candidate report> ... -- <baseline report> ...

Grades the FINAL decision of every traced trial (JSON or .json.gz); pure JSON.

WT1 (each gate fails -> withdraw WT1):
- sanity: candidate trials ending exact `registry_features` without a discriminator
  acceptance, where a witnessed tag of the final reading has no quote stating it = 0.
- compute prompts (t1-otter, wt-compute-laptop, wt-compute-runtime): candidate exact
  PANDA <= baseline exact PANDA.
- controls, exact >= baseline - 1: gran-tf-agg-relaxed-en (OTTER),
  ms-ctl-message-passing (PANDA), ms-ctl-factorization (GIRAFFE).
WT2 (each gate fails -> withdraw WT2):
- sanity: candidate trials recommending PUMA or LIONESS-PUMA although the request
  has no regulator_class evidence word = 0 (all trials, blind included).
- controls: mirna-degradation-en recommends PUMA >= baseline - 1; blind case5-en
  OK >= baseline - 1.
Blind: candidate blind-en final WRONG <= baseline + 3, else withdraw both.
"""
import collections
import gzip
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLIND = json.loads((HERE.parent / "blind" / "expectations.json").read_text(encoding="utf-8"))
COMPUTE = {"t1-otter", "wt-compute-laptop", "wt-compute-runtime"}
WT1_CONTROLS = {
    "gran-tf-agg-relaxed-en": "run_otter",
    "ms-ctl-message-passing": "run_panda",
    "ms-ctl-factorization": "run_giraffe",
}
MIRNA_ACTIONS = {"run_puma", "run_lioness_puma"}
# Copied from the registry as pre-declared in Log 306 (independent of either arm's code).
REGULATOR_WITNESS = (
    r"\bmi(?:cro)?[- ]?rnas?\b|\bmir[- ]?\d|non[- ]?coding|\bnc[- ]?rnas?\b|"
    r"\bsmall\s+(?:[\w-]+\s+)?rnas?\b|post[- ]?transcription|"
    r"微小核糖核酸|微型\s*RNA|小\s*RNA|非編碼|轉錄後"
)
TF_ACTIVITY = r"\bactiv(?:e|ity|ities)\b|活性|活躍|活跃"
TAG_WITNESSES = {
    "message_passing": r"message[- ]?passing|pass(?:es|ing)?\s+messages|iterat|訊息傳遞|消息傳遞|消息传递|信息傳遞|信息传递|迭代",
    "relaxed_graph_matching": (r"graph[- ]?matching|objective|loss|optimi[sz]|gradient|converge|convex|heuristic|"
                               r"圖匹配|图匹配|目標|目标|損失|损失|最佳化|最優化|优化|梯度|收斂|收敛|凸|啟發式|启发式"),
    # Synced with the registry in the Log 306 supplement (verb form added before live).
    "biologically_informed_matrix_factorization": (r"factori[sz]|(?<!transcription\s)\bfactor(?:s|ed|ing)?\s+(?:the\s+)?"
                                                   r"(?:gene\s+)?expression|decompos|矩陣分解|矩阵分解|因子分解|分解"),
    "linear_model_coefficients": r"linear|regression|coefficient|線性|线性|迴歸|回归|係數|系数",
    "signed_partial_regulatory_effects": r"\bsign(?:ed)?\b|activat|repress|inhibit|positive|negative|正負|正负|活化|抑制|促進|促进",
    "tfa": TF_ACTIVITY, "joint_grn_tfa_inference": TF_ACTIVITY, "tfa_covariate_regression": TF_ACTIVITY,
    "lioness_base_compatibility": (r"\bLIONESS\b|base(?:line)?\s+network|per[- ]sample|sample[- ]specific|"
                                   r"each\s+(?:sample|patient|individual)|基礎網路|基础网络|每個樣本|每个样本|個體|个体"),
}


def load(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def blind_verdict(case, decision, reason_code):
    """score_blind.verdict applied to the final decision (as in Logs 290-304)."""
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


def unstated_first_pass_pick(trace):
    decision = trace.get("decision") or {}
    if decision.get("match_basis") != "registry_features" or decision.get("capability_match_status") != "exact":
        return False
    if any(e["type"].endswith("discriminator_accepted") for e in trace["events"]):
        return False
    for reading in decision.get("outcome_hypotheses") or []:
        for tag in set(reading["outcome"].get("selection_tags") or []) & set(TAG_WITNESSES):
            spans = [e.get("text_span") or "" for e in reading.get("evidence", [])
                     if e.get("dimension") == "selection_tag" and e.get("value") == tag]
            if not any(re.search(TAG_WITNESSES[tag], span, re.I) for span in spans):
                return True
    return False


def facts(row):
    trace = row["_trace"]
    decision = trace.get("decision") or {}
    matched = list(decision.get("matched_actions") or [])
    status = decision.get("capability_match_status")
    recommendation = decision.get("advisory_recommendation") or {}
    blind_key = row["id"].split("-")[0]
    return {
        "id": row["id"],
        "status": status,
        "reason": trace.get("reason_code"),
        "shown": matched or list(decision.get("hypothesis_actions") or []),
        "recommended": recommendation.get("action"),
        "exact": matched if status == "exact" else [],
        "unstated_first_pass_pick": unstated_first_pass_pick(trace),
        "unfounded_mirna": recommendation.get("action") in MIRNA_ACTIONS
                           and not re.search(REGULATOR_WITNESS, trace.get("prompt", ""), re.I),
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
            + (" [UNSTATED-TAG]" if item["unstated_first_pass_pick"] else "")
            + (" [UNFOUNDED-MIRNA]" if item["unfounded_mirna"] else "")
            for item in group
        )
        print(f"   {case:30s} {marks}")
    blind = [item for item in items if item["blind"] is not None]
    result = {
        "trials": len(items),
        "provider_errors": sum(item["provider_error"] for item in items),
        "unstated_first_pass_picks": sum(item["unstated_first_pass_pick"] for item in items),
        "compute_trials": sum(item["id"] in COMPUTE for item in items),
        "compute_exact_panda": sum(item["id"] in COMPUTE and item["exact"] == ["run_panda"] for item in items),
        "wt1_controls": {case: sum(item["exact"] == [action] for item in by_case.get(case, []))
                         for case, action in WT1_CONTROLS.items()},
        "unfounded_mirna": sum(item["unfounded_mirna"] for item in items),
        "mirna_degradation_puma": sum(item["recommended"] == "run_puma" for item in by_case.get("mirna-degradation-en", [])),
        "case5_ok": sum(item["blind"] == "OK" for item in by_case.get("case5-en", [])),
        "blind_trials": len(blind),
        "blind_wrong": sum(item["blind"] == "WRONG" for item in blind),
        "blind_verdicts": dict(collections.Counter(item["blind"] for item in blind)),
    }
    print("   " + json.dumps(result))
    return result


def gates(candidate, baseline):
    validity = candidate["provider_errors"] == 0 and baseline["provider_errors"] == 0
    blind = candidate["blind_wrong"] <= baseline["blind_wrong"] + 3
    wt1 = {
        "sanity (no unstated first-pass tag decides a tie)": candidate["unstated_first_pass_picks"] == 0,
        "compute prompts (candidate exact PANDA <= baseline)":
            candidate["compute_trials"] == 9 and candidate["compute_exact_panda"] <= baseline["compute_exact_panda"],
        **{f"control {case} exact {action} (>= baseline - 1)":
           candidate["wt1_controls"][case] >= baseline["wt1_controls"][case] - 1
           for case, action in WT1_CONTROLS.items()},
    }
    wt2 = {
        "sanity (no miRNA workflow recommended without miRNA words)": candidate["unfounded_mirna"] == 0,
        "mirna-degradation-en recommends PUMA (>= baseline - 1)":
            candidate["mirna_degradation_puma"] >= baseline["mirna_degradation_puma"] - 1,
        "blind case5-en OK (>= baseline - 1)": candidate["case5_ok"] >= baseline["case5_ok"] - 1,
    }
    print(f"== validity (no provider errors): {'PASS' if validity else 'FAIL -> void and rerun'}")
    print(f"== blind (candidate WRONG <= baseline + 3): {'PASS' if blind else 'FAIL -> withdraw WT1 and WT2'}")
    for name, checks in (("WT1", wt1), ("WT2", wt2)):
        print(f"== gates ({name})")
        for label, ok in checks.items():
            print(f"   {'PASS' if ok else 'FAIL'}  {label}")
        print(f"   {name} " + ("KEPT" if validity and blind and all(checks.values()) else "WITHDRAWN"))


def main():
    args = sys.argv[1:]
    split = args.index("--")
    candidate = summarize([Path(p) for p in args[:split]], "candidate")
    baseline = summarize([Path(p) for p in args[split + 1:]], "baseline")
    gates(candidate, baseline)


if __name__ == "__main__":
    main()
