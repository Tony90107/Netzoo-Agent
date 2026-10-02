"""Re-render the deterministic reply of chosen traced trials (as score_blind.reply_for).

Needs the agent's runtime (langchain), so run it in the harness image:

  docker run --rm -v "$PWD:/work" -w /work -e PYTHONPATH=/work/scripts \
    netzoo_agent:latest python docs/research-log/method-signal-2026-10-02/render_replies.py \
    docs/research-log/method-signal-2026-10-02/live-ms-cand-s3-targeted.json.gz:ms-lung-generic

Each argument is `<report>:<case id>`. Log 303 quotes the replies this prints (run it from the tree whose reports it renders: the policy and code are that tree's).
"""
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts"))
from analyze import load  # noqa: E402
from langchain_core.messages import HumanMessage  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.graph.response import respond  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()


def reply_for(trace):
    decision = TaskDecision.model_validate(trace["decision"])
    task = trace.get("prompt", "")
    if decision.capability_match_status == "ambiguous":
        return render_outcome_clarification(decision, POLICY, task=task) or ""
    plan = WorkflowPlan(workflow="NO-TOOL", objective="render", decision=decision.model_dump(),
                        status="respond_only")
    state = {"messages": [HumanMessage(content=task)], "decision": decision.model_dump(),
             "plan": plan.model_dump(), "tool_results": []}
    return str(respond(SimpleNamespace(project_policy=POLICY, response_llm=None), state)["messages"][0].content)


for spec in sys.argv[1:]:
    path, case = spec.rsplit(":", 1)
    for row in load(path)["results"]:
        if row["id"] == case:
            status = row["_trace"]["decision"].get("capability_match_status")
            print(f"########## {Path(path).name} {case} [{status}]")
            print(reply_for(row["_trace"]))
            print()
