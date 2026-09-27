import json, glob, os, sys, inspect
root=sys.argv[1]; S=sys.argv[2]; sys.path.insert(0, root+"/scripts")
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation, SemanticPatch
from netzoo_agent_core.interpretation.semantic_patch import apply_semantic_patch
from netzoo_agent_core.interpretation.stated_field_restoration import restore_stated_fields
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses
takes_task = "user_task" in inspect.signature(apply_semantic_patch).parameters
out={}
for f in sorted(glob.glob(f"{S}/trace_*.json")):
    try: r=json.load(open(f))
    except Exception: continue
    for i,row in enumerate(r.get("results",[])):
        t=row.get("_trace") or {}
        first=[c for c in t.get("calls",[]) if c["schema"]=="SemanticInterpretation"]
        patch=[c for c in t.get("calls",[]) if c["schema"]=="SemanticPatch"]
        ev=[e for e in t.get("events",[]) if e["type"]=="routing.semantic_patch_applied"]
        if not first or not patch or not ev or not first[0].get("parsed") or not patch[0].get("parsed"): continue
        try:
            p=SemanticInterpretation.model_validate(first[0]["parsed"]); sp=SemanticPatch.model_validate(patch[0]["parsed"])
        except Exception: continue
        p,_=restore_stated_fields(t["prompt"],p,align_artifact_constraints=False,restore_explicit_scalar_evidence=True)
        kw={"permitted_fields":frozenset(ev[0]["payload"]["permitted_fields"])}
        if takes_task: kw["user_task"]=t["prompt"]
        try: m,ret=apply_semantic_patch(p,sp,**kw)
        except Exception as e: out[f"{os.path.basename(f)}#{i}"]=("error",str(e)[:60]); continue
        m,_=restore_stated_fields(t["prompt"],m,align_artifact_constraints=True,restore_explicit_scalar_evidence=True)
        v=validate_outcome_hypotheses(t["prompt"],[h.model_copy(deep=True) for h in m.outcome_hypotheses],m.request_mode)
        ignored=[x for x in ret if x.get("reason")=="withdrawal_of_asserted_value"]
        out[f"{os.path.basename(f)}#{i}"]=(v.valid, len(ignored), sorted(v.issues)[:3])
json.dump(out, open(sys.argv[3],"w"), indent=1)
print("patches replayed:", len(out))
