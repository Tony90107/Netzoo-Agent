"""Log 182 replay: re-validate every recorded semantic_fallback, with partial validity and matching."""
import json, glob, os, sys
root=sys.argv[1]; S=sys.argv[2]; sys.path.insert(0, root+"/scripts")
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation
from netzoo_agent_core.interpretation.stated_field_restoration import restore_stated_fields
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses
from netzoo_agent_core.graph.partial_validity import _valid_subset
from netzoo_agent_core.routing.outcome_matching import match_semantic_request
out={}
files=sorted(glob.glob(f"{S}/trace*.json"))+sorted(glob.glob(f"{root}/docs/research-log/live-semantic-trace-*.json"))
for f in files:
    try: r=json.load(open(f))
    except Exception: continue
    for i,row in enumerate(r.get("results",[])):
        t=row.get("_trace") or {}
        if t.get("reason_code")!="semantic_fallback": continue
        fail=[e for e in t.get("events",[]) if e["type"]=="routing.semantic_interpreter_failed"]
        ri=fail and fail[-1]["payload"].get("rejected_interpretation")
        if not ri: continue
        task=t.get("prompt") or row.get("prompt")
        try: interp=SemanticInterpretation.model_validate(ri)
        except Exception: continue
        interp,_=restore_stated_fields(task,interp,align_artifact_constraints=True,restore_explicit_scalar_evidence=True)
        v=validate_outcome_hypotheses(task,[h.model_copy(deep=True) for h in interp.outcome_hypotheses],interp.request_mode)
        hyps=None
        if v.valid: hyps=interp.outcome_hypotheses
        elif len(interp.outcome_hypotheses)>=2:
            kept,dropped=_valid_subset(task,interp)
            if kept and dropped and validate_outcome_hypotheses(task,[h.model_copy(deep=True) for h in kept],interp.request_mode).valid:
                hyps=kept
        m=None
        if hyps is not None:
            hs=[h.model_copy(deep=True) for h in hyps]
            validate_outcome_hypotheses(task,hs,interp.request_mode)
            mm=match_semantic_request(task,hs,request_mode=interp.request_mode)
            m=[mm.status,mm.matched_actions,mm.hypothesis_actions]
        out[f"{os.path.basename(f)}#{row.get('id')}#{i}"]=[hyps is not None, sorted(v.issues), m]
json.dump(out,open(sys.argv[3],"w"),indent=1,sort_keys=True); print("fallbacks with an interpretation:", len(out), "rescued:", sum(1 for x in out.values() if x[0]))
