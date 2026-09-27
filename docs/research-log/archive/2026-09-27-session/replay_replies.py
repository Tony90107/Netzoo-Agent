"""Render every recorded ambiguous decision's reply twice: patched-old vs current."""
import json, glob, os, sys, importlib
root = sys.argv[1]; sys.path.insert(0, root + "/scripts")
P = "/private/tmp/claude-501/-Users-chenzhonghan-Documents-LLM-AGENT/8f6660b9-a748-4022-87ea-7496f85a5ff5/scratchpad"
from pathlib import Path
from netzoo_agent_core.contracts import TaskDecision
from netzoo_agent_core.graph.input_inspection import advise_from_inspected_inputs
from netzoo_agent_core.policy import ProjectPolicyLoader
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification
policy = ProjectPolicyLoader(Path(root)).load()
cases = []
for f in sorted(glob.glob(P + "/trace*.json")):
    try: r = json.load(open(f))
    except Exception: continue
    for i, row in enumerate(r.get("results", [])):
        t = row.get("_trace") or {}; d = t.get("decision")
        if not d or d.get("capability_match_status") != "ambiguous": continue
        try: dec = TaskDecision.model_validate(d)
        except Exception: continue
        cases.append((f"{os.path.basename(f)}#{row.get('id')}#{i}", t.get("prompt") or row.get("prompt"), dec))
def render():
    out = {}
    for key, task, dec in cases:
        base = dec.model_copy(update={"advisory_recommendation": dec.advisory_recommendation, "inspected_directories": [], "discovered_inputs": []})
        a = advise_from_inspected_inputs(task, base, root=Path(root))
        try: out[key] = render_outcome_clarification(a, policy, task=task)
        except Exception as e: out[key] = "ERROR " + type(e).__name__ + " " + str(e)[:80]
    return out
new = render()
exec(open(sys.argv[2]).read())  # apply the "old" patch
old = render()
changed = [k for k in new if new[k] != old[k]]
print("ambiguous decisions", len(cases), "changed", len(changed), "errors new", sum(1 for v in new.values() if str(v).startswith("ERROR")), "errors old", sum(1 for v in old.values() if str(v).startswith("ERROR")))
for k in changed: print(" ", k)
json.dump({k: {"old": old[k], "new": new[k]} for k in changed}, open(sys.argv[3], "w"), indent=1, ensure_ascii=False)
