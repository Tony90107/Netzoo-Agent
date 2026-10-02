"""Log 313 exploration: readings whose artifact_type no quote supports, beside a reading whose artifact is quoted.

Usage (repository root): python docs/research-log/unquoted-sibling-2026-10-02/scan_siblings.py

For every distinct recorded final decision (all traced reports, void ones
skipped) with two or more readings, a reading is "quoted" when some
artifact_type evidence for its own artifact carries a text span found in the
request, and "unquoted" otherwise. Prints each prompt where both kinds occur,
with the match before and after dropping the unquoted readings (prototype).
"""
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402


def quoted(task, hypothesis):
    return any(item.dimension == "artifact_type" and item.value == hypothesis.outcome.artifact_type
               and item.text_span and item.text_span.casefold() in task.casefold()
               for item in hypothesis.evidence)


def traces():
    for path in sorted({*ROOT.glob("docs/research-log/**/live-*.json"), *ROOT.glob("docs/research-log/**/live-*.json.gz")}):
        if ".provider-error" in path.name or ".unpaired" in path.name:
            continue
        opener = gzip.open if path.suffix == ".gz" else open
        try:
            with opener(path, "rt", encoding="utf-8") as handle:
                report = json.load(handle)
        except (OSError, ValueError):
            continue
        for row in report.get("results", []) if isinstance(report, dict) else []:
            trace = row.get("_trace") if isinstance(row, dict) else None
            if trace and trace.get("decision"):
                yield row.get("id"), trace


def main():
    seen, rows, trials = set(), defaultdict(Counter), Counter()
    multi = single_unquoted = 0
    for case, trace in traces():
        task, raw = trace["prompt"], trace["decision"].get("outcome_hypotheses") or []
        if not raw:
            continue
        hypotheses = [OutcomeHypothesis.model_validate(item) for item in raw]
        marks = [quoted(task, h) for h in hypotheses]
        if len(hypotheses) == 1:
            single_unquoted += not marks[0]
            continue
        multi += 1
        if not (any(marks) and not all(marks)):
            continue
        trials[(case, task)] += 1
        key = json.dumps([task, raw], sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        kept = [h for h, mark in zip(hypotheses, marks) if mark]
        before = match_semantic_request(task, hypotheses, request_mode="guidance")
        after = match_semantic_request(task, kept, request_mode="guidance")
        dropped = tuple(h.outcome.artifact_type for h, mark in zip(hypotheses, marks) if not mark)
        rows[(case, task)][(dropped, before.status, tuple(before.matched_actions or before.hypothesis_actions),
                            after.status, tuple(after.matched_actions or after.hypothesis_actions))] += 1
    print(f"multi-reading trials: {multi}; single-reading trials with an unquoted artifact (untouched): {single_unquoted}")
    print(f"mixed quoted/unquoted: {len(seen)} distinct decisions, {sum(trials.values())} trials, {len(rows)} prompts")
    for (case, task), outcomes in sorted(rows.items(), key=lambda item: -trials[item[0]]):
        print(f"- {case} ({trials[(case, task)]} trials) | {' '.join(task.split())[:150]}")
        for (dropped, bs, ba, as_, aa), count in outcomes.most_common():
            print(f"    {count}x drop {list(dropped)}: {bs} {list(ba)} -> {as_} {list(aa)}")


if __name__ == "__main__":
    main()
