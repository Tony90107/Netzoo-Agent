"""Log 136 generated outcome grid: record matcher results for every legal outcome.

Usage: python log136_outcome_grid.py <out.json>
       python log136_outcome_grid.py --diff <baseline.json> <candidate.json>

Deterministic and offline: no provider calls. A "legal" outcome is one that
constructs and has no `outcome_consistency_issues`.
"""
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts.artifact_semantics import outcome_consistency_issues  # noqa: E402
from netzoo_agent_core.routing.clarification_planner import plan_clarification  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import (  # noqa: E402
    OutcomeHypothesis,
    RequestedOutcome,
    match_outcome_hypotheses,
    match_requested_outcome,
)

OPERATIONS = ["infer", "analyze", "unknown"]
ARTIFACTS = list(RequestedOutcome.model_fields["artifact_type"].annotation.__args__)
GRANULARITIES = ["aggregate", "sample_specific", "not_applicable", "unknown"]
ENTITY_POOL = ["tf", "mirna", "gene", "sample", "pathway"]
ENTITY_SETS = [[]] + [
    list(combo) for size in (1, 2, 3) for combo in itertools.combinations(ENTITY_POOL, size)
] + [["unknown"]]
REGULATORS = [[], ["tf"], ["mirna"], ["tf", "mirna"]]
TARGETS = [[], ["gene"]]
INPUTS = [[], ["expression_matrix"], ["mutation_matrix"]]


def _key(o: dict) -> str:
    return json.dumps(o, sort_keys=True)


def _record(outcome: RequestedOutcome) -> dict:
    strict = match_requested_outcome(outcome)
    hyp = match_outcome_hypotheses(
        [OutcomeHypothesis(outcome=outcome, confidence=0.9, evidence=[], assumptions=[])]
    )
    candidates = list(dict.fromkeys([*hyp.hypothesis_actions, *strict.hypothesis_actions]))
    plan = plan_clarification(candidates, outcomes=[outcome]) if len(candidates) > 1 else None
    return {
        "strict": [strict.status, strict.matched_actions, strict.hypothesis_actions,
                   strict.alternative_actions, strict.mismatch_dimensions,
                   strict.clarification_question],
        "hyp": [hyp.status, hyp.matched_actions, hyp.hypothesis_actions,
                hyp.clarification_question],
        "plan_dimension": plan.dimension if plan else None,
    }


def build() -> dict:
    rows = {}
    for op, art, gran, ents, regs, tgts, inputs in itertools.product(
        OPERATIONS, ARTIFACTS, GRANULARITIES, ENTITY_SETS, REGULATORS, TARGETS, INPUTS
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
        rows[_key(fields)] = _record(outcome)
    return rows


def diff(base_path: str, cand_path: str) -> None:
    base = json.loads(Path(base_path).read_text())
    cand = json.loads(Path(cand_path).read_text())
    assert base.keys() == cand.keys(), "grid domains differ"
    changed = [k for k in base if base[k] != cand[k]]
    # The clarification question text (strict[5], hyp[3]) is planner output
    # embedded in the match; it is judged by T-b, not by S-a/S-b.
    def _matcher(row):
        return row["strict"][:5], row["hyp"][:3]
    matcher_changed = [k for k in changed if _matcher(base[k]) != _matcher(cand[k])]
    plan_only = [k for k in changed if k not in matcher_changed]
    print(f"legal outcomes: {len(base)}; changed: {len(changed)} "
          f"(matcher {len(matcher_changed)}, planner-only {len(plan_only)})")

    # S-a: every matcher change must be a sample_specific outcome that names `sample`.
    s_a = [k for k in matcher_changed
           if not (json.loads(k)["granularity"] == "sample_specific"
                   and "sample" in json.loads(k)["entity_types"])]
    # S-b: no resolution loss, no tool swap.
    resolved = {"exact", "fallback"}
    s_b = []
    transitions = {}
    for k in matcher_changed:
        for part in ("strict", "hyp"):
            b, c = base[k][part], cand[k][part]
            transitions[(part, b[0], c[0])] = transitions.get((part, b[0], c[0]), 0) + 1
            if b[0] in resolved and (c[0] not in resolved or b[1] != c[1]):
                s_b.append((k, part, b[:3], c[:3]))
    print("S-a violations:", len(s_a))
    print("S-b violations:", len(s_b))
    for t, n in sorted(transitions.items()):
        print("  transition", t, n)

    # T-b: a planner question may change only away from a dimension the outcome resolved.
    t_b = []
    dim_moves = {}
    for k in changed:
        b, c = base[k]["plan_dimension"], cand[k]["plan_dimension"]
        if b == c:
            continue
        dim_moves[(b, c)] = dim_moves.get((b, c), 0) + 1
        if k in matcher_changed:
            continue  # candidate set itself changed; covered by S-a/S-b
        o = json.loads(k)
        resolved_dim = (
            (b == "artifact_type" and o["artifact_type"] != "unknown")
            or (b == "granularity" and o["granularity"] in {"aggregate", "sample_specific"})
        )
        if not resolved_dim:
            t_b.append((k, b, c))
    print("T-b violations:", len(t_b))
    for t, n in sorted(dim_moves.items(), key=str):
        print("  plan dimension", t, n)
    for item in (s_a[:3], s_b[:3], t_b[:3]):
        for row in item:
            print("  example:", row)


if __name__ == "__main__":
    if sys.argv[1] == "--diff":
        diff(sys.argv[2], sys.argv[3])
    else:
        rows = build()
        Path(sys.argv[1]).write_text(json.dumps(rows, sort_keys=True))
        print("legal outcomes:", len(rows))
