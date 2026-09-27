"""Log 198 criteria: L-b (veto), L-c (fabricated quotes on requested pairs), L-d (descriptive)."""
import json, sys, collections
BLIND_TOOL = {"case5-en": "run_puma", "case7-en": "run_dragon"}
AGGREGATE_TOOLS = {"run_puma", "run_panda"}
EXPECTED = {c["id"]: c["expected"] for c in json.load(open("/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/tests/routing_semantic_families.json"))}
lb1 = lb2 = lb3 = lb4 = lc = 0
d = collections.Counter()
for path in sys.argv[1:]:
    report = json.load(open(path))
    print(path.rsplit("/", 1)[-1], report["summary"]["passed"], "/", report["summary"]["trials"])
    for r in report["results"]:
        t = r["_trace"]; dec = t["decision"]; cid = r["id"]; events = t["events"]
        status = dec["capability_match_status"]; matched = dec.get("matched_actions") or []
        supplied = [e["payload"] for e in events if e["type"] == "routing.semantic_evidence_supplied"]
        calls = [c for c in t["calls"] if c["schema"] == "SemanticEvidenceSupply"]
        fails = [e["payload"] for e in events if e["type"] == "routing.semantic_interpreter_failed"]
        final_issues = [str(x) for x in ((fails[-1].get("validation_issues") or []) if fails else [])]
        unverified = [e for e in events if e["type"] == "routing.semantic_evidence_unverified"]
        if unverified: final_issues += [str(x) for x in unverified[-1]["payload"].get("issues") or []]
        if dec.get("should_execute"): lb1 += 1
        expected = {BLIND_TOOL[cid]} if cid in BLIND_TOOL else set((EXPECTED.get(cid) or {}).get("actions") or [])
        if supplied and status == "exact" and expected and not set(matched) <= expected:
            lb2 += 1; print("L-b(2)", cid, matched, expected)
        if cid == "role-both-ss-en" and status == "exact" and set(matched) & AGGREGATE_TOOLS:
            lb3 += 1; print("L-b(3)", cid, matched)
        for c in calls:
            if c.get("exception") or (c.get("parsing_error") and "BadRequest" in c["parsing_error"]):
                lb4 += 1; print("L-b(4)", cid, c.get("exception") or c.get("parsing_error"))
        if not supplied: continue
        requested = {x.split(".", 1)[1] for x in (supplied[0].get("requested") or supplied[0].get("required"))}
        fabricated = [x for x in final_issues if ".ungrounded_evidence:" in x and x.split(".ungrounded_evidence:", 1)[1] in requested]
        if fabricated: lc += 1; print("L-c", cid, fabricated)
        accepted = t["reason_code"] == "semantic_registry_intent" and not unverified
        d["triggered"] += 1; d["triggered_accepted"] += accepted
        d["sources:" + ",".join(map(str, supplied[0].get("sources") or ["-"]))] += 1
        if any(x.split("=", 1)[0] in ("artifact_type", "granularity") for x in requested):
            d["t2_triggered"] += 1; d["t2_accepted"] += accepted
            print("  T2", cid, sorted(requested), "->", t["reason_code"], status, matched or dec.get("hypothesis_actions"), "unverified" if unverified else "")
        if t["reason_code"] != "semantic_registry_intent" or unverified:
            print("  not accepted:", cid, t["reason_code"], final_issues[:4])
print(f"L-b(1)={lb1} L-b(2)={lb2} L-b(3)={lb3} L-b(4)={lb4} L-c={lc}")
for k, v in sorted(d.items()): print(f"  {k}: {v}")
