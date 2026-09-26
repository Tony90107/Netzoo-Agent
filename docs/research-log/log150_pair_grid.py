"""Log 150 pair grid: matcher results for two-hypothesis interpretations.

Usage: python log150_pair_grid.py <repo_root> <out.json>
       python log150_pair_grid.py --diff <old.json> <new.json>

Pairs of legal, artifact-known outcomes from the Log 136 grid domain whose
strict match admits at least one workflow. A fixed-seed sample of pairs with
different artifact types, plus a control sample with the same artifact type.
Deterministic and offline.
"""
import itertools
import json
import random
import sys
from pathlib import Path

SAMPLE = 6000


def build(root: str) -> dict:
    sys.path.insert(0, str(Path(root) / "scripts"))
    sys.path.insert(0, str(Path(root) / "docs" / "research-log"))
    import log136_outcome_grid as grid
    from netzoo_agent_core.contracts.artifact_semantics import outcome_consistency_issues
    from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis
    from netzoo_agent_core.routing.outcome_matching import (
        RequestedOutcome, match_outcome_hypotheses, match_requested_outcome,
    )

    pool = []
    for op, art, gran, ents, regs, tgts, inputs in itertools.product(
        ["infer", "analyze"], grid.ARTIFACTS, ["aggregate", "sample_specific"],
        grid.ENTITY_SETS, grid.REGULATORS, grid.TARGETS, grid.INPUTS,
    ):
        if art == "unknown":
            continue
        fields = dict(operation=op, artifact_type=art, granularity=gran,
                      entity_types=ents, regulator_types=regs, target_types=tgts,
                      input_artifacts=inputs, selection_tags=[])
        try:
            outcome = RequestedOutcome(**fields)
        except Exception:
            continue
        if outcome_consistency_issues(outcome):
            continue
        strict = match_requested_outcome(outcome)
        if strict.matched_actions or strict.hypothesis_actions:
            pool.append(fields)
    rng = random.Random(150)
    different, same = [], []
    while len(different) < SAMPLE or len(same) < SAMPLE // 3:
        a, b = rng.sample(pool, 2)
        (different if a["artifact_type"] != b["artifact_type"] else same).append((a, b))
    pairs = [("different", p) for p in different[:SAMPLE]] + [("same", p) for p in same[:SAMPLE // 3]]
    rows = {}
    for kind, (a, b) in pairs:
        hyps = [
            OutcomeHypothesis(outcome=RequestedOutcome(**a), confidence=0.9),
            OutcomeHypothesis(outcome=RequestedOutcome(**b), confidence=0.8),
        ]
        m = match_outcome_hypotheses(hyps)
        rows[json.dumps({"kind": kind, "a": a, "b": b}, sort_keys=True)] = [
            m.status, m.matched_actions, m.hypothesis_actions,
        ]
    return {"pool": len(pool), "rows": rows}


def diff(old_path: str, new_path: str) -> None:
    old = json.loads(Path(old_path).read_text())
    new = json.loads(Path(new_path).read_text())
    assert old["rows"].keys() == new["rows"].keys(), "pair domains differ"
    print("pool:", old["pool"], "pairs:", len(old["rows"]))
    changed_same, lost, executable, transitions = [], [], [], {}
    changed = 0
    for key, b in old["rows"].items():
        c = new["rows"][key]
        if b == c:
            continue
        changed += 1
        kind = json.loads(key)["kind"]
        transitions[(kind, b[0], c[0])] = transitions.get((kind, b[0], c[0]), 0) + 1
        if kind == "same":
            changed_same.append(key)
        if (set(b[1]) | set(b[2])) - (set(c[1]) | set(c[2])):
            lost.append((key, b, c))
        if c[0] == "exact":
            executable.append((key, b, c))
    print("changed:", changed)
    print("P-a same-artifact pairs changed (must be 0):", len(changed_same))
    print("P-b a previously offered workflow disappeared (must be 0):", len(lost))
    print("P-c changed rows that are now exact (must be 0):", len(executable))
    for t, n in sorted(transitions.items()):
        print("  transition", t, n)
    for row in (lost[:2] + executable[:2]):
        print("  example:", row)


if __name__ == "__main__":
    if sys.argv[1] == "--diff":
        diff(sys.argv[2], sys.argv[3])
    else:
        rows = build(sys.argv[1])
        Path(sys.argv[2]).write_text(json.dumps(rows, sort_keys=True))
        print("pool:", rows["pool"], "pairs:", len(rows["rows"]))
