"""PLAN-M-SHADOW.md gate B4 ($0, not scored): what candidate C would ask on the six h9 sessions M flagged, from the
recorded h9 trace (the live call and the turn's decision) and the recorded closed-menu reading (`menu-h9.json`),
decided and rendered by C's code (`.worktrees/netzoo-m-hold`). The question rule was set on these six, so this only
shows the questions before the live round.

Usage: python3 b4_dryrun.py > mhold-build/b4-dryrun.txt
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = HERE.parents[2].parent / "netzoo-m-hold"
sys.path.insert(0, str(C / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.contracts.menu_reading import MenuReading  # noqa: E402
from netzoo_agent_core.interpretation.ask_facts import ask_result  # noqa: E402
from netzoo_agent_core.interpretation.clarify_goal import clarify_result  # noqa: E402
from netzoo_agent_core.interpretation.m_hold import held_core, triggers  # noqa: E402
from netzoo_agent_core.interpretation.menu_decision import decide_menu  # noqa: E402

FLAGGED = ("Z03", "Z05", "Z21", "Z22", "Z14", "Z23")


def main():
    import netzoo_agent_core
    assert Path(netzoo_agent_core.__file__).resolve().is_relative_to(C.resolve()), "must be C's code"
    items = {i["id"]: i for i in json.loads((HERE / "h9" / "items.json").read_text())["single"]}
    menu = {r["id"]: r for r in json.loads((HERE / "menu-h9.json").read_text())["rows"]}
    for key in FLAGGED:
        turn = HERE / "live" / "h9" / f"hb-h9-{key}-1" / "t1"
        found = [json.loads(line) for trace in sorted(turn.glob("trace-*.jsonl"))
                 for line in trace.read_text().splitlines() if line.strip()]
        live = next(e["payload"] for e in reversed(found) if e.get("event_type") == "core.decision")
        core = CoreDecision.model_validate(live)
        decision = TaskDecision.model_validate(json.loads((turn / "session.json").read_text())["plan"]["decision"])
        decision = decision.model_copy(update={"core": None})
        task = items[key]["prompt"]
        decided = decide_menu(MenuReading.model_validate(menu[key]["reading"]), task)
        held = held_core(core, decision, decided, task) if triggers(core, True) else None
        print(f"== {key} ({items[key]['category']}, gold {items[key]['expected_call']}): live {core.kind}/{core.basis}; "
              f"menu {decided.kind}/{decided.basis} {[q.dimension + ':' + q.kind for q in decided.questions]}")
        if held is None:
            print("   not held\n")
            continue
        state = {"decision": TaskDecision(action="no_tool", in_scope=True, should_execute=False, reason="r",
                                          confidence=0.0, core=held).model_dump(mode="json")}
        text = ask_result(state, lambda t, k: t) or clarify_result(state, lambda t, k: t)
        print(f"   held {held.kind}/{held.basis}, source {held.evidence['m_hold']['source']}")
        print("   " + text.replace("\n", "\n   ") + "\n")


if __name__ == "__main__":
    main()
