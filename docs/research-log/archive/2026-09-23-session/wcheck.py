import json, sys
from collections import Counter
sys.path.insert(0, "/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts")
from pathlib import Path
from evaluate_routing import load_scenarios
T = Path("/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/tests")
E = {}
for f in ("routing_semantic_families.json", "routing_semantic_variants.json"):
    E.update({c.id: c.expected for c in load_scenarios(T / f)})
REG = {"regulatory_network", "signed_regulatory_effect_network", "regulatory_network_and_tf_activity"}
for tag in sys.argv[1:]:
    for contract in ("legacy", "claims"):
        c = Counter()
        for corpus in ("orig8", "fam32"):
            for r in json.load(open(f"{tag}-{corpus}-{contract}.json"))["results"]:
                e = E[r["id"]]
                if r["matched_actions"] and set(r["matched_actions"]) != set(e.actions):
                    c["wrong_exact" if r["status"] == "exact" else "wrong_fallback"] += 1
                if r["id"] == "gran-mirna-unstated-control" and r["matched_actions"]: c["W3_control_recommended"] += 1
                ev = json.dumps([x["payload"] for x in r["_trace"]["events"]])
                if "stated_roles_conflict" in ev:
                    c["roles_conflict_trials"] += 1
                    if e.artifact_type not in REG: c["W4_false_positive"] += 1
                if "undecided_granularity" in ev: c["undecided_trials"] += 1
        print(tag, contract, dict(c))
