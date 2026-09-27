import json, sys
sys.path.insert(0, "/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts")
from netzoo_agent_core.contracts.semantic_claims import SemanticClaims, SemanticClaimRepair
from netzoo_agent_core.interpretation.stated_field_restoration import restore_stated_fields
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses
from netzoo_agent_core.routing.outcome_matching import match_semantic_request
d = json.load(open(sys.argv[1]))
for r in d["results"]:
    t = r["_trace"]
    if len(t["calls"]) < 2 or t["calls"][1]["schema"] != "SemanticClaimRepair":
        continue
    p = t["prompt"]
    first = t["calls"][0]["raw_tool_calls"]
    try:
        proposal = SemanticClaims.model_validate(first[0]["args"])
    except Exception as e:
        print(r["id"], r["trial"], "first-pass decode fail", type(e).__name__); continue
    rv = t["calls"][1]["raw_tool_calls"]
    tag = f"{r['id']} t{r['trial']}"
    if len(rv) != 1:
        print(tag, f"REVIEW: {len(rv)} tool calls -> semantic_payload ValueError (no decodable call)"); continue
    args = rv[0]["args"]
    idx = [x.get("hypothesis_index") for x in args.get("repairs", [])]
    try:
        repair = SemanticClaimRepair.model_validate(args)
    except Exception as e:
        print(tag, "REVIEW schema fail", str(e)[:300]); continue
    try:
        claims = repair.apply(proposal)
    except Exception as e:
        print(tag, f"REVIEW apply fail: {type(e).__name__}: {str(e)[:120]} repairs_idx={idx}")
        # what if we took only the first repair per index?
        seen=set(); dedup=[]
        for x in args["repairs"]:
            if x["hypothesis_index"] in seen: continue
            seen.add(x["hypothesis_index"]); dedup.append(x)
        try:
            c2 = SemanticClaimRepair.model_validate({**args, "repairs": dedup}).apply(proposal)
            i2, _ = restore_stated_fields(p, c2.to_internal(), restore_explicit_scalar_evidence=True)
            v2 = validate_outcome_hypotheses(p, i2.outcome_hypotheses)
            m2 = match_semantic_request(p, i2.outcome_hypotheses, request_mode=i2.request_mode)
            print("     first-per-index would give: valid=", v2.valid, v2.issues[:4], "match=", m2.status, m2.matched_actions)
        except Exception as e2:
            print("     first-per-index also fails:", type(e2).__name__, str(e2)[:200])
        # do all repairs for the same index agree?
        print("     duplicate repairs identical:", len({json.dumps(x, sort_keys=True) for x in args['repairs']}) == 1)
        continue
    same = claims == proposal
    interp, _ = restore_stated_fields(p, claims.to_internal(), restore_explicit_scalar_evidence=True)
    v = validate_outcome_hypotheses(p, interp.outcome_hypotheses)
    m = match_semantic_request(p, interp.outcome_hypotheses, request_mode=interp.request_mode)
    print(tag, f"REVIEW applied: noop={same} valid={v.valid} issues={list(v.issues)[:4]} match={m.status} {m.matched_actions} hyp={m.hypothesis_actions}")
    for s in v.evidence_shapes:
        pass
