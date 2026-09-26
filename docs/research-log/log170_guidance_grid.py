"""Log 170 guidance grid: match_semantic_request results for evidenced outcomes.

Usage: python log170_guidance_grid.py <repo_root> <out.json>
       python log170_guidance_grid.py --diff <old.json> <new.json>

Every legal, artifact-known outcome with a concrete operation is matched in
guidance and in execute mode, with every stated field cited explicitly
(the Log 148 `all` configuration). Deterministic and offline.
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
    from netzoo_agent_core.routing.outcome_matching import RequestedOutcome, match_semantic_request

    rows = {}
    for op, art, gran, ents, regs, tgts, inputs in itertools.product(
        ["infer", "analyze"], grid.ARTIFACTS, grid.GRANULARITIES, grid.ENTITY_SETS,
        grid.REGULATORS, grid.TARGETS, grid.INPUTS,
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
        stated = [("operation", op), ("artifact_type", art), ("granularity", gran)]
        stated += [("input_artifact", v) for v in inputs]
        stated += [("entity_type", v) for v in ents]
        stated += [("regulator_type", v) for v in regs]
        stated += [("target_type", v) for v in tgts]
        stated = [(d, v) for d, v in stated if v not in {"unknown", "not_applicable"}]
        evidence = [
            OutcomeEvidence(dimension=d, value=v, source="explicit",
                            text_span=f"quote-{d}-{v}", rationale="grid")
            for d, v in stated
        ]
        for mode in ("guidance", "execute"):
            hyp = OutcomeHypothesis(outcome=outcome, confidence=0.9, evidence=evidence)
            m = match_semantic_request("", [hyp], request_mode=mode)
            rows[json.dumps({**fields, "mode": mode}, sort_keys=True)] = [
                m.status, m.matched_actions, m.hypothesis_actions,
            ]
    return rows


def diff(old_path: str, new_path: str) -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    from workflow_registry import OUTPUT_CAPABILITIES

    old = json.loads(Path(old_path).read_text())
    new = json.loads(Path(new_path).read_text())
    assert old.keys() == new.keys(), "grid domains differ"
    execute_changed, swapped, bad_admission, transitions, changed = [], [], [], {}, 0
    for key in old:
        b, c = old[key], new[key]
        if b == c:
            continue
        changed += 1
        row = json.loads(key)
        transitions[(row["mode"], b[0], c[0])] = transitions.get((row["mode"], b[0], c[0]), 0) + 1
        if row["mode"] == "execute":
            execute_changed.append(key)
        if c[0] == "exact" and b[0] == "exact" and b[1] != c[1]:
            swapped.append((key, b, c))
        before = set(b[1]) | set(b[2])
        after = set(c[1]) | set(c[2])
        for action in after - before:
            if OUTPUT_CAPABILITIES[action].operation == row["operation"]:
                bad_admission.append((key, action))
    print("rows:", len(old), "changed:", changed)
    print("G-a execute-mode rows changed (must be 0):", len(execute_changed))
    print("G-b exact tool swaps (must be 0):", len(swapped))
    print("G-c newly admitted with the same operation as the evidence (must be 0):", len(bad_admission))
    for t, n in sorted(transitions.items()):
        print("  transition", t, n)
    for row in (execute_changed[:2] + swapped[:2] + bad_admission[:2]):
        print("  example:", row)


if __name__ == "__main__":
    if sys.argv[1] == "--diff":
        diff(sys.argv[2], sys.argv[3])
    else:
        rows = build(sys.argv[1])
        Path(sys.argv[2]).write_text(json.dumps(rows, sort_keys=True))
        print("rows:", len(rows))
