import json, glob, os, sys
root=sys.argv[1]; S=sys.argv[2]; sys.path.insert(0, root+"/scripts")
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation
from netzoo_agent_core.interpretation.stated_field_restoration import restore_stated_fields
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses
out={}
for f in sorted(glob.glob(f"{S}/trace_*.json")):
    try: r=json.load(open(f))
    except Exception: continue
    for i,row in enumerate(r.get("results",[])):
        t=row.get("_trace") or {}
        if t.get("reason_code")!="semantic_fallback": continue
        fail=[e for e in t.get("events",[]) if e["type"]=="routing.semantic_interpreter_failed"]
        ri=fail and fail[0]["payload"].get("rejected_interpretation")
        if not ri: continue
        interp=SemanticInterpretation.model_validate(ri)
        interp,_=restore_stated_fields(t["prompt"],interp,align_artifact_constraints=True,restore_explicit_scalar_evidence=True)
        v=validate_outcome_hypotheses(t["prompt"],[h.model_copy(deep=True) for h in interp.outcome_hypotheses],interp.request_mode)
        out[f"{os.path.basename(f)}#{i}"]=(v.valid, sorted(v.issues))
json.dump(out,open(sys.argv[3],"w"),indent=1); print("fallbacks with an interpretation:", len(out))
