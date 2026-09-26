"""Log 148 evidence grid: matcher results for legal outcomes carrying evidence.

Usage: python log148_evidence_grid.py <repo_root> <out.json>
       python log148_evidence_grid.py --diff <old.json> <new.json>

The Log 136 grid has no evidence, so the explicit-evidence branch of
`match_outcome_hypotheses` never runs there. Here every legal outcome is
matched under three evidence configurations:

- artifact:      artifact_type explicit, every other field inferred
- artifact_gran: artifact_type and granularity explicit, the rest inferred
- all:           every stated field explicit

Deterministic and offline.
"""
import itertools
import json
import sys
from pathlib import Path

CONFIGS = ("artifact", "artifact_gran", "all")


def build(root: str) -> dict:
    sys.path.insert(0, str(Path(root) / "scripts"))
    sys.path.insert(0, str(Path(root) / "docs" / "research-log"))
    import log136_outcome_grid as grid
    from netzoo_agent_core.contracts.artifact_semantics import outcome_consistency_issues
    from netzoo_agent_core.contracts.outcomes import OutcomeEvidence, OutcomeHypothesis
    from netzoo_agent_core.routing.outcome_matching import (
        RequestedOutcome, match_outcome_hypotheses, match_requested_outcome,
    )

    rows = {}
    for op, art, gran, ents, regs, tgts, inputs in itertools.product(
        grid.OPERATIONS, grid.ARTIFACTS, grid.GRANULARITIES, grid.ENTITY_SETS,
        grid.REGULATORS, grid.TARGETS, grid.INPUTS,
    ):
        fields = dict(operation=op, artifact_type=art, granularity=gran,
                      entity_types=ents, regulator_types=regs, target_types=tgts,
                      input_artifacts=inputs, selection_tags=[])
        try:
            outcome = RequestedOutcome(**fields)
        except Exception:
            continue
        if outcome_consistency_issues(outcome) or art == "unknown":
            continue
        stated = [("operation", op), ("artifact_type", art), ("granularity", gran)]
        stated += [("input_artifact", v) for v in inputs]
        stated += [("entity_type", v) for v in ents]
        stated += [("regulator_type", v) for v in regs]
        stated += [("target_type", v) for v in tgts]
        stated = [(d, v) for d, v in stated if v not in {"unknown", "not_applicable"}]
        strict = match_requested_outcome(outcome)
        for config in CONFIGS:
            explicit = {
                "artifact": {"artifact_type"},
                "artifact_gran": {"artifact_type", "granularity"},
                "all": {d for d, _ in stated},
            }[config]
            evidence = [
                OutcomeEvidence(
                    dimension=d, value=v,
                    source="explicit" if d in explicit else "inferred",
                    text_span=f"quote-{d}-{v}" if d in explicit else None,
                    rationale="grid",
                )
                for d, v in stated
            ]
            hyp = match_outcome_hypotheses(
                [OutcomeHypothesis(outcome=outcome, confidence=0.9, evidence=evidence)]
            )
            key = json.dumps({**fields, "config": config}, sort_keys=True)
            rows[key] = {
                "hyp": [hyp.status, hyp.matched_actions, hyp.hypothesis_actions],
                "strict_candidates": sorted(set(strict.hypothesis_actions) | set(strict.matched_actions)),
            }
    return rows


def diff(old_path: str, new_path: str) -> None:
    old = json.loads(Path(old_path).read_text())
    new = json.loads(Path(new_path).read_text())
    assert old.keys() == new.keys(), "grid domains differ"
    changed, widened, swapped, unresolved, outside = 0, [], [], [], []
    transitions = {}
    for key in old:
        b, c = old[key]["hyp"], new[key]["hyp"]
        if b == c:
            continue
        changed += 1
        transitions[(b[0], c[0])] = transitions.get((b[0], c[0]), 0) + 1
        before = set(b[1]) | set(b[2])
        after = set(c[1]) | set(c[2])
        if after - before:
            widened.append((key, sorted(after - before)))
        if b[0] in {"exact", "fallback"} and (c[0] not in {"exact", "fallback"} or b[1] != c[1]):
            swapped.append((key, b, c))
        strict = set(old[key]["strict_candidates"])
        if strict and (before - after) - (before - strict):
            # a removed candidate that the typed outcome itself admitted
            outside.append((key, sorted((before - after) & strict)))
    print(f"rows: {len(old)}; changed: {len(changed and old) and changed}")
    print("F-a widened candidate sets (must be 0):", len(widened))
    print("F-b resolved outcome lost or swapped (must be 0):", len(swapped))
    print("F-c removed a candidate the strict match admitted (must be 0):", len(outside))
    for t, n in sorted(transitions.items()):
        print("  transition", t, n)
    for row in (widened[:3] + swapped[:3] + outside[:3]):
        print("  example:", row)


if __name__ == "__main__":
    if sys.argv[1] == "--diff":
        diff(sys.argv[2], sys.argv[3])
    else:
        rows = build(sys.argv[1])
        Path(sys.argv[2]).write_text(json.dumps(rows, sort_keys=True))
        print("rows:", len(rows))
