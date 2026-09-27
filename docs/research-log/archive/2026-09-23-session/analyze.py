import json, sys
from collections import Counter, defaultdict
GQ = "Should the result be aggregate or sample-specific?"
def load(p): return json.load(open(p))
def structural(d):
    s = Counter()
    for r in d["results"]:
        t = r["_trace"]
        first = t["calls"][0]
        fa = (first.get("raw_tool_calls") or [{}])[0].get("args") or {}
        fh = (fa.get("outcome_hypotheses") or [{}])
        fgran = [(h.get("outcome") or {}).get("granularity") for h in fh]
        fgran = [g["value"] if isinstance(g, dict) else g for g in fgran]
        for c in t["calls"]:
            if c["schema"] in ("SemanticClaimRepair", "SemanticPatch", "SemanticReview", "SemanticClaims") and c is not first:
                if c["schema"] == "IntentDecision": continue
                s["review_calls"] += 1
                u = c.get("usage") or {}
                if u.get("output_tokens") == 1200: s["S2_truncated_1200"] += 1
                if c["schema"] == "SemanticClaimRepair":
                    for tc in c.get("raw_tool_calls") or []:
                        a = tc.get("args") or {}
                        if "repairs" in a: s["S1_list_shape"] += 1
                        idx = a.get("hypothesis_index")
                        if isinstance(idx, int) and idx >= len(fh): s["S1_out_of_range"] += 1
                    if not c.get("raw_tool_calls"): s["review_no_tool_call"] += 1
        q = (r.get("next_step") or {}).get("question") or ""
        dq = r.get("_trace", {}).get("decision", {}).get("clarification_question") or ""
        if "aggregate" in fgran and (GQ in q or GQ in dq): s["S3_agg_first_pass_then_gran_question"] += 1
        if "aggregate" in fgran: s["first_pass_aggregate"] += 1
    return dict(s)
def fam(i): return i.split("-")[0] if i.split("-")[0] in ("gran","hist","role","zh") else "orig8"
def summary(tag, d):
    s = d["summary"]
    print(f"== {tag}: passed {s['passed']}/{s['trials']} route {round(s['route_pass_rate']*s['trials'])} sem {round(s['semantic_pass_rate']*s['trials'])} calls {s['provider_calls']} "
          f"review {s.get('semantic_review_attempts')} valid {s.get('semantic_review_validation_rate')} success {s.get('semantic_review_success_rate')} "
          f"repair_att {s['review_repair_attempts']} ungrounded {s['ungrounded_evidence_shapes']} clusters {s['ungrounded_evidence_clusters']} unsafe {s['unsafe_execution_count']} "
          f"every_repeat {s['prompts_passed_every_repeat']}/{s['unique_prompts']}")
    print("   structural:", structural(d))
    by = defaultdict(lambda: [0, 0, 0, 0])
    for r in d["results"]:
        b = by[fam(r["id"])]; b[0] += r["passed"]; b[1] += r["route_passed"]; b[2] += r["semantic_passed"]; b[3] += 1
    print("   by family (pass/route/sem of n):", {k: tuple(v) for k, v in sorted(by.items())})
def paired(a, b):
    pa, pb = defaultdict(int), defaultdict(int)
    for r in a["results"]: pa[r["id"]] += r["passed"]
    for r in b["results"]: pb[r["id"]] += r["passed"]
    w = sum(pb[k] > pa[k] for k in pa); l = sum(pb[k] < pa[k] for k in pa); t = len(pa) - w - l
    print(f"   paired per prompt (claims vs legacy): claims better {w}, worse {l}, tie {t}")
    for k in pa: print(f"     {k:36s} legacy {pa[k]}/3 claims {pb[k]}/3")
if __name__ == "__main__":
    L, C = load(sys.argv[1]), load(sys.argv[2])
    summary("legacy", L); summary("claims", C); paired(L, C)
