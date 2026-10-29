"""U2 (ROUND.md): the recorded ac1 j6 X22 turn-2 decision (session plan) through `guidance_interaction` and
`build_next_turn_prompt`, with this checkout's code. No model calls.
Usage (from docs/research-log): python3 decided-no-unavailable-2026-10-29/rerender.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.interpretation.guidance_interaction import guidance_interaction  # noqa: E402

session = json.loads(Path("answered-counts-2026-10-29/live/ac1/hb-ac1-X22-1/t2/session.json").read_text())
decision = TaskDecision.model_validate(session["plan"]["decision"])
print("core:", decision.core.kind, decision.core.basis, "| match status:", decision.capability_match_status)
interaction = guidance_interaction(decision)
print("interaction:", interaction.status if interaction else None)
stdout = Path("answered-counts-2026-10-29/live/ac1/hb-ac1-X22-1/t2/stdout.txt").read_text()
print("recorded reply had the notice:", "Semantic routing unavailable" in stdout, "| had the limit:", "31,960,000" in stdout)
try:
    from netzoo_agent_core.cli.follow_up import build_next_turn_prompt
    prompt = build_next_turn_prompt({"decision": decision.model_dump(mode="json"), "plan": session["plan"]})
    print("next step now:", prompt.kind, "|", prompt.question)
except Exception as exc:  # noqa: BLE001 -- reported
    print("next step: not rebuilt here:", type(exc).__name__, str(exc)[:120])
