import json, sys
for f in sys.argv[1:]:
    n = ok = 0
    for r in json.load(open(f))["results"]:
        if not r["id"].startswith("hist-expression-then-mutation"): continue
        if any("terminal_goal_conflict" in str(e["payload"]) for e in r["_trace"]["events"]):
            n += 1; ok += (r["outcome"] or {}).get("artifact_type") == "sample_cluster_assignment"
            print("  ", r["id"], r["trial"], "final artifact:", (r["outcome"] or {}).get("artifact_type"), "passed" if r["passed"] else "FAIL")
    print(f, f"R4: {ok}/{n}")
