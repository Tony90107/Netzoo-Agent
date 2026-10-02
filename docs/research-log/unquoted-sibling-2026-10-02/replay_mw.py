"""Log 313 offline evidence: what MW changes in every recorded final decision.

Usage (repository root): python docs/research-log/unquoted-sibling-2026-10-02/replay_mw.py [--tree]

MW (prototype): when the request names no second omics layer (`LAYER`), a
multi_omic_network reading beside other readings is dropped, provided a reading
remains and the remaining readings validate on their own (the guard of Log
285's rule B). With --tree the repository's `drop_unwitnessed_readings` is used
instead; the Log 313 supplement compares the two printouts.
"""
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(HERE), str(ROOT / "scripts")]

from scan_multiomic import LAYER, traces  # noqa: E402
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis, SemanticInterpretation  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402

TREE = "--tree" in sys.argv


def prototype(task, hypotheses):
    if len(hypotheses) < 2 or LAYER.search(task):
        return hypotheses
    kept = [h for h in hypotheses if h.outcome.artifact_type != "multi_omic_network"]
    if not kept or len(kept) == len(hypotheses) or not validate_outcome_hypotheses(task, kept, "guidance").valid:
        return hypotheses
    return kept


def tree(task, hypotheses):
    from netzoo_agent_core.routing.reading_selection import drop_unwitnessed_readings
    reading = SemanticInterpretation.model_construct(request_mode="guidance", semantic_goal="", outcome_hypotheses=hypotheses)
    return drop_unwitnessed_readings(task, reading)[0].outcome_hypotheses


def main():
    seen, changed, trials, blocked = set(), defaultdict(Counter), Counter(), Counter()
    for case, trace in traces():
        task, raw = trace["prompt"], trace["decision"].get("outcome_hypotheses") or []
        if len(raw) < 2:
            continue
        hypotheses = [OutcomeHypothesis.model_validate(item) for item in raw]
        kept = (tree if TREE else prototype)(task, hypotheses)
        if kept == hypotheses:
            if not LAYER.search(task) and any(h.outcome.artifact_type == "multi_omic_network" for h in hypotheses):
                blocked[(case, task)] += 1
            continue
        trials[(case, task)] += 1
        key = json.dumps([task, raw], sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        before = match_semantic_request(task, hypotheses, request_mode="guidance")
        after = match_semantic_request(task, kept, request_mode="guidance")
        changed[(case, task)][(before.status, tuple(before.matched_actions or before.hypothesis_actions),
                               after.status, tuple(after.matched_actions or after.hypothesis_actions))] += 1
    print(f"changed: {len(seen)} distinct decisions, {sum(trials.values())} trials, {len(changed)} prompts")
    for (case, task), outcomes in sorted(changed.items(), key=lambda item: -trials[item[0]]):
        print(f"- {case} ({trials[(case, task)]} trials) | {' '.join(task.split())[:120]}")
        for (bs, ba, as_, aa), count in outcomes.most_common():
            print(f"    {count}x {bs} {list(ba)} -> {as_} {list(aa)}")
    print("kept by the guard (remaining readings do not validate alone):", dict(blocked))


if __name__ == "__main__":
    main()
