"""Log 309 offline evidence: what the per-unit rule (prototype) changes in recorded readings and discriminator picks.

Usage (repository root): python docs/research-log/scale-unit-2026-10-02/replay_sw.py [--tree]

With --tree, SW1 is the repository's `drop_unnamed_scale` and
`relax_unstated_scale(..., scale_dropped=True)` instead of the prototype; the
Log 309 supplement compares the two printouts.

1. Readings: every recorded final reading (decision.outcome_hypotheses) is
   matched by `match_semantic_request` as recorded and again with SW1 applied
   (a request naming no unit keeps no per-sample claim: granularity
   sample_specific -> unknown, tags sample_specific /
   leave_one_out_network_inference dropped, with their evidence). As DD3 does,
   a resulting tie of one cohort workflow and only its per-sample extensions
   becomes fallback on the cohort workflow. Distinct (prompt, readings) pairs
   are counted once.
2. Discriminator: every recorded accepted discriminator pick whose tags
   include a per-sample tag, in a request naming no unit (SW2 would reject it).
"""
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(HERE), str(ROOT / "scripts")]

from scan_unit import per_unit_mention  # noqa: E402
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis  # noqa: E402
from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402

TREE = "--tree" in sys.argv


def tree_route(task, hypotheses):
    from netzoo_agent_core.routing.scale_relaxation import drop_unnamed_scale, relax_unstated_scale
    reading = SemanticInterpretation.model_construct(request_mode="guidance", semantic_goal="",
                                                     outcome_hypotheses=hypotheses)
    dropped, changed = drop_unnamed_scale(task, reading)
    match = match_semantic_request(task, dropped.outcome_hypotheses, request_mode="guidance")
    match = relax_unstated_scale(task, dropped, match, scale_dropped=bool(changed))[1]
    actions = tuple(dict.fromkeys(match.hypothesis_actions))
    if match.status == "fallback":
        # The prototype's fold keeps the tie it folded; report the same tie.
        actions = tuple(dict.fromkeys(match_semantic_request(
            task, dropped.outcome_hypotheses, request_mode="guidance").hypothesis_actions))
    return bool(changed), (match.status, tuple(match.matched_actions), actions)

PER_SAMPLE_TAGS = {"sample_specific", "leave_one_out_network_inference"}


def demote(hypothesis):
    outcome = hypothesis.outcome
    tags = [tag for tag in outcome.selection_tags if tag not in PER_SAMPLE_TAGS]
    if outcome.granularity != "sample_specific" and tags == list(outcome.selection_tags):
        return hypothesis
    return hypothesis.model_copy(update={
        "outcome": outcome.model_copy(update={
            "granularity": "unknown" if outcome.granularity == "sample_specific" else outcome.granularity,
            "selection_tags": tags,
        }),
        "evidence": [item for item in hypothesis.evidence
                     if not (item.dimension == "granularity" and item.value == "sample_specific")
                     and not (item.dimension == "selection_tag" and item.value in PER_SAMPLE_TAGS)],
    })


def fold(match):
    """DD3 generalized: {base} + its per-sample extensions only -> fallback base."""
    actions = list(dict.fromkeys(match.hypothesis_actions))
    if match.status != "ambiguous" or len(actions) < 2:
        return match.status, tuple(match.matched_actions), tuple(actions)
    bases = [a for a in actions if not OUTPUT_CAPABILITIES[a].guidance_predecessors]
    if len(bases) == 1 and all(OUTPUT_CAPABILITIES[a].guidance_predecessors == (bases[0],)
                               for a in actions if a != bases[0]):
        return "fallback", (bases[0],), tuple(actions)
    return match.status, tuple(match.matched_actions), tuple(actions)


def reports():
    for path in sorted({*ROOT.glob("docs/research-log/**/live-*.json"), *ROOT.glob("docs/research-log/**/live-*.json.gz")}):
        if ".provider-error" in path.name or ".unpaired" in path.name:  # void by rule, never analyzed
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
    seen, changed, trials = set(), {}, Counter()
    picks = Counter()
    for case, trace in reports():
        task, decision = trace["prompt"], trace["decision"]
        unnamed = per_unit_mention(task) is None
        for event in trace.get("events", []):
            if event["type"] == "routing.semantic_discriminator_accepted" and unnamed:
                tags = set(event["payload"].get("selection_tags") or ())
                if tags & PER_SAMPLE_TAGS:
                    picks[(case, tuple(sorted(tags)), tuple(event["payload"].get("matched_actions") or ()))] += 1
        raw = decision.get("outcome_hypotheses") or []
        if not raw or not unnamed:
            continue
        key = json.dumps([task, raw], sort_keys=True)
        hypotheses = [OutcomeHypothesis.model_validate(item) for item in raw]
        demoted = [demote(item) for item in hypotheses]
        if TREE:
            changed_here, after = tree_route(task, hypotheses)
            if not changed_here:
                continue
        elif demoted == hypotheses:
            continue
        trials[(case, task)] += 1
        if key in seen:
            continue
        seen.add(key)
        before = match_semantic_request(task, hypotheses, request_mode="guidance")
        if not TREE:
            after = fold(match_semantic_request(task, demoted, request_mode="guidance"))
        changed.setdefault((case, task), Counter())[(
            before.status, tuple(before.matched_actions), tuple(before.hypothesis_actions), *after)] += 1
    print("readings changed by SW1:", len(seen), "distinct, in", sum(trials.values()), "trials,",
          len(changed), "prompts")
    for (case, task), outcomes in sorted(changed.items(), key=lambda item: -trials[item[0]]):
        print(f"- {case} ({trials[(case, task)]} trials) | {' '.join(task.split())[:150]}")
        for (bs, bm, bh, as_, am, ah), count in outcomes.most_common():
            print(f"    {count}x  {bs} {list(bm) or list(bh)}  ->  {as_} {list(am) or list(ah)}")
    print("recorded discriminator picks SW2 would reject:", sum(picks.values()))
    for key, count in picks.most_common():
        print("   ", count, key)


if __name__ == "__main__":
    main()
