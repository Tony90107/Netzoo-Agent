import json, sys
root=sys.argv[1]; sys.path.insert(0, root+"/scripts")
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation, SemanticPatch
from netzoo_agent_core.interpretation.semantic_patch import apply_semantic_patch
from netzoo_agent_core.interpretation.stated_field_restoration import restore_stated_fields
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses
from netzoo_agent_core.routing.outcome_matching import match_semantic_request
r=json.load(open(sys.argv[2])); row=r["results"][int(sys.argv[3])]; t=row["_trace"]
first=[c for c in t["calls"] if c["schema"]=="SemanticInterpretation"][0]["parsed"]
patch=[c for c in t["calls"] if c["schema"]=="SemanticPatch"][0]["parsed"]
permitted=[e for e in t["events"] if e["type"]=="routing.semantic_patch_applied"][0]["payload"]["permitted_fields"]
proposal=SemanticInterpretation.model_validate(first)
proposal,_=restore_stated_fields(t["prompt"],proposal,align_artifact_constraints=False,restore_explicit_scalar_evidence=True)
merged,_=apply_semantic_patch(proposal,SemanticPatch.model_validate(patch),permitted_fields=frozenset(permitted))
merged,_=restore_stated_fields(t["prompt"],merged,align_artifact_constraints=True,restore_explicit_scalar_evidence=True)
v=validate_outcome_hypotheses(t["prompt"],merged.outcome_hypotheses,merged.request_mode)
print("hyps:",[(h.outcome.artifact_type,h.outcome.granularity,h.outcome.regulator_types) for h in merged.outcome_hypotheses],"| valid:",v.valid,v.issues)
if v.valid:
    m=match_semantic_request(t["prompt"],merged.outcome_hypotheses,request_mode=merged.request_mode)
    print("match:",m.status,m.matched_actions,m.hypothesis_actions,"|",m.clarification_question)
