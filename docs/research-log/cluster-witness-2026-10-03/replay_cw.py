"""Log 332 offline evidence: every recorded final decision CW changes.

Usage (repository root): python docs/research-log/cluster-witness-2026-10-03/replay_cw.py

Rows are those of `test12-2026-10-02/replay_cards.py` (traced reports and the
TEST_PROMPTS rounds). CW alone is applied -- `drop_unwitnessed_readings` with
only the sample_cluster_assignment witness -- so the multi-omic rule of Log
313 does not count here. Each change is matched before and after.
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
from netzoo_agent_core.routing import reading_selection  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402

CW = {"sample_cluster_assignment": reading_selection.READING_WITNESSES["sample_cluster_assignment"]}


def main():
    reading_selection.READING_WITNESSES = CW
    seen, changed, trials, kept_by_guard, single = set(), defaultdict(Counter), Counter(), Counter(), Counter()
    for task, decision in replay_cards.rows():
        raw = decision.get("outcome_hypotheses") or []
        has = any(item["outcome"]["artifact_type"] == "sample_cluster_assignment" for item in raw)
        if not has:
            continue
        if len(raw) < 2:
            single[(bool(CW["sample_cluster_assignment"].search(task)), task)] += 1
            continue
        hypotheses = [OutcomeHypothesis.model_validate(item) for item in raw]
        reading = SemanticInterpretation.model_construct(
            request_mode=decision.get("request_mode") or "guidance", semantic_goal="", outcome_hypotheses=hypotheses)
        kept = reading_selection.drop_unwitnessed_readings(task, reading)[0].outcome_hypotheses
        if kept == hypotheses:
            if not CW["sample_cluster_assignment"].search(task):
                kept_by_guard[task] += 1
            continue
        trials[task] += 1
        key = json.dumps([task, raw], sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        before = match_semantic_request(task, hypotheses, request_mode="guidance")
        after = match_semantic_request(task, kept, request_mode="guidance")
        changed[task][(before.status, tuple(before.matched_actions or before.hypothesis_actions),
                       after.status, tuple(after.matched_actions or after.hypothesis_actions))] += 1
    print(f"changed: {len(seen)} distinct decisions, {sum(trials.values())} rows, {len(changed)} prompts")
    for task, outcomes in changed.items():
        print(f"- ({trials[task]} rows) witness={bool(CW['sample_cluster_assignment'].search(task))} | "
              f"{' '.join(task.split())[:120]}")
        for (bs, ba, as_, aa), count in outcomes.most_common():
            print(f"    {count}x {bs} {list(ba)} -> {as_} {list(aa)}")
    print("kept by the guard:", dict(kept_by_guard))
    print("single readings (untouched), by witness:")
    for (witness, task), count in single.most_common():
        print(f"    {count}x witness={witness} | {' '.join(task.split())[:100]}")


if __name__ == "__main__":
    main()
