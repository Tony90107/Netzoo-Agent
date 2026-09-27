"""Log 186 replay: every recorded ambiguous decision through input inspection."""
import json, glob, os, sys
root=sys.argv[1]; S=sys.argv[2]; sys.path.insert(0, root+"/scripts")
from pathlib import Path
from netzoo_agent_core.contracts import TaskDecision
from netzoo_agent_core.graph.input_inspection import advise_from_inspected_inputs
out={}
files=sorted(glob.glob(f"{S}/trace*.json"))+sorted(glob.glob(f"{root}/docs/research-log/live-semantic-trace-*.json"))
for f in files:
    try: r=json.load(open(f))
    except Exception: continue
    for i,row in enumerate(r.get("results",[])):
        t=row.get("_trace") or {}; d=t.get("decision")
        if not d or d.get("capability_match_status")!="ambiguous": continue
        task=t.get("prompt") or row.get("prompt")
        try: dec=TaskDecision.model_validate(d)
        except Exception: continue
        dec=dec.model_copy(update={"advisory_recommendation":None,"inspected_directories":[]})
        a=advise_from_inspected_inputs(task,dec,root=Path(root))
        rec=a.advisory_recommendation
        out[f"{os.path.basename(f)}#{row.get('id')}#{i}"]=[rec.action if rec else None, sorted(a.inspected_directories or []), sorted(dec.hypothesis_actions)]
json.dump(out,open(sys.argv[3],"w"),indent=1,sort_keys=True); print("ambiguous decisions:",len(out))
