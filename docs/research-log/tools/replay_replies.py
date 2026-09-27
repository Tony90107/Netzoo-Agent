"""Re-render the reply of every recorded ambiguous decision, optionally against an older rule.

Usage: python docs/research-log/tools/replay_replies.py <out.json> [<old_patch.py>]

Each recorded ambiguous decision goes through the folder inspection and
`render_outcome_clarification`, as the response node does. With an
`old_patch.py` (Python executed in-process, e.g. restoring a helper to its
previous behaviour), the replies are rendered twice and only the decisions
whose reply changed are written. Used for Logs 193-195.
"""
import json
import sys

from traces import ROOT, traced_rows

sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.graph.input_inspection import advise_from_inspected_inputs  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

policy = ProjectPolicyLoader(ROOT).load()
cases = []
for path, index, row in traced_rows():
    trace = row["_trace"]; decision = trace.get("decision")
    if not decision or decision.get("capability_match_status") != "ambiguous":
        continue
    try:
        cases.append((f"{path.name}#{row.get('id')}#{index}", trace.get("prompt") or row.get("prompt"),
                      TaskDecision.model_validate(decision)))
    except Exception:
        continue


def render():
    replies = {}
    for key, task, decision in cases:
        base = decision.model_copy(update={"inspected_directories": [], "discovered_inputs": []})
        advised = advise_from_inspected_inputs(task, base, root=ROOT)
        try:
            replies[key] = render_outcome_clarification(advised, policy, task=task)
        except Exception as error:
            replies[key] = f"ERROR {type(error).__name__} {str(error)[:80]}"
    return replies


new = render()
if len(sys.argv) > 2:
    exec(open(sys.argv[2]).read())
    old = render()
    changed = {key: {"old": old[key], "new": new[key]} for key in new if old[key] != new[key]}
else:
    changed = {key: {"new": value} for key, value in new.items()}
open(sys.argv[1], "w").write(json.dumps(changed, indent=1, ensure_ascii=False))
errors = sum(1 for value in new.values() if str(value).startswith("ERROR"))
print("ambiguous decisions:", len(cases), "written:", len(changed), "render errors:", errors)
