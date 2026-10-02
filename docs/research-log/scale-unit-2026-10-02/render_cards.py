"""Render the terminal card and reply text of chosen traced trials with this tree's code (Log 310).

Usage (repository root):
  python docs/research-log/scale-unit-2026-10-02/render_cards.py <report.json[.gz]>:<case id> [...]

Each trial's final decision is rendered as the CLI shows it (`respond()`, then
`build_reply_card`, then the terminal renderer). Nothing calls a model.
"""
import gzip
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_routing import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.cli import terminal_cards  # noqa: E402
from netzoo_agent_core.cli.follow_up import build_next_turn_prompt  # noqa: E402
from netzoo_agent_core.contracts import HumanMessage, TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.graph import response as response_module  # noqa: E402
from netzoo_agent_core.reply_cards import build_reply_card  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
terminal_cards._width = lambda: 76


def render(task, raw):
    made = TaskDecision.model_validate(raw)
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task, decision=made.model_dump(), status="respond_only")
    state = {"decision": made.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None}
    reply = response_module.respond(SimpleNamespace(project_policy=POLICY, response_llm=None), state)
    result = {**state, "messages": [HumanMessage(content=task), reply["messages"][-1]], "reply_kind": reply["reply_kind"]}
    card = build_reply_card(result, build_next_turn_prompt(result), POLICY, task=task)
    text = str(reply["messages"][-1].content)
    shown = ""
    if card is not None:
        data = card.model_dump(mode="json")
        shown = terminal_cards.render_card(data, color=False)
        if data.get("choices"):
            shown += "\n" + "\n".join(terminal_cards.render_options(data, color=False))
    return reply["reply_kind"], shown, text


def main():
    for spec in sys.argv[1:]:
        path, case = spec.rsplit(":", 1)
        opener = gzip.open if path.endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8") as handle:
            report = json.load(handle)
        for row in report["results"]:
            if row["id"] != case:
                continue
            trace = row["_trace"]
            kind, shown, text = render(trace["prompt"], trace["decision"])
            print(f"########## {Path(path).name} {case} [{trace['decision'].get('capability_match_status')}] {kind}")
            print(shown)
            print("---- full text (first 600 characters)")
            print(text[:600])
            print()


if __name__ == "__main__":
    main()
