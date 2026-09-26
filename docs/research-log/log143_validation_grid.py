"""Log 143 validation grid: evidence-requirement issues for every legal outcome.

Usage: python log143_validation_grid.py <repo_root> <out.json>
       python log143_validation_grid.py --diff <old.json> <new.json>

Each legal outcome from the Log 136 grid domain gets a quoted, grounded
evidence entry for every field except entity types, which are left without
evidence, so every entity-evidence requirement the validator imposes shows up
as an issue. Deterministic and offline.
"""
import itertools
import json
import sys
from pathlib import Path


def build(root: str) -> dict:
    sys.path.insert(0, str(Path(root) / "scripts"))
    sys.path.insert(0, str(Path(root) / "docs" / "research-log"))
    import log136_outcome_grid as grid
    from netzoo_agent_core.contracts.artifact_semantics import outcome_consistency_issues
    from netzoo_agent_core.contracts.outcomes import OutcomeEvidence, OutcomeHypothesis
    from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses
    from netzoo_agent_core.routing.outcome_matching import RequestedOutcome

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
        if outcome_consistency_issues(outcome):
            continue
        quoted = [("operation", op), ("artifact_type", art), ("granularity", gran)]
        quoted += [("input_artifact", v) for v in inputs]
        quoted += [("regulator_type", v) for v in regs]
        quoted += [("target_type", v) for v in tgts]
        quoted = [(d, v) for d, v in quoted if v not in {"unknown", "not_applicable"}]
        if __import__("os").environ.get("GRID_OMIT_OPERATION"):
            quoted = [(d, v) for d, v in quoted if d != "operation"]
        spans = [f"quote-{d}-{v}" for d, v in quoted]
        evidence = [
            OutcomeEvidence(dimension=d, value=v, source="explicit", text_span=span,
                            rationale="grid")
            for (d, v), span in zip(quoted, spans)
        ]
        task = " ".join(spans) or "grid request"
        hypothesis = OutcomeHypothesis(outcome=outcome, confidence=0.9, evidence=evidence)
        mode = __import__("os").environ.get("GRID_REQUEST_MODE")
        result = (validate_outcome_hypotheses(task, [hypothesis], mode) if mode
                  else validate_outcome_hypotheses(task, [hypothesis]))
        rows[json.dumps(fields, sort_keys=True)] = sorted(result.issues)
    return rows


def diff(old_path: str, new_path: str) -> None:
    old = json.loads(Path(old_path).read_text())
    new = json.loads(Path(new_path).read_text())
    assert old.keys() == new.keys(), "grid domains differ"
    added, removed_kinds, violations, changed = [], {}, [], 0
    for key in old:
        before, after = set(old[key]), set(new[key])
        if before == after:
            continue
        changed += 1
        if after - before:
            added.append((key, sorted(after - before)))
        outcome = json.loads(key)
        for issue in before - after:
            kind = issue.split(".", 1)[1]
            removed_kinds[kind] = removed_kinds.get(kind, 0) + 1
            if __import__("os").environ.get("GRID_ALLOW") == "operation":
                allowed = kind.startswith("missing_evidence:operation=")
                if not allowed:
                    violations.append((key, kind))
                continue
            allowed = (
                (kind == "missing_evidence:entity_type=sample"
                 and outcome["granularity"] == "sample_specific")
                or (kind == "missing_evidence:entity_type=gene"
                    and outcome["artifact_type"] in {"coexpression_network", "pvalue_matrix"})
            )
            if not allowed:
                violations.append((key, kind))
    print(f"outcomes: {len(old)}; changed: {changed}")
    print("M-a added issues (must be 0):", len(added))
    print("M-b removals outside the declared kinds (must be 0):", len(violations))
    for kind, count in sorted(removed_kinds.items()):
        print("  removed", kind, count)
    for row in (added[:3] + violations[:3]):
        print("  example:", row)


if __name__ == "__main__":
    if sys.argv[1] == "--diff":
        diff(sys.argv[2], sys.argv[3])
    else:
        rows = build(sys.argv[1])
        Path(sys.argv[2]).write_text(json.dumps(rows, sort_keys=True))
        print("outcomes:", len(rows))
