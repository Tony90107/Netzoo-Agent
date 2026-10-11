"""Log 409: re-render every labelled recording with one checkout's routing-time verdict step and renderers.

Usage (repository root):
  REPLAY_CODE_ROOT=<checkout> python docs/research-log/verdict-architecture-2026-10-12/replay409.py <out.jsonl>

For every session of the labelled rounds (n11, s11, b12, m13, r14, x15), takes the stored decision -- routing
and the check as recorded, after that arm's own verdict step -- applies the checkout's `checked_match` (the
step that runs last in `invoke_router`) and renders the reply and card with the checkout's code. No model is
called. Run once with the live code (base) and once with the candidate; `compare409.py` diffs them.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CODE_ROOT = Path(os.environ.get("REPLAY_CODE_ROOT") or ROOT)
sys.path.insert(0, str(CODE_ROOT / "scripts"))
WORKTREES = ROOT.parent / ".worktrees"

from evaluate_routing import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.cli.follow_up import build_next_turn_prompt  # noqa: E402
from netzoo_agent_core.contracts import HumanMessage, TaskDecision  # noqa: E402
from netzoo_agent_core.graph.response import respond  # noqa: E402
from netzoo_agent_core.interpretation.checked_match import checked_match  # noqa: E402
from netzoo_agent_core.interpretation.unmapped_routes import without_unmapped_candidates  # noqa: E402
from netzoo_agent_core.reply_cards import build_reply_card  # noqa: E402

POLICY = ProjectPolicyLoader(CODE_ROOT).load()
ARMS = {
    "n11": ["netzoo-verdict-base", "netzoo-verdict-cand"], "s11": ["netzoo-verdict-base", "netzoo-verdict-cand"],
    "b12": ["netzoo-p1-base", "netzoo-p1-cand"], "m13": ["netzoo-cm-base", "netzoo-cm-cand"],
    "r14": ["netzoo-rr-base", "netzoo-rr-cand"], "x15": ["netzoo-score-live"],
}


def study_purpose(tree: str, run_id: str | None) -> dict | None:
    path = WORKTREES / tree / ".netzoo" / "traces" / str(run_id) / "events.jsonl"
    if not run_id or not path.exists():
        return None
    for line in path.read_text().splitlines():
        event = json.loads(line) if line.strip() else {}
        if event.get("event_type") == "routing.study_purpose_detected":
            payload = event["payload"]
            return {"design": payload.get("design"), "design_quote": payload.get("design_quote"),
                    "claims": payload.get("claims") or []}
    return None


def render(task: str, decision: TaskDecision, plan: dict, purpose: dict | None) -> dict:
    plan = {**plan, "decision": decision.model_dump()}
    state = {"decision": decision.model_dump(), "plan": plan, "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None, "study_purpose": purpose}
    out = respond(SimpleNamespace(project_policy=POLICY), state)
    result = {**state, "messages": [HumanMessage(content=task), out["messages"][-1]],
              "reply_kind": out.get("reply_kind")}
    try:
        card = build_reply_card(result, build_next_turn_prompt(result), POLICY, task=task).model_dump()
    except Exception as error:  # the runtime skips invalid cards without discarding the reply
        card = {"error": f"{type(error).__name__}: {str(error)[:200]}"}
    return {"reply": str(out["messages"][-1].content), "reply_kind": out.get("reply_kind"), "card": card}


def main() -> None:
    out_path = Path(sys.argv[1])
    rows = errors = 0
    with out_path.open("w") as handle:
        for tag, trees in ARMS.items():
            for tree in trees:
                for path in sorted((WORKTREES / tree / ".netzoo" / "sessions").glob(f"ve-{tag}-*.json")):
                    data = json.loads(path.read_text())
                    messages = data.get("messages") or []
                    task = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), None)
                    plan = data.get("plan") or {}
                    stored = plan.get("decision")
                    if not task or not stored or stored.get("action") != "no_tool":
                        continue
                    row = {"session": path.stem, "tree": tree}
                    try:
                        decision = without_unmapped_candidates(TaskDecision.model_validate(stored))
                        decision = checked_match(decision, POLICY.workflows)
                        row.update(render(task, decision, plan, study_purpose(tree, data.get("run_id"))))
                        row["matched"] = decision.matched_actions
                        row["basis"] = decision.match_basis
                    except Exception as error:  # a recorded decision the current contract rejects
                        row["error"] = f"{type(error).__name__}: {str(error)[:200]}"
                        errors += 1
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                    rows += 1
    print(f"rows {rows} errors {errors} -> {out_path}")


if __name__ == "__main__":
    main()
