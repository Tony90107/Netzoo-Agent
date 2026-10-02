"""Log 306 offline gates: replay recorded readings (WT1) and preferences (WT2) through one code tree.

Usage: python replay_wt.py <code root> <out.json>
Run it once with the candidate tree and once with the baseline tree, then diff
the two outputs: every key whose value differs is a change made by WT1 or WT2.
Recordings are read from this repository's research log, whichever tree runs.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

RESEARCH = Path(__file__).resolve().parents[1]
CODE = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(RESEARCH / "tools"), str(CODE / "scripts")]

from traces import report_paths, traced_rows  # noqa: E402
from netzoo_agent_core.contracts.outcomes import MethodPreference, OutcomeHypothesis, RequestedOutcome  # noqa: E402
from netzoo_agent_core.graph.condition_recommender import _candidate_facts, _recommend_from_preference  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402


def main():
    context = SimpleNamespace(project_policy=ProjectPolicyLoader(CODE).load())
    paths = list(dict.fromkeys(report_paths() + sorted(RESEARCH.glob("*-2026-10-0[12]/*.json.gz"))))
    readings, preferences = {}, {}
    for _, _, row in traced_rows(paths):
        trace = row["_trace"]
        decision = trace.get("decision") or {}
        if decision.get("outcome_hypotheses"):
            key = row["id"] + " | " + json.dumps([trace["prompt"], decision["outcome_hypotheses"]], sort_keys=True)
            if key not in readings:
                match = match_semantic_request(
                    trace["prompt"], [OutcomeHypothesis.model_validate(h) for h in decision["outcome_hypotheses"]],
                    request_mode="guidance")
                readings[key] = [match.status, match.matched_actions, match.hypothesis_actions]
        started = next((e["payload"] for e in trace["events"] if e["type"] == "routing.selection_conditions_started"), None)
        for call in trace["calls"] if started else []:
            if call.get("schema") != "MethodComparisonReview":
                continue
            preference = ((call.get("raw_tool_calls") or [{}])[0].get("args") or {}).get("preference")
            if not preference:
                continue
            key = row["id"] + " | " + json.dumps([trace["prompt"], preference, started["candidate_actions"]], sort_keys=True)
            if key in preferences:
                continue
            try:
                outcome = decision.get("requested_outcome")
                result = _recommend_from_preference(
                    trace["prompt"], MethodPreference.model_validate(preference),
                    _candidate_facts(list(started["candidate_actions"]), context),
                    RequestedOutcome.model_validate(outcome) if outcome else None)
                preferences[key] = result.action if result else None
            except Exception as error:  # noqa: BLE001 - a malformed recording is reported, not fatal
                preferences[key] = f"error:{type(error).__name__}"
    Path(sys.argv[2]).write_text(json.dumps({"readings": readings, "preferences": preferences}))
    print(f"{CODE.name}: {len(readings)} readings, {len(preferences)} preferences")


if __name__ == "__main__":
    main()
