import json, glob, collections, sys, os
P="/private/tmp/claude-501/-Users-chenzhonghan-Documents-LLM-AGENT/8f6660b9-a748-4022-87ea-7496f85a5ff5/scratchpad"
files=sorted(glob.glob(P+"/trace*.json"))+sorted(glob.glob("docs/research-log/live-semantic-trace-*.json"))
kinds=collections.Counter(); only_missing=[]; total=0; seen=set()
for f in files:
    try: d=json.load(open(f))
    except Exception: continue
    for i,r in enumerate(d.get("results",[])):
        t=r.get("_trace") or {}
        if t.get("reason_code")!="semantic_fallback": continue
        total+=1
        fails=[e for e in t.get("events",[]) if e["type"]=="routing.semantic_interpreter_failed"]
        if not fails: kinds["no_failed_event"]+=1; continue
        issues=fails[-1]["payload"].get("validation_issues") or []
        issues=[x if isinstance(x,str) else json.dumps(x) for x in issues]
        cls=sorted({x.split(".",1)[-1].split(":",1)[0] for x in issues})
        kinds[tuple(cls)]+=1
        if cls==["missing_evidence"]:
            only_missing.append((os.path.basename(f), r.get("id"), i, [x.split(":",1)[1] for x in issues]))
print("fallbacks", total)
for k,v in kinds.most_common(): print(v, k)
print("--- only missing_evidence:")
for x in only_missing: print(x)
