"""Log 337 offline gate: the repository's SR on every recorded final decision.

Usage (repository root): python docs/research-log/shadow-readings-2026-10-04/replay_sr.py

Must agree with scan_shadow.txt (the declared prototype). Applies
`drop_shadow_readings` (with rule B's guard) and matches before and after.
SR was withdrawn in Log 338, so this runs only on its commit-less candidate
tree; its output is kept in replay_sr.txt.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "docs" / "research-log" / "test12-2026-10-02"), str(ROOT / "scripts")]

import replay_cards  # noqa: E402
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis, SemanticInterpretation  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402
from netzoo_agent_core.routing.reading_selection import drop_shadow_readings  # noqa: E402


def main():
    fired, seen, rows = defaultdict(Counter), set(), Counter()
    for task, decision in replay_cards.rows():
        raw = decision.get("outcome_hypotheses") or []
        if len(raw) < 2:
            continue
        readings = [OutcomeHypothesis.model_validate(item) for item in raw]
        reading = SemanticInterpretation.model_construct(
            request_mode=decision.get("request_mode") or "guidance", semantic_goal="", outcome_hypotheses=readings)
        result, dropped = drop_shadow_readings(task, reading)
        if not dropped:
            continue
        rows[task] += 1
        key = json.dumps([task, raw], sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        before = match_semantic_request(task, readings, request_mode="guidance")
        after = match_semantic_request(task, result.outcome_hypotheses, request_mode="guidance")
        fired[task][(tuple(dropped), before.status, tuple(before.matched_actions or before.hypothesis_actions),
                     after.status, tuple(after.matched_actions or after.hypothesis_actions))] += 1
    print(f"fires on {len(seen)} distinct decisions, {sum(rows.values())} rows, {len(fired)} prompts")
    for task, outcomes in sorted(fired.items(), key=lambda item: -rows[item[0]]):
        print(f"- ({rows[task]} rows) {' '.join(task.split())[:130]}")
        for (drops, bs, ba, as_, aa), n in outcomes.most_common():
            print(f"    {n}x drop {list(drops)}\n       {bs} {list(ba)} -> {as_} {list(aa)}")


if __name__ == "__main__":
    main()
