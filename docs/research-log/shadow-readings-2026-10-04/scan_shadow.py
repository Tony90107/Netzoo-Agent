"""Log 337 exploratory scan (before declaration): where would the shadow-reading rule fire?

Usage (repository root): python docs/research-log/shadow-readings-2026-10-04/scan_shadow.py

Prototype SR: reading B shadows reading A when both quote the same artifact text
(explicit, in the request) and, on some dimension where A has an explicit quote,
B has a different, concrete value (not unknown) and no explicit quote of its own. Rows are those of
`test12-2026-10-02/replay_cards.py` (traced reports and TEST_PROMPTS rounds).
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "docs" / "research-log" / "test12-2026-10-02"), str(ROOT / "scripts")]

import replay_cards  # noqa: E402
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis  # noqa: E402
from netzoo_agent_core.graph.condition_recommender import _quote_grounded  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402

DIMENSIONS = {"operation": "operation", "granularity": "granularity", "artifact_type": "artifact_type"}


def explicit(reading, dimension, task):
    return [e.text_span.strip() for e in reading.evidence
            if e.dimension == dimension and e.source == "explicit" and e.text_span
            and _quote_grounded(task, e.text_span)]


def _norm(span):
    return " ".join(span.casefold().rstrip(".,;:!?").split())


def shadowed_by(task, b, a):
    shared = {_norm(s) for s in explicit(a, "artifact_type", task)} & {_norm(s) for s in explicit(b, "artifact_type", task)}
    if not shared:
        return None
    for dimension, field in DIMENSIONS.items():
        if dimension == "artifact_type":
            continue
        value = getattr(b.outcome, field)
        if (explicit(a, dimension, task) and value != getattr(a.outcome, field)
                and value not in {"unknown", "not_applicable"} and not explicit(b, dimension, task)):
            return dimension
    return None


def main():
    fired, seen, rows = defaultdict(Counter), set(), Counter()
    for task, decision in replay_cards.rows():
        raw = decision.get("outcome_hypotheses") or []
        if len(raw) < 2:
            continue
        readings = [OutcomeHypothesis.model_validate(item) for item in raw]
        dropped = []
        for i, b in enumerate(readings):
            for j, a in enumerate(readings):
                if i != j and (dim := shadowed_by(task, b, a)) and not shadowed_by(task, a, b):
                    dropped.append((i, dim, (a.outcome.operation, a.outcome.artifact_type, a.outcome.granularity),
                                    (b.outcome.operation, b.outcome.artifact_type, b.outcome.granularity)))
                    break
        if not dropped:
            continue
        rows[task] += 1
        key = json.dumps([task, raw], sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        kept = [r for i, r in enumerate(readings) if i not in {d[0] for d in dropped}]
        before = match_semantic_request(task, readings, request_mode="guidance")
        after = match_semantic_request(task, kept, request_mode="guidance") if kept else None
        fired[task][(tuple((d[1], d[2], d[3]) for d in dropped), before.status,
                     tuple(before.matched_actions or before.hypothesis_actions),
                     after.status if after else None,
                     tuple((after.matched_actions or after.hypothesis_actions) if after else ()))] += 1
    print(f"fires on {len(seen)} distinct decisions, {sum(rows.values())} rows, {len(fired)} prompts")
    for task, outcomes in sorted(fired.items(), key=lambda item: -rows[item[0]]):
        print(f"- ({rows[task]} rows) {' '.join(task.split())[:130]}")
        for (drops, bs, ba, as_, aa), n in outcomes.most_common():
            print(f"    {n}x drop {list(drops)}\n       {bs} {list(ba)} -> {as_} {list(aa)}")


if __name__ == "__main__":
    main()
