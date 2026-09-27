import json, hashlib, sys
from pathlib import Path
tag, label = sys.argv[1], sys.argv[2]
out = Path("/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/docs/research-log")
for corpus, name in (("orig8", "orig8"), ("fam32", "families32")):
    for c in ("legacy", "claims"):
        d = json.load(open(f"{tag}-{corpus}-{c}.json"))
        for r in d["results"]:
            for call in r["_trace"]["calls"]:
                for m in call["messages"]:
                    if m["type"] == "SystemMessage":
                        m["content_sha256"] = hashlib.sha256(m.pop("content").encode()).hexdigest()
        d["metadata"]["capture"] = f"trace harness; {label}"
        (out / f"live-semantic-trace-2026-09-23-{tag.replace('v','round')}-{name}-{c}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1))
print("saved", tag)
