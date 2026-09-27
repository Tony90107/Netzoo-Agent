import json, sys
root=sys.argv[1]; S=sys.argv[2]; sys.path.insert(0, root+"/scripts")
from pathlib import Path
from netzoo_agent_core.contracts import TaskDecision
from netzoo_agent_core.policy import ProjectPolicyLoader
from netzoo_agent_core.interpretation.concept_answers import render_workflow_composition_guidance, render_outcome_clarification
policy=ProjectPolicyLoader(Path(root)).load()
def dec(f,i): return TaskDecision.model_validate(json.load(open(f"{S}/{f}"))["results"][i]["_trace"]["decision"])
out={
 "composition": render_workflow_composition_guidance(dec("trace_log160_live.json",1), policy, None),
 "inspected_formA": render_outcome_clarification(dec("trace_log160_live.json",0), policy),
 "condition_formA": render_outcome_clarification(dec("trace_log148_live.json",0), policy),
}
json.dump(out, open(sys.argv[3],"w"), indent=1)
