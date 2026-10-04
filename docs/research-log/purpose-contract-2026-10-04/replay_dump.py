"""Log 359 O3/O6: render every recorded decision with this tree's code and no study-purpose state.

Usage (any tree root): python3 <path>/replay_dump.py <out.json>
Writes {key: reply} for the 3,592 traced decisions (O3) and Log 343's 156 live
decisions (O6). Run it in the baseline worktree and in the candidate tree and
compare the two files: without the call's state, the candidate must reply as
the baseline does. Nothing calls a model.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "docs" / "research-log" / "tools"))
from langchain_core.messages import HumanMessage  # noqa: E402
from evaluate_routing import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.graph import response  # noqa: E402
from traces import traced_rows  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()


def reply(task, decision):
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task[:200], decision=decision.model_dump(), status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None}
    try:
        return str(response.respond(SimpleNamespace(project_policy=POLICY), state)["messages"][-1].content)
    except Exception as error:
        return f"<{type(error).__name__}>"


out = {}
for path, index, row in traced_rows():
    trace = row.get("_trace") or {}
    task = trace.get("prompt") or row.get("prompt")
    if task and trace.get("decision"):
        try:
            out[f"traced:{path.name}#{index}"] = reply(task, TaskDecision.model_validate(trace["decision"]))
        except Exception:
            pass
live = json.loads((ROOT / "docs/research-log/purpose-contract-2026-10-04/live/s1-decisions.json").read_text())
for key, item in live.items():
    out[f"live:{key}"] = reply(item["prompt"], TaskDecision.model_validate(item["decision"]))
Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False))
print(len(out), "replies")
