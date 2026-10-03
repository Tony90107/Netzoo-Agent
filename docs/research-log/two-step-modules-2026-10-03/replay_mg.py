"""Log 327: replay the recorded pf-patient-specific-modules calls end to end under the current code.

Usage (repository root): python docs/research-log/two-step-modules-2026-10-03/replay_mg.py [n]

`pf_recorded_calls.json` holds the five SP-candidate trials' provider replies
(Log 326) without the SiblingSemanticPatch, which MG makes unnecessary. Each is
routed by `evaluate` with a provider that replays them in order (a different
call order fails), then answered by `respond()` and its card rendered.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
import evaluate_routing  # noqa: E402
from evaluate_routing import ProjectPolicyLoader, RoutingScenario, evaluate  # noqa: E402
from netzoo_agent_core.cli import terminal_cards  # noqa: E402
from netzoo_agent_core.cli.follow_up import build_next_turn_prompt  # noqa: E402
from netzoo_agent_core.contracts import HumanMessage, WorkflowPlan  # noqa: E402
from netzoo_agent_core.graph import response as response_module  # noqa: E402
from netzoo_agent_core.reply_cards import build_reply_card  # noqa: E402
from test_sibling_only_reduction import RecordedProvider  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
terminal_cards._width = lambda: 76


def route(fixture):
    decisions = []
    original = evaluate_routing.invoke_router

    def recording(context, state, prompt):
        result = original(context, state, prompt)
        decisions.append(result.decision)
        return result

    evaluate_routing.invoke_router = recording
    try:
        case = RoutingScenario.model_validate({"id": "pf", "language": "en", "category": "positive",
                                               "prompt": fixture["prompt"],
                                               "expected": {"status": "ambiguous", "actions": []}})
        evaluate([case], provider=RecordedProvider(fixture["calls"]), model_name="recorded")
    finally:
        evaluate_routing.invoke_router = original
    return decisions[0]


def answer(task, decision):
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task, decision=decision.model_dump(), status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None}
    reply = response_module.respond(SimpleNamespace(project_policy=POLICY, response_llm=None), state)
    result = {**state, "messages": [HumanMessage(content=task), reply["messages"][-1]], "reply_kind": reply["reply_kind"]}
    card = build_reply_card(result, build_next_turn_prompt(result), POLICY, task=task)
    shown = ""
    if card is not None:
        data = card.model_dump(mode="json")
        shown = terminal_cards.render_card(data, color=False)
        if data.get("choices"):
            shown += "\n" + "\n".join(terminal_cards.render_options(data, color=False))
    return reply["reply_kind"], str(reply["messages"][-1].content), shown


def main(limit):
    for number, fixture in enumerate(json.loads((HERE / "pf_recorded_calls.json").read_text())[:limit], 1):
        decision = route(fixture)
        readings = [(h.outcome.artifact_type, h.outcome.granularity) for h in decision.outcome_hypotheses]
        print(f"##### trial {number}: {decision.capability_match_status} {decision.matched_actions} "
              f"{decision.hypothesis_actions} readings={readings}")
        kind, text, card = answer(fixture["prompt"], decision)
        print(f"--- reply ({kind})\n{text}\n--- card\n{card}\n")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5)
