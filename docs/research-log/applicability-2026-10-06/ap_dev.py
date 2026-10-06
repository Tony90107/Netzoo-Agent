"""Log 380 prep: replay item 4 on SEEN data (calibration only, never a verdict). No model is called.

Usage (repository root): python3 docs/research-log/applicability-2026-10-06/ap_dev.py
Takes Log 379's recorded base-arm decisions on heldout19 (live/s19-decisions.json, code without
item 3 or 4) and the dev data-facts readings of the same prompts (dev19-calls.json, rep-matched),
attaches the reading and the applicability exactly as routing would, re-renders reply and card,
and compares with the annotation (priors_stated, mirna_stated).
"""
import json
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
from langchain_core.messages import HumanMessage  # noqa: E402
from netzoo_agent_core.cli.follow_up import build_next_turn_prompt  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.contracts.data_facts import DataFactsProposal  # noqa: E402
from netzoo_agent_core.graph import response  # noqa: E402
from netzoo_agent_core.graph.data_facts_call import verify_data_facts  # noqa: E402
from netzoo_agent_core.interpretation.applicability import assess_applicability, merge_inputs, needs_data_facts  # noqa: E402
from netzoo_agent_core.interpretation.request_requirements import stated_in_text  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.reply_cards import build_reply_card  # noqa: E402
from netzoo_agent_core.routing.capability_compatibility import input_availability  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
PF = ROOT / "docs/research-log/purpose-first-2026-10-05"


def render(task, decision, purpose):
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task[:200], decision=decision.model_dump(), status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None, "study_purpose": purpose}
    out = response.respond(SimpleNamespace(project_policy=POLICY), state)
    result = {**state, "messages": [HumanMessage(content=task), out["messages"][-1]], "reply_kind": out["reply_kind"]}
    return str(out["messages"][-1].content), build_reply_card(result, build_next_turn_prompt(result), POLICY, task=task)


SETS = {
    "19": (PF / "heldout19/heldout.json", PF / "live/s19-decisions.json", "base"),
    "18": (ROOT / "docs/research-log/purpose-contract-2026-10-04/heldout18/heldout.json",
           ROOT / "docs/research-log/purpose-contract-2026-10-04/live/s18-decisions.json", "cand"),
}


def main(number="19"):
    held, recorded, arm_name = SETS[number]
    items = {i["id"]: i for i in json.loads(held.read_text())["items"]}
    rows = json.loads(recorded.read_text())
    calls = {(r["id"], r["rep"]): r["proposal"] for r in json.loads((HERE / f"dev{number}-calls.json").read_text())}
    counts, notes = Counter(), []
    for key, row in rows.items():
        arm, item_id, rep = key.split("-")
        if arm != arm_name:
            continue
        item, task = items[item_id], row["prompt"]
        decision = TaskDecision.model_validate(row["decision"])
        recorded_purpose = row.get("study_purpose") or {}
        if isinstance(recorded_purpose, str):
            import ast
            recorded_purpose = ast.literal_eval(recorded_purpose) if recorded_purpose not in ("None", "") else {}
        purpose = {k: recorded_purpose.get(k) for k in ("source", "design", "design_quote", "claims")}
        listed = [*decision.matched_actions, *decision.hypothesis_actions, *decision.recommended_actions]
        if decision.action != "no_tool" or not needs_data_facts(listed, stated_in_text(task)):
            counts["not asked to read"] += 1
            continue
        facts, _ = verify_data_facts(task, DataFactsProposal.model_validate(calls[(item_id, int(rep))]))
        present = set(input_availability(task).present) | {
            v for h in decision.outcome_hypotheses for v in h.outcome.input_artifacts if v != "unknown"}
        judged = decision.model_copy(update={
            "data_facts": facts, "applicability": assess_applicability(listed, merge_inputs(present, facts), task)})
        try:
            old_text, old_card = render(task, decision, purpose)
            new_text, new_card = render(task, judged, purpose)
        except Exception as error:  # the >8-option card bug, another session's (fix/method-card-option-limit)
            counts[f"render failed in both: {type(error).__name__}"] += 1
            continue
        old_ask = bool(old_card.choices and old_card.choices.header == "Inputs")
        new_ask = bool(new_card.choices and new_card.choices.header == "Inputs")
        new_says_ruled = "which you said you do not have" in new_text
        label = item["priors_stated"]
        counts["read"] += 1
        counts[f"priors {label}: asks old {old_ask} -> new {new_ask}"] += 1
        if new_says_ruled:
            counts[f"priors {label}: says ruled out"] += 1
        if new_ask and label != "unstated":
            notes.append(f"  ASK ON {label} {key}: {new_card.choices.question}")
        if new_says_ruled and label != "ruled_out":
            notes.append(f"  RULED-OUT ON {label} {key}")
        if old_text != new_text:
            counts["reply changed"] += 1
        if "data_question" in item and item["data_question"] == "none" and new_ask and "motif prior" in new_card.choices.question:
            notes.append(f"  ASK WHERE NOT NEEDED {key} ({item['claim_kind']}, priors {label}): "
                         f"{[a.removeprefix('run_') for a in listed]} | {task[-110:]!r}")
        if "data_question" in item:
            counts[f"data_question {item['data_question']}: new asks about priors "
                   f"{bool(new_ask and 'motif prior' in new_card.choices.question)}"] += 1
    for name, n in sorted(counts.items()):
        print(f"{n:4}  {name}")
    print("\n".join(notes))


if __name__ == "__main__":
    main(*sys.argv[1:])
