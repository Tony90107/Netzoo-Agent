"""Re-render the verified guidance reply of every recorded exact/fallback guidance decision.

Usage: python docs/research-log/tools/replay_guidance.py <out.json> [<baseline.json>]

Every distinct recorded decision with `action == "no_tool"`, no execution and an
exact or fallback match goes through `guidance_contract` and
`render_verified_guidance`, as the response node does. Without a baseline the
replies are written as `{key: reply}`; with a baseline written earlier by this
script (e.g. on HEAD before a change), only the replies that changed are written
as `{key: {"old", "new"}}`. Used for Log 221.
"""
import hashlib
import json
import sys

from traces import ROOT, traced_rows

sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.interpretation.verified_guidance import (  # noqa: E402
    guidance_contract,
    render_verified_guidance,
)
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

policy = ProjectPolicyLoader(ROOT).load()
replies, seen = {}, set()
for path, index, row in traced_rows():
    trace = row["_trace"]; decision = trace.get("decision")
    if not decision or decision.get("action") != "no_tool" or decision.get("should_execute"):
        continue
    if decision.get("capability_match_status") not in {"exact", "fallback"}:
        continue
    task = trace.get("prompt") or row.get("prompt") or ""
    digest = hashlib.sha256(json.dumps([task, decision], sort_keys=True).encode()).hexdigest()[:16]
    if digest in seen:
        continue
    seen.add(digest)
    try:
        parsed = TaskDecision.model_validate(decision)
        reply = render_verified_guidance(parsed, guidance_contract(parsed, policy, task))
    except Exception as error:
        reply = f"ERROR {type(error).__name__} {str(error)[:80]}"
    replies[f"{digest}#{path.name}#{row.get('id')}#{index}"] = reply

if len(sys.argv) > 2:
    baseline = json.load(open(sys.argv[2]))
    written = {key: {"old": baseline.get(key), "new": value}
               for key, value in replies.items() if baseline.get(key) != value}
else:
    written = replies
open(sys.argv[1], "w").write(json.dumps(written, indent=1, ensure_ascii=False))
errors = sum(1 for value in replies.values() if str(value).startswith("ERROR"))
print("guidance decisions:", len(replies), "written:", len(written), "render errors:", errors)
