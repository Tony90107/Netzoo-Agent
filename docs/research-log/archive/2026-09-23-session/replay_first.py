import json, sys
from collections import Counter
sys.path.insert(0, "/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts")
from netzoo_agent_core.contracts.semantic_claims import SemanticClaims
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation
from netzoo_agent_core.interpretation.stated_field_restoration import restore_stated_fields
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses
from netzoo_agent_core.routing.outcome_matching import match_semantic_request
for f in sys.argv[1:]:
    d = json.load(open(f)); tally = Counter(); per = Counter()
    for r in d["results"]:
        t = r["_trace"]; p = t["prompt"]; exp = r["id"]
        a = t["calls"][0]["raw_tool_calls"][0]["args"]
        si = (SemanticClaims.model_validate(a).to_internal() if t["calls"][0]["schema"] == "SemanticClaims"
              else SemanticInterpretation.model_validate(a))
        si, _ = restore_stated_fields(p, si, restore_explicit_scalar_evidence=True)
        v = validate_outcome_hypotheses(p, si.outcome_hypotheses)
        if not v.valid:
            kind = "rejected:" + ",".join(sorted({i.split('.',1)[1].split(':')[0] for i in v.issues}))
        else:
            m = match_semantic_request(p, si.outcome_hypotheses, request_mode=si.request_mode)
            want = "run_puma" if "cohort" in exp else "run_lioness_puma"
            inp = [x for h in si.outcome_hypotheses for x in h.outcome.input_artifacts]
            kind = f"valid:{m.status}:{'OK' if m.matched_actions == [want] else m.matched_actions}" + (f":inputs={inp}" if inp else "")
        tally[kind] += 1; per[(exp, kind)] += 1
    print("==", f, dict(tally))
    for k, n in sorted(per.items()): print("   ", k, n)
