"""Log 381 prep: replay Log 380's recorded candidate sessions with the redo (SEEN data, calibration only).

Usage (repository root): python3 docs/research-log/applicability-redo-2026-10-06/ar_dev.py
For each candidate session of Log 380 (live/s20-decisions.json) with a data-facts proposal, the
proposal is re-verified by the current code and routing's applicability step re-run on the recorded
decision (the call patched to return it); the reply is re-rendered with the recorded study purpose
and measured as Log 380's analyzer measures it. No model is called.
"""
import json
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "scripts")]
from langchain_core.messages import HumanMessage  # noqa: E402
from netzoo_agent_core.contracts import LLMUsage, TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.contracts.data_facts import DataFactsProposal  # noqa: E402
from netzoo_agent_core.graph import response, router_invocation  # noqa: E402
from netzoo_agent_core.graph.data_facts_call import verify_data_facts  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

sys.path.insert(0, str(ROOT / "docs/research-log/applicability-2026-10-06"))
import ap_analyze as A  # noqa: E402  (measure(), questions(): Log 380's own definitions)

POLICY = ProjectPolicyLoader(ROOT).load()
ROWS = json.loads((ROOT / "docs/research-log/applicability-2026-10-06/live/s20-decisions.json").read_text())


def replay(row):
    decision = TaskDecision.model_validate(row["decision"])
    event = row.get("data_facts_event")
    if event and event.get("proposal"):
        facts, _ = verify_data_facts(row["prompt"], DataFactsProposal.model_validate(event["proposal"]))
        base = decision.model_copy(update={"data_facts": None, "applicability": []})
        result = router_invocation._RouterInvocation(decision=base, routing_state={}, usage=LLMUsage(budget_tokens=10**6),
                                                     budget_warnings=[], reason_code="replay")
        with patch.object(router_invocation, "invoke_data_facts", return_value=(facts, result.usage, [])):
            decision = router_invocation._with_applicability(
                SimpleNamespace(recorder=SimpleNamespace(append=lambda *a: None)), {}, row["prompt"], result).decision
    plan = WorkflowPlan(workflow="NO-TOOL", objective=row["prompt"][:200], decision=decision.model_dump(), status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=row["prompt"])],
             "tool_results": [], "evaluation": None, "study_purpose": row["study_purpose"]}
    out = response.respond(SimpleNamespace(project_policy=POLICY), state)
    return {"decision": decision.model_dump(), "reply": str(out["messages"][-1].content), "roles": row["roles"]}


def main():
    counts, notes = Counter(), []
    for key, row in ROWS.items():
        arm, item_id, rep = key.split("-")
        if arm != "cand" or "response" in row["roles"]:
            continue
        item = A.ITEMS[item_id]
        before, after = A.measure(row), A.measure(replay(row))
        for name in ("asks_priors", "says_ruled_out"):
            counts[(name, item["priors_label"], item["data_question"], before[name], after[name])] += 1
        if before["asks_priors"] != after["asks_priors"] or before["offered"] != after["offered"]:
            notes.append(f"  {key}: asks {before['asks_priors']}->{after['asks_priors']}, "
                         f"offered {sorted(before['offered'])}->{sorted(after['offered'])}")
    for (name, label, dq, b, a), n in sorted(counts.items()):
        if b or a:
            print(f"{n:3}  {name:15} priors={label:9} dq={dq:6} before {b!s:5} after {a}")
    print("\n".join(notes))


if __name__ == "__main__":
    main()
