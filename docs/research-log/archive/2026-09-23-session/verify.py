import json, sys
from collections import Counter
REG = {"regulatory_network", "signed_regulatory_effect_network"}
def first_art(r):
    a = r["_trace"]["calls"][0].get("raw_tool_calls") or []
    if not a: return None
    h = (a[0]["args"].get("outcome_hypotheses") or [{}])[0].get("outcome", {})
    v = h.get("artifact_type"); return v["value"] if isinstance(v, dict) else v
for f in sys.argv[1:]:
    d = json.load(open(f)); c = Counter()
    for r in d["results"]:
        ev = r["_trace"]["events"]
        tgc = any("terminal_goal_conflict:sample_cluster_assignment" in str(e["payload"]) for e in ev)
        if r["id"] == "hist-hypothetical-control-en": c["V1_hypothetical_trials"] += 1; c["V1_conflict"] += tgc
        if r["id"].startswith("hist-expression-then-mutation") and first_art(r) not in (None, "sample_cluster_assignment"):
            c["V2_wrong_art_trials"] += 1; c["V2_missed"] += not tgc
        o = r["outcome"] or {}
        if o.get("artifact_type") in REG and "sample" in (o.get("entity_types") or []): c["V3_sample_left"] += 1
        fired = [x for e in ev for x in ((e["payload"].get("restored") or []) + (e["payload"].get("alignments") or [])) if isinstance(x, dict) and x.get("source") == "artifact_ontology" and x.get("value") == "sample"]
        if fired:
            c["F5_fired_trials"] += 1; c["F5_fired_" + r["language"]] += 1
            if o.get("artifact_type") == "regulatory_network_and_tf_activity": c["V4_tfa_sample_removed"] += 1
    print(f.split("/")[-1], dict(c))
