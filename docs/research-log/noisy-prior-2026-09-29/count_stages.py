"""Log 257 structural counters over the interleaved live reports.

Usage: python count_stages.py live-*.json[.gz]

K-c: a trial is eligible when its goal review (hypothesis_bases) succeeded with
no accepted hypothesis and its decision is a tie the condition recommender
owns (method, divergent-reading or same-subject). Every eligible trial must
also contain a selection_conditions call. Scored counts are descriptive only.
"""
import collections
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.graph.condition_recommender import (  # noqa: E402
    _same_subject_choice, is_divergent_reading_tie, is_method_tie,
)


def framing(trace):
    for event in trace.get("events", []):
        if event["type"] == "routing.hypothesis_bases_matched":
            return event["payload"]
    return None


def main(paths):
    for path in paths:
        opener = gzip.open if path.endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8") as handle:
            rows = json.load(handle)["results"]
        counts = collections.Counter()
        for row in rows:
            trace = row["_trace"]
            decision = TaskDecision.model_validate(trace["decision"])
            roles = row["call_roles"]
            review = framing(trace)
            owned = is_method_tie(decision) or is_divergent_reading_tie(decision) or _same_subject_choice(decision)
            no_comparison = review is not None and not review["accepted"]
            counts["trials"] += 1
            counts["call_limit_errors"] += sum(e.startswith("call_limit") for e in row["errors"])
            if review is not None:
                counts["review_ran"] += 1
            if no_comparison and owned:
                counts["eligible"] += 1
                counts["eligible_with_conditions"] += "selection_conditions" in roles
            if "selection_conditions" in roles:
                counts["conditions_ran"] += 1
            if row["id"].startswith("noisy-prior"):
                counts["noisy_trials"] += 1
                counts["noisy_gap"] += decision.advisory_capability_gap is not None
                counts["noisy_granularity_question"] += "aggregate or sample-specific" in row.get("answer", "")
                counts["noisy_puma_named"] += "PUMA" in row.get("answer", "")
            if row["id"].startswith("case3"):
                counts["case3_trials"] += 1
                rec = decision.advisory_recommendation
                counts["case3_bonobo_recommended"] += bool(rec and rec.action == "run_bonobo")
        print(Path(path).name, dict(counts))


if __name__ == "__main__":
    main(sys.argv[1:])
