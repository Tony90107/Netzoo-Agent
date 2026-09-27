"""Log 188 replay: recorded ambiguous decisions -> rematch divergent question, inspect, render."""
import json, glob, os, sys
root=sys.argv[1]; S=sys.argv[2]; sys.path.insert(0, root+"/scripts")
from pathlib import Path
from netzoo_agent_core.contracts import TaskDecision
from netzoo_agent_core.graph.input_inspection import advise_from_inspected_inputs
from netzoo_agent_core.policy import ProjectPolicyLoader
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification
from netzoo_agent_core.routing.outcome_matching import match_outcome_hypotheses
policy=ProjectPolicyLoader(Path(root)).load()
out={}
files=sorted(glob.glob(f"{S}/trace*.json"))
for f in files:
    try: r=json.load(open(f))
    except Exception: continue
    for i,row in enumerate(r.get("results",[])):
        t=row.get("_trace") or {}; d=t.get("decision")
        if not d or d.get("capability_match_status")!="ambiguous": continue
        task=t.get("prompt") or row.get("prompt")
        try: dec=TaskDecision.model_validate(d)
        except Exception: continue
        m=match_outcome_hypotheses([h.model_copy(deep=True) for h in dec.outcome_hypotheses])
        dec=dec.model_copy(update={"advisory_recommendation":None,"inspected_directories":[]})
        a=advise_from_inspected_inputs(task,dec,root=Path(root))
        try: text=render_outcome_clarification(a,policy,task=task)
        except Exception as e: text="ERROR "+type(e).__name__+" "+str(e)[:100]
        out[f"{os.path.basename(f)}#{row.get('id')}#{i}"]={"q":m.clarification_question,"text":text,"rec":a.advisory_recommendation.action if a.advisory_recommendation else None}
json.dump(out,open(sys.argv[3],"w"),indent=1,sort_keys=True); print("ambiguous decisions:",len(out))
