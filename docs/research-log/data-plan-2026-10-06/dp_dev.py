"""Log 383 prep: replay Logs 380-381's recorded sessions (both arms) with the data-needs plan (SEEN, calibration).

Usage (repository root): python3 docs/research-log/data-plan-2026-10-06/dp_dev.py
Each session's recorded routing decision (item-4 fields stripped) and study purpose are kept; routing's
post-step re-runs with the current code, the data-facts call patched to return that item's reading
(dev20b/dev21, rep-matched). The reply is re-rendered and measured with Log 381's definitions
(ar_analyze.measure). No model is called.
"""
import json
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(HERE)]
from langchain_core.messages import HumanMessage  # noqa: E402
from netzoo_agent_core.contracts import LLMUsage, TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.graph import response, router_invocation  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
import plan_eval  # noqa: E402

sys.path.insert(0, str(ROOT / "docs/research-log/applicability-redo-2026-10-06"))
import ar_analyze as A  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
STRIP = {"data_facts": None, "applicability": [], "data_plan": None}


def replay(row, facts):
    decision = TaskDecision.model_validate(row["decision"]).model_copy(update=STRIP)
    purpose = row.get("study_purpose")
    result = router_invocation._RouterInvocation(decision=decision, routing_state={"study_purpose": purpose},
                                                 usage=LLMUsage(budget_tokens=10**6), budget_warnings=[],
                                                 reason_code="replay")
    with patch.object(router_invocation, "invoke_data_facts", return_value=(facts, result.usage, [])):
        decision = router_invocation._with_applicability(
            SimpleNamespace(recorder=SimpleNamespace(append=lambda *a: None)), {}, row["prompt"], result).decision
    plan = WorkflowPlan(workflow="NO-TOOL", objective=row["prompt"][:200], decision=decision.model_dump(), status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=row["prompt"])],
             "tool_results": [], "evaluation": None, "study_purpose": purpose}
    out = response.respond(SimpleNamespace(project_policy=POLICY), state)
    return {"decision": decision.model_dump(), "reply": str(out["messages"][-1].content), "roles": row["roles"]}, decision


def main():
    table, notes = Counter(), []
    for tag, (decisions, heldout) in plan_eval.SETS.items():
        items = {i["id"]: i for i in json.loads(heldout.read_text())["items"]}
        read = plan_eval.readings(tag)
        for key, row in json.loads(decisions.read_text()).items():
            arm, item_id, rep = key.split("-")
            if "response" in (row.get("roles") or []):
                continue
            item = items[item_id]
            before = A.measure(row)
            session, decision = replay(row, read.get((item_id, int(rep))))
            after = A.measure(session)
            label = item["data_question"]
            for when, m in (("recorded", before), ("plan", after)):
                table[(arm, when, "asks priors | dq=priors")] += (label == "priors") and m["asks_priors"]
                table[(arm, when, "dq=priors sessions")] += label == "priors"
                table[(arm, when, "asks priors | dq!=priors")] += (label != "priors") and m["asks_priors"]
                table[(arm, when, "asks mirna | dq=mirna")] += (label == "mirna") and m["asks_mirna"]
                table[(arm, when, "asks mirna | mirna stated/ruled out")] += (
                    item["mirna_label"] in {"stated", "ruled_out"} and m["asks_mirna"])
                table[(arm, when, "says ruled out | priors ruled out")] += (
                    item["priors_label"] == "ruled_out" and m["says_ruled_out"])
                table[(arm, when, "priors ruled out sessions")] += item["priors_label"] == "ruled_out"
            if after["asks_priors"] != (label == "priors"):
                plan = decision.data_plan
                notes.append(f"  {tag} {key}: dq={label} asks={after['asks_priors']} plan asks {plan.asks() if plan else None} "
                             f"basis {plan.basis if plan else None}")
    for (arm, when, name), n in sorted(table.items()):
        print(f"{arm:4} {when:8} {name:40} {n}")
    print("\n".join(sorted(notes)))


if __name__ == "__main__":
    main()
