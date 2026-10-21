"""ROUND-21 R21-B sizing ($0): would rule R1 accepting a fact quote in the same request sentence as a quote the check
read as uncertain change any call? Every reading replayed by the harness with its recorded fact-agent proposals; an
R1-rejected proposal that passes the relaxed R1 is held to R2-R7 again (this checkout's `kept_facts`) and added.

Usage: python3 r1_sentence.py OUT.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "stability-round13-2026-10-21"))
import harness  # noqa: E402

sys.path.insert(0, str(HERE.parent / "goal-read-2026-10-21"))
replay_full = harness.replay_full
replay_full.GOAL_READS.update({d["task"]: d["read"] for d in json.loads(
    (HERE.parent / "goal-read-2026-10-21/reads.json").read_text())["reads"] if d["read"]})


def main(out: str):
    from types import SimpleNamespace

    import netzoo_agent_core.interpretation.core_decision as core_decision
    from netzoo_agent_core.contracts.fact_check import FactProposals
    from netzoo_agent_core.interpretation import fact_check
    from netzoo_agent_core.interpretation.request_spans import _span
    from netzoo_agent_core.interpretation.sentence_ownership import request_sentences
    from netzoo_agent_core.policy import ProjectPolicyLoader

    policy = ProjectPolicyLoader(HERE.parents[2]).load()
    original, overlaps, added = core_decision.decide_core, fact_check._overlaps, []

    def same_sentence(task):
        sentences = request_sentences(task)

        def where(words):
            span = _span(task, words)
            return {i for i, (s, e) in enumerate(sentences) if span and s < span[1] and span[0] < e}

        return lambda a, b: overlaps(a, b) or bool(where(a) & where(b))

    def relaxed(decision, task="", **kwargs):
        agent = decision.fact_check
        if agent is not None and agent.status == "checked" and task:
            fact_check._overlaps = same_sentence(task)
            try:
                for rejected in agent.rejected:
                    if not rejected.rule.startswith("R1 the check"):
                        continue
                    # proposals recorded before phase 5c have no about/alternatives: they were about the user's data
                    raw = {"about": "user_data", "alternatives": [], **rejected.proposal}
                    proposals = FactProposals.model_validate({"facts": [raw]})
                    kept = fact_check.kept_facts(task, proposals, decision, policy, model=agent.model)
                    new = [f for f in kept.accepted if all(f.user_quote != a.user_quote for a in agent.accepted)]
                    if new:
                        agent = agent.model_copy(update={"accepted": [*agent.accepted, *new][:fact_check.MAX_ASKED]})
                        added.append({"task": task[:120], "questions": [f.question for f in new]})
            finally:
                fact_check._overlaps = overlaps
            decision = decision.model_copy(update={"fact_check": agent})
        return original(decision, task, **kwargs)

    core_decision.decide_core = relaxed
    try:
        harness.run(out)
    finally:
        core_decision.decide_core = original
    print(f"{len(added)} decisions got a question from the relaxed R1")


if __name__ == "__main__":
    main(sys.argv[1])
