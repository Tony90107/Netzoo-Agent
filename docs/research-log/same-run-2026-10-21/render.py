"""ROUND-17: the reply this checkout gives each changed gold-DECLINE reading (B2 decision, then `respond`). No model calls.

Usage: python3 render.py > replies.txt
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "stability-round13-2026-10-21"))
import harness  # noqa: E402

replay_full = harness.replay_full
WANT = ["hb-h3main-L21-1", "hb-h1-H40-1", "hb-h2main-J44-1", "hb-h1-H18-1", "hb-h3main-L13-1", "cj-p5r-C08-1"]


def main():
    import netzoo_agent_core.interpretation.core_decision as core_decision
    from netzoo_agent_core.graph.response import respond

    original, seen = core_decision.decide_core, {}

    def spy(decision, task="", **kwargs):
        seen["decision"], seen["core"] = decision, original(decision, task, **kwargs)
        return seen["core"]

    for key, folder, sid, task, payload, reread, found, _n in harness.readings():
        if sid not in WANT:
            continue
        core_decision.decide_core = spy
        try:
            replay_full.replay(folder, task, payload, reread, found)
        finally:
            core_decision.decide_core = original
        final = core_decision.with_core(seen["decision"], seen["core"])
        reply = respond(None, {"decision": final.model_dump(mode="json"), "messages": []})
        print(f"===== {sid}: {seen['core'].kind} ({reply.get('reply_kind')})\nRequest: {task}\n")
        print(reply["messages"][-1].content, "\n")


if __name__ == "__main__":
    main()
