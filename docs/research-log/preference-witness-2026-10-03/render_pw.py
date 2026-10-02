"""Render recorded preference trials as PW would answer them (Log 318).

Usage (repository root): python docs/research-log/preference-witness-2026-10-03/render_pw.py <prompt prefix> ...

For the first traced trial whose prompt starts with each prefix, the recorded
MethodComparisonReview payload is fed back through `invoke_condition_recommender`
(a fake model returns it), on the recorded decision with its recommendation
removed. The reply and the terminal card are then rendered. Nothing calls a model.
"""
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(HERE))
from replay_pw import traces  # noqa: E402
from test_condition_recommender import _context  # noqa: E402
from evaluate_routing import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.cli import terminal_cards  # noqa: E402
from netzoo_agent_core.cli.follow_up import build_next_turn_prompt  # noqa: E402
from netzoo_agent_core.contracts import HumanMessage, LLMUsage, TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.graph import response as response_module  # noqa: E402
from netzoo_agent_core.graph.condition_recommender import invoke_condition_recommender  # noqa: E402
from netzoo_agent_core.reply_cards import build_reply_card  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
terminal_cards._width = lambda: 76


def render(task, decision):
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task, decision=decision.model_dump(), status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None}
    reply = response_module.respond(SimpleNamespace(project_policy=POLICY, response_llm=None), state)
    result = {**state, "messages": [HumanMessage(content=task), reply["messages"][-1]], "reply_kind": reply["reply_kind"]}
    card = build_reply_card(result, build_next_turn_prompt(result), POLICY, task=task)
    data = card.model_dump(mode="json")
    shown = terminal_cards.render_card(data, color=False)
    if data.get("choices"):
        shown += "\n" + "\n".join(terminal_cards.render_options(data, color=False))
    return shown, str(reply["messages"][-1].content)


def main(prefixes):
    for prefix in prefixes:
        for _, case, trace in traces():
            if not trace["prompt"].startswith(prefix):
                continue
            call = next((c for c in trace.get("calls", []) if c.get("schema") == "MethodComparisonReview"), None)
            if not call or not isinstance(call.get("parsed"), dict) or not call["parsed"].get("preference"):
                continue
            recorded = TaskDecision.model_validate(trace["decision"])
            before = recorded.model_copy(update={"advisory_recommendation": None})
            context, state, _, _ = _context(Path(tempfile.mkdtemp()), call["parsed"])
            context.project_policy = POLICY
            after, _, _ = invoke_condition_recommender(context, state, trace["prompt"], before, LLMUsage(), [])
            shown, text = render(trace["prompt"], after)
            print(f"########## {case}: {trace['prompt'][:100]}")
            print(shown)
            print("---- full text (first 500 characters)")
            print(text[:500])
            print()
            break


if __name__ == "__main__":
    main(sys.argv[1:])
