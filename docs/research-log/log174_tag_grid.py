"""Log 174 tag grid: tag discrimination for every legal outcome and registered tag.

Usage: python log174_tag_grid.py <repo_root> <out.json>
       python log174_tag_grid.py --diff <old.json> <new.json>

Each legal, artifact-known outcome from the Log 136 grid domain is matched
with exactly one registered selection tag, declared in the outcome and backed
by a grounded explicit quote. Deterministic and offline.
"""
import itertools
import json
import sys
from pathlib import Path

RESTATING = {"coexpression", "multi_omic_network", "sample_specific", "aggregate_network",
             "mirna_regulation", "tf_gene_regulation"}


def build(root: str) -> dict:
    sys.path.insert(0, str(Path(root) / "scripts"))
    sys.path.insert(0, str(Path(root) / "docs" / "research-log"))
    import log136_outcome_grid as grid
    from workflow_registry import OUTPUT_CAPABILITIES
    from netzoo_agent_core.contracts.artifact_semantics import outcome_consistency_issues
    from netzoo_agent_core.contracts.outcomes import OutcomeEvidence, OutcomeHypothesis
    from netzoo_agent_core.routing.outcome_matching import RequestedOutcome, match_outcome_hypotheses

    tags = sorted({t for c in OUTPUT_CAPABILITIES.values() for t in c.selection_tags})
    rows = {}
    for op, art, gran, ents, regs, tgts in itertools.product(
        ["infer", "analyze", "unknown"], grid.ARTIFACTS, grid.GRANULARITIES,
        [[], ["gene"], ["tf", "gene"], ["mirna", "gene"], ["tf", "mirna", "gene"]],
        grid.REGULATORS, grid.TARGETS,
    ):
        if art == "unknown":
            continue
        base = dict(operation=op, artifact_type=art, granularity=gran,
                    entity_types=ents, regulator_types=regs, target_types=tgts,
                    input_artifacts=["expression_matrix"])
        try:
            probe = RequestedOutcome(**base, selection_tags=[])
        except Exception:
            continue
        if outcome_consistency_issues(probe):
            continue
        for tag in tags:
            span = f"quote-{tag}"
            try:
                outcome = RequestedOutcome(**base, selection_tags=[tag])
            except Exception:
                continue
            evidence = [OutcomeEvidence(dimension="selection_tag", value=tag, source="explicit",
                                        text_span=span, rationale="grid")]
            m = match_outcome_hypotheses(
                [OutcomeHypothesis(outcome=outcome, confidence=0.9, evidence=evidence)],
                user_task=span,
            )
            rows[json.dumps({**base, "tag": tag}, sort_keys=True)] = [
                m.status, m.matched_actions, m.hypothesis_actions,
            ]
    return rows


def diff(old_path: str, new_path: str) -> None:
    old = json.loads(Path(old_path).read_text())
    new = json.loads(Path(new_path).read_text())
    assert old.keys() == new.keys(), "grid domains differ"
    changed, outside, swapped, transitions = 0, [], [], {}
    for key in old:
        b, c = old[key], new[key]
        if b == c:
            continue
        changed += 1
        row = json.loads(key)
        transitions[(row["tag"], b[0], c[0])] = transitions.get((row["tag"], b[0], c[0]), 0) + 1
        if row["tag"] not in RESTATING:
            outside.append(key)
        if c[0] == "exact" and b[0] == "exact" and b[1] != c[1]:
            swapped.append((key, b, c))
        if (set(b[1]) | set(b[2])) - (set(c[1]) | set(c[2])):
            swapped.append((key, "lost a candidate", b, c))
    print("rows:", len(old), "changed:", changed)
    print("T-a changes with a method (non-restating) tag (must be 0):", len(outside))
    print("T-b tool swaps or lost candidates (must be 0):", len(swapped))
    for t, n in sorted(transitions.items()):
        print("  transition", t, n)
    for row in (outside[:2] + swapped[:2]):
        print("  example:", row)


if __name__ == "__main__":
    if sys.argv[1] == "--diff":
        diff(sys.argv[2], sys.argv[3])
    else:
        rows = build(sys.argv[1])
        Path(sys.argv[2]).write_text(json.dumps(rows, sort_keys=True))
        print("rows:", len(rows))
