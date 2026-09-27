import json, sys
from collections import Counter
sys.path.insert(0, "/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts")
from pathlib import Path
from evaluate_routing import load_scenarios
EXP = {}
for f in ("routing_semantic_families.json", "routing_semantic_variants.json"):
    EXP.update({c.id: c.expected for c in load_scenarios(Path("/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/tests") / f)})
ONTO = {"terminal_goal_conflict", "artifact_granularity", "artifact_entity", "artifact_roles", "conflicting_evidence", "missing_current_input", "noncurrent_input"}
for f in sys.argv[1:]:
    tot = Counter()
    for r in json.load(open(f))["results"]:
        e = EXP[r["id"]]
        if r["status"] == "exact" and r["matched_actions"] and r["matched_actions"] != e.actions: tot["wrong_exact_route"] += 1
        rev = [x for x in r["_trace"]["calls"] if x["schema"] == "SemanticClaimRepair"]
        if not rev: continue
        d = json.loads(rev[0]["messages"][-1]["content"].split("\n", 1)[1])
        kinds = {i.split(".", 1)[-1].split(":")[0] for i in d["issues"]}
        g = "ontology" if kinds & ONTO else ("quote_only" if kinds <= {"ungrounded_evidence", "missing_evidence"} else "other")
        tot[g + "_reviews"] += 1; tot[g + "_validated"] += r["semantic_review_validated"]; tot[g + "_correct"] += r["semantic_review_correct"]
    print(f, dict(sorted(tot.items())))
