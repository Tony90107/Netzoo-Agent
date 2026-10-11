"""Re-render every recorded guidance session's reply and card with the current code (Log 403).

Usage (repository root):
  [REPLAY_CODE_ROOT=<checkout>] python docs/research-log/requirement-verdicts-2026-10-10/replay_sessions.py \
      <out.jsonl> [prefix ...]

Reads the recorded sessions of the capability-trap worktrees (`.worktrees/*/.netzoo/sessions/ce-*.json`),
takes the stored task and decision, and runs `graph.response.respond` and the reply card on them, as
the CLI does after routing. No model is called: every capability-check reply is code-rendered, so the
output depends only on the recorded decision and the code under test. Each row holds the recorded and
the re-rendered reply, so a renderer change can be compared over every recorded session.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import os

ROOT = Path(__file__).resolve().parents[3]
# REPLAY_CODE_ROOT renders with another checkout's code (the base arm of a comparison).
CODE_ROOT = Path(os.environ.get("REPLAY_CODE_ROOT") or ROOT)
sys.path.insert(0, str(CODE_ROOT / "scripts"))

from evaluate_routing import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.cli.follow_up import build_next_turn_prompt  # noqa: E402
from netzoo_agent_core.contracts import HumanMessage, TaskDecision  # noqa: E402
from netzoo_agent_core.graph.response import respond  # noqa: E402
from netzoo_agent_core.reply_cards import build_reply_card  # noqa: E402

WORKTREES = ROOT.parent / ".worktrees"
# REPLAY_ARMS / REPLAY_SESSION_PREFIX select other recorded sessions (the heldout11 round: ve-).
ARMS = tuple((os.environ.get("REPLAY_ARMS") or "netzoo-trap-base,netzoo-cc-cand,netzoo-forms-cand").split(","))
SESSION_PREFIX = os.environ.get("REPLAY_SESSION_PREFIX", "ce")
POLICY = ProjectPolicyLoader(CODE_ROOT).load()


def sessions(prefixes: tuple[str, ...]):
    for arm in ARMS:
        for path in sorted((WORKTREES / arm / ".netzoo" / "sessions").glob(f"{SESSION_PREFIX}-*.json")):
            name = path.stem
            if prefixes and not any(name.startswith(f"{SESSION_PREFIX}-{prefix}-") for prefix in prefixes):
                continue
            yield arm, name, json.loads(path.read_text())


def study_purpose(arm: str, run_id: str | None) -> dict | None:
    """The turn's model-read study purpose, from its `routing.study_purpose_detected` trace event.

    The session file keeps the decision but not the routing state, and without the purpose
    `respond()` falls back to the word witnesses, which quote differently.
    """
    path = WORKTREES / arm / ".netzoo" / "traces" / str(run_id) / "events.jsonl"
    if not run_id or not path.exists():
        return None
    for line in path.read_text().splitlines():
        event = json.loads(line)
        if event.get("event_type") == "routing.study_purpose_detected":
            payload = event["payload"]
            return {"design": payload.get("design"), "design_quote": payload.get("design_quote"),
                    "claims": payload.get("claims") or []}
    return None


try:  # Log 403 part D: the routing-time step that runs after the check, when the code under test has it.
    from netzoo_agent_core.interpretation.unmapped_routes import without_unmapped_candidates  # noqa: E402
except ImportError:
    without_unmapped_candidates = None


def render(task: str, decision: dict, plan: dict, purpose: dict | None = None) -> dict:
    made = TaskDecision.model_validate(decision)
    if without_unmapped_candidates is not None:
        made = without_unmapped_candidates(made)
    plan = {**plan, "decision": made.model_dump()}
    state = {"decision": made.model_dump(), "plan": plan, "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None, "study_purpose": purpose}
    out = respond(SimpleNamespace(project_policy=POLICY), state)
    result = {**state, "messages": [HumanMessage(content=task), out["messages"][-1]],
              "reply_kind": out.get("reply_kind")}
    card_error = None
    try:
        card = build_reply_card(result, build_next_turn_prompt(result), POLICY, task=task)
    except Exception as error:  # the runtime skips invalid cards without discarding the reply
        card = None
        card_error = f"{type(error).__name__}: {str(error)[:200]}"
    return {"reply": str(out["messages"][-1].content), "reply_kind": out.get("reply_kind"),
            "card": card.model_dump() if card is not None else None, "card_error": card_error}


def main() -> None:
    out_path, prefixes = Path(sys.argv[1]), tuple(sys.argv[2:])
    rows = errors = 0
    with out_path.open("w") as handle:
        for arm, name, data in sessions(prefixes):
            messages = data.get("messages") or []
            # The last turn's request is what the stored decision answers (multi-turn items).
            task = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), None)
            recorded = next((m["content"] for m in reversed(messages) if m.get("role") == "assistant"), None)
            plan = data.get("plan") or {}
            decision = plan.get("decision")
            if not task or not decision or decision.get("action") != "no_tool":
                continue
            row = {"arm": arm, "session": name, "task": task, "recorded": recorded,
                   "decision": decision}
            try:
                row.update(render(task, decision, plan, study_purpose(arm, data.get("run_id"))))
            except Exception as error:  # a recorded decision the current contract rejects
                row["error"] = f"{type(error).__name__}: {str(error)[:200]}"
                errors += 1
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            rows += 1
    print(f"rows {rows} errors {errors} -> {out_path}")


if __name__ == "__main__":
    main()
