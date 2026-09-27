import json, sys
root = sys.argv[1]; sys.path.insert(0, root + "/scripts")
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation
from netzoo_agent_core.interpretation.stated_field_restoration import restore_stated_fields
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses
S = sys.argv[2]; out = []
for f in ("trace_log141_live.json", "trace_log141_live_extra.json", "trace_log139_live.json"):
    r = json.load(open(f"{S}/{f}"))
    for i, row in enumerate(r["results"]):
        t = row["_trace"]
        if t.get("reason_code") != "semantic_fallback":
            continue
        fail = [e for e in t["events"] if e["type"] == "routing.semantic_interpreter_failed"][0]["payload"]
        ri = fail.get("rejected_interpretation")
        if not ri:
            out.append((f, row["id"], i, "no_interpretation", fail.get("error_type"))); continue
        interp = SemanticInterpretation.model_validate(ri)
        interp, _ = restore_stated_fields(t["prompt"], interp, align_artifact_constraints=True, restore_explicit_scalar_evidence=True)
        v = validate_outcome_hypotheses(t["prompt"], interp.outcome_hypotheses)
        out.append((f, row["id"], i, "valid" if v.valid else "rejected", list(v.issues)))
for o in out: print(json.dumps(o, ensure_ascii=False))
print("VALID", sum(o[3] == "valid" for o in out), "of", len(out))
