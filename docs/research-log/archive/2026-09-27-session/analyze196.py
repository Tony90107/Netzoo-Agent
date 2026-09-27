"""Log 196 criteria over traced reports: K-b (veto), K-c (veto for the witness rule), K-d (descriptive)."""
import json, sys, collections
BLIND_TOOL = {"case5-en": "run_puma", "case7-en": "run_dragon"}
AGGREGATE_TOOLS = {"run_puma", "run_panda"}
rows = []
for path in sys.argv[1:]:
    for r in json.load(open(path))["results"]:
        rows.append(r)
kb1 = kb2 = kb3 = kc = 0
d = collections.Counter(); per_case = collections.defaultdict(list)
for r in rows:
    t = r["_trace"]; dec = t["decision"]; exp = r.get("expected") or {}
    cid = r["id"]; events = t["events"]
    status = dec["capability_match_status"]; matched = dec.get("matched_actions") or []
    supplied = [e["payload"] for e in events if e["type"] == "routing.semantic_evidence_supplied"]
    folded = [p for p in supplied if p.get("folded")]
    fails = [e["payload"] for e in events if e["type"] in ("routing.semantic_interpreter_failed",)]
    final_issues = (fails[-1].get("validation_issues") or []) if fails else []
    first_rej = [e["payload"] for e in events if e["type"] == "routing.semantic_interpretation_rejected" and e["payload"].get("attempt") == 1]
    if dec.get("should_execute"): kb1 += 1
    expected_tools = {BLIND_TOOL[cid]} if cid in BLIND_TOOL else set(exp.get("actions") or [])
    expected_status = "exact" if cid in BLIND_TOOL else exp.get("status")
    if folded and status == "exact" and (not set(matched) <= expected_tools):
        kb2 += 1; print("K-b(2) VIOLATION", cid, matched, expected_tools)
    if cid == "role-both-ss-en" and ((status == "exact" and set(matched) & AGGREGATE_TOOLS) or (dec.get("hypothesis_actions") and set(dec["hypothesis_actions"]) <= AGGREGATE_TOOLS)):
        kb3 += 1; print("K-b(3) VIOLATION", cid, status, matched, dec.get("hypothesis_actions"))
    exp_gran = exp.get("granularity")
    for issue in final_issues:
        if "granularity_contradicts_request:" in str(issue) and exp_gran and str(issue).endswith(":" + exp_gran):
            kc += 1; print("K-c VIOLATION", cid, issue)
    for p in first_rej:
        for issue in p.get("issues") or []:
            if "granularity_contradicts_request" in str(issue): d["first_pass_witness_issue"] += 1
    d["trials"] += 1
    d["supply_triggered"] += bool(supplied)
    d["supply_folded"] += bool(folded)
    if supplied: d["supply_then_" + t["reason_code"]] += 1
    if folded: d["folded_then_" + t["reason_code"] + "_" + status if status else "folded_then_" + t["reason_code"]] += 1
    if t["reason_code"] == "semantic_fallback":
        kinds = sorted({str(x).split(".", 1)[-1].split(":", 1)[0] for x in final_issues})
        d["fallback:" + ",".join(kinds)] += 1
    ok = (status == "exact" and set(matched) <= expected_tools and matched) if expected_status == "exact" else (status == expected_status)
    per_case[cid].append(("ok" if ok else "x") + ("*" if folded else "") + f"[{status}:{','.join(matched or dec.get('hypothesis_actions') or [])}]")
print("K-b(1) should_execute:", kb1, "| K-b(2) folded wrong exact:", kb2, "| K-b(3) role-both-ss aggregate:", kb3, "| K-c:", kc)
for k, v in sorted(d.items()): print(f"  {k}: {v}")
for cid, v in sorted(per_case.items()): print(f"  {cid}: {' '.join(v)}")
