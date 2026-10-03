"""Log 323 offline evidence for SH (list-valued assumptions) and FI (fold step readings).

Usage (repository root): python docs/research-log/validation-fallbacks-2026-10-03/replay_vf.py

1. SH: every recorded first-pass payload rejected for `assumptions:list_type`
   is shape-normalized and schema-validated again.
2. FI on the two Test 5 fallbacks (local sessions t10-r3/r4-test5, events
   copied into test5-fallbacks.json): the rejected interpretation is folded,
   validated and matched.
3. FI scan: every recorded SemanticInterpretation/SemanticPatch output where
   the fold would fire. Nothing calls a model.
"""
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "docs" / "research-log" / "activity-witness-2026-10-03")]
from replay_ta import rows  # noqa: E402
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis, SemanticInterpretation  # noqa: E402
from netzoo_agent_core.graph.semantic_shape import normalize_semantic_shape  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses  # noqa: E402
from netzoo_agent_core.interpretation.terminal_goal_fold import fold_intermediate_readings  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402


def sh():
    outcome = collections.Counter()
    for row in rows():
        trace = row["_trace"]
        for event in trace.get("events", []):
            payload = event["payload"]
            if (event["type"] != "routing.semantic_interpretation_rejected" or payload.get("attempt") != 1
                    or not any("assumptions:list_type" in issue for issue in payload.get("issues", []))):
                continue
            normalized, notes = normalize_semantic_shape(payload.get("provider_payload"))
            try:
                SemanticInterpretation.model_validate(normalized)
                outcome[("schema valid", bool(notes))] += 1
            except ValueError as error:
                missing = [str(e["loc"][-1]) for e in getattr(error, "errors", lambda: [])()]
                outcome[("still invalid: " + ",".join(sorted(set(missing))), bool(notes))] += 1
    print("SH, first passes rejected for assumptions:list_type ->", dict(outcome))


def fi_test5():
    for case in json.loads((HERE / "test5-fallbacks.json").read_text()):
        interpretation = SemanticInterpretation.model_validate(case["rejected_interpretation"])
        before = validate_outcome_hypotheses(case["task"], [h.model_copy(deep=True) for h in interpretation.outcome_hypotheses],
                                             interpretation.request_mode)
        folded, notes = fold_intermediate_readings(case["task"], interpretation)
        after = validate_outcome_hypotheses(case["task"], [h.model_copy(deep=True) for h in folded.outcome_hypotheses],
                                            folded.request_mode)
        match = match_semantic_request(case["task"], folded.outcome_hypotheses, request_mode=folded.request_mode)
        print(f"FI {case['session']}: before valid={before.valid} {list(before.issues)}; folded={notes}; "
              f"after valid={after.valid} {list(after.issues)}; match {match.status} {match.matched_actions}")


def fi_scan():
    fired, seen = collections.Counter(), 0
    for row in rows():
        trace = row["_trace"]
        for call in trace.get("calls", []):
            if call.get("schema") != "SemanticInterpretation" or not isinstance(call.get("parsed"), dict):
                continue
            try:
                interpretation = SemanticInterpretation.model_validate(call["parsed"])
            except ValueError:
                continue
            seen += 1
            _, notes = fold_intermediate_readings(trace["prompt"], interpretation)
            if notes:
                fired[(trace["prompt"][:90], tuple(h.outcome.artifact_type for h in interpretation.outcome_hypotheses))] += 1
    print(f"FI scan: recorded first passes {seen}; fold fires {sum(fired.values())}")
    for key, n in fired.most_common():
        print(f"  {n:3d} {key}")


if __name__ == "__main__":
    sh()
    fi_test5()
    fi_scan()
