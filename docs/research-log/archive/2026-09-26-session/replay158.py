import json, glob, os, sys
root=sys.argv[1]; S=sys.argv[2]; sys.path.insert(0, root+"/scripts")
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation
from netzoo_agent_core.interpretation.stated_field_restoration import restore_stated_fields
from netzoo_agent_core.routing.outcome_matching import match_semantic_request
try:
    from netzoo_agent_core.graph.partial_validity import valid_first_pass_subset
except ImportError:
    valid_first_pass_subset = None
total=rescued=0; rows=[]
for f in sorted(glob.glob(f"{S}/trace_*.json")):
    try: r=json.load(open(f))
    except Exception: continue
    for row in r.get("results",[]):
        t=row.get("_trace") or {}
        if t.get("reason_code")!="semantic_fallback": continue
        total+=1
        first=[c for c in t.get("calls",[]) if c["schema"]=="SemanticInterpretation"]
        if not first or not first[0].get("parsed"):
            rows.append((os.path.basename(f),row["id"],"first pass did not parse")); continue
        interp=SemanticInterpretation.model_validate(first[0]["parsed"])
        interp,_=restore_stated_fields(t["prompt"],interp,align_artifact_constraints=False,restore_explicit_scalar_evidence=True)
        sub=valid_first_pass_subset(t["prompt"],interp) if valid_first_pass_subset else None
        if sub is None:
            rows.append((os.path.basename(f),row["id"],f"no valid subset ({len(interp.outcome_hypotheses)} hyp)")); continue
        rescued+=1
        m=match_semantic_request(t["prompt"],sub.outcome_hypotheses,request_mode=sub.request_mode)
        rows.append((os.path.basename(f),row["id"],f"RESCUED {[(h.outcome.artifact_type,h.outcome.granularity) for h in sub.outcome_hypotheses]} -> {m.status} {m.matched_actions or m.hypothesis_actions}"))
for x in rows: print(*x)
print("fallbacks:",total,"rescued by first-pass subset:",rescued)
