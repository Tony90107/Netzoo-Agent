"""Log 196(b): re-validate every recorded first pass and accepted reading with and without the witness rule."""
import json, glob, os, sys
root = sys.argv[1]; sys.path.insert(0, root + "/scripts")
P = "/private/tmp/claude-501/-Users-chenzhonghan-Documents-LLM-AGENT/8f6660b9-a748-4022-87ea-7496f85a5ff5/scratchpad"
from netzoo_agent_core.contracts import TaskDecision
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation
from netzoo_agent_core.interpretation import request_integrity as ri
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses
from netzoo_agent_core.interpretation.stated_field_restoration import restore_stated_fields
items = []
for f in sorted(glob.glob(P + "/trace*.json")) + sorted(glob.glob(root + "/docs/research-log/live-semantic-trace-*.json")):
    try: d = json.load(open(f))
    except Exception: continue
    for i, r in enumerate(d.get("results", [])):
        t = r.get("_trace") or {}; task = t.get("prompt") or r.get("prompt")
        if not task: continue
        for c in t.get("calls", []):
            if c.get("schema") == "SemanticInterpretation" and c.get("parsed"):
                try: items.append((f"{os.path.basename(f)}#{r.get('id')}#{i}#first", task, SemanticInterpretation.model_validate(c["parsed"])))
                except Exception: pass
        for e in t.get("events", []):
            ri_ = (e.get("payload") or {}).get("rejected_interpretation")
            if ri_:
                try: items.append((f"{os.path.basename(f)}#{r.get('id')}#{i}#rejected{len(items)}", task, SemanticInterpretation.model_validate(ri_)))
                except Exception: pass
        if t.get("decision"):
            try:
                dec = TaskDecision.model_validate(t["decision"])
                if dec.outcome_hypotheses:
                    items.append((f"{os.path.basename(f)}#{r.get('id')}#{i}#accepted", task, SemanticInterpretation(request_mode="guidance", semantic_goal="g", outcome_hypotheses=dec.outcome_hypotheses)))
            except Exception: pass
def run():
    out = {}
    for key, task, interp in items:
        x, _ = restore_stated_fields(task, interp.model_copy(deep=True), align_artifact_constraints=False, restore_explicit_scalar_evidence=True)
        v = validate_outcome_hypotheses(task, [h.model_copy(deep=True) for h in x.outcome_hypotheses], x.request_mode)
        out[key] = (v.valid, sorted(v.issues))
    return out
new = run()
real = ri.granularity_mentions
ri.granularity_mentions = lambda task: ()   # old: the rule never fires (restoration keeps its own import)
old = run()
ri.granularity_mentions = real
flips = {k for k in new if new[k][0] != old[k][0]}
changed = {k for k in new if new[k] != old[k]}
print("interpretations", len(items), "issue sets changed", len(changed), "validity flips", len(flips))
for k in sorted(changed): print(" ", k, "old", old[k][0], "new", new[k][0], [x for x in new[k][1] if "granularity_contradicts" in x])
