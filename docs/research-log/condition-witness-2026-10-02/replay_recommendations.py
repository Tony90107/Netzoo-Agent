"""Log 304 offline gate: recorded condition recommendations replayed through the current code.

Usage (from the repository root):
  python docs/research-log/condition-witness-2026-10-02/replay_recommendations.py

Every traced trial whose condition recommender recommended from quoted
conditions is replayed through `recommend_from_claims` with its recorded
request, claims and candidates. Prints each distinct payload whose replayed
action differs from the recorded one, with the rejection reasons.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "docs" / "research-log" / "tools"), str(ROOT / "scripts")]

from traces import report_paths, traced_rows  # noqa: E402
from netzoo_agent_core.contracts.outcomes import ConditionClaim, SelectionConditionClaims  # noqa: E402
from netzoo_agent_core.graph.condition_recommender import condition_options, recommend_from_claims  # noqa: E402


def main():
    research = ROOT / "docs" / "research-log"
    paths = list(dict.fromkeys(report_paths() + sorted(research.glob("*-2026-10-0[12]/*.json.gz"))))
    seen = {}
    for _, _, row in traced_rows(paths):
        trace = row["_trace"]
        for event in trace["events"]:
            payload = event["payload"]
            if event["type"] != "routing.selection_conditions_recommended" or not payload.get("conditions"):
                continue
            key = (trace["prompt"], tuple((c["axis"], c["value"], c["text_span"]) for c in payload["conditions"]),
                   tuple(payload["candidate_actions"]))
            seen.setdefault(key, [0, row["id"], payload["recommended_action"]])[0] += 1
    print("distinct", len(seen), "trials", sum(item[0] for item in seen.values()))
    for (prompt, conditions, candidates), (count, case, recorded) in seen.items():
        claims = SelectionConditionClaims(claims=[
            ConditionClaim(condition=f"{axis}:{value}", text_span=span) for axis, value, span in conditions])
        replayed, rejected = recommend_from_claims(prompt, claims, condition_options(list(candidates)), list(candidates))
        if (replayed and replayed.action) != recorded:
            print(f"  {count} {case} {[c[0] for c in conditions]} recorded {recorded} now "
                  f"{replayed and replayed.action} {[item['reason'] for item in rejected]}")


if __name__ == "__main__":
    main()
