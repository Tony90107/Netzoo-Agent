"""C31 fail-closed diagnosis ($0): readings whose routing ended in `research_choices_unavailable` although the
hypothesis reader answered (no failed call, budget not spent), decided again as an ordinary turn -- the reader's
answer "no stated hypotheses" is not a failure, so the check and the fact agent decide.

Usage: python3 simulate.py OUT.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "stability-round13-2026-10-21"))
import harness  # noqa: E402

replay_full = harness.replay_full
replay_full.GOAL_READS.update({d["task"]: d["read"] for d in json.loads(
    (HERE.parent / "goal-read-2026-10-21/reads.json").read_text())["reads"] if d["read"]})


def answered(found: list[dict]) -> bool:
    """The hypothesis reader ran and answered: its matched event, no failed event, and the turn budget not spent."""
    kinds = {e["event_type"] for e in found}
    return "routing.hypothesis_bases_matched" in kinds and "routing.hypothesis_bases_failed" not in kinds


def main(out: str):
    import netzoo_agent_core.interpretation.core_decision as core_decision

    original_replay, original_decide, current, changed = replay_full.replay, core_decision.decide_core, {}, []

    def replay(folder, task, payload, reread, found):
        current["found"] = found
        return original_replay(folder, task, payload, reread, found)

    def decide(decision, task="", *, reason_code=""):
        if reason_code == "research_choices_unavailable" and answered(current["found"]):
            changed.append(task[:80])
            decision = decision.model_copy(update={"match_basis": "unverified_evidence", "clarification_question": None})
            reason_code = "research_choices_unread"
        return original_decide(decision, task, reason_code=reason_code)

    replay_full.replay, core_decision.decide_core = replay, decide
    try:
        harness.run(out)
    finally:
        replay_full.replay, core_decision.decide_core = original_replay, original_decide
    print(f"{len(changed)} readings relabelled")


if __name__ == "__main__":
    main(sys.argv[1])
