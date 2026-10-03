"""Pre-registered analysis for Log 327 (MG: keep the modules half).

Usage (repository root): python docs/research-log/two-step-modules-2026-10-03/analyze.py

Reads live-mg-{base,cand}-{a,b}.json(.gz).
- pf: "both halves" = the final decision keeps a community_assignment reading
  and offers LIONESS-PANDA or LIONESS-PUMA. Candidate replies are also rendered
  (current code) and must name LIONESS and CONDOR.
- FF / II-C positives: the gap shape of Log 295 (unsupported, ["granularity"],
  CONDOR as the alternative).
- Controls: ctl-condor-aggregate -> CONDOR, ctl-per-sample-tf and
  role-tf-ss-en -> LIONESS-PANDA, as exact matches.
"""
import collections
import gzip
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
CONTROLS = {"ctl-condor-aggregate": "run_condor", "ctl-per-sample-tf": "run_lioness_panda",
            "role-tf-ss-en": "run_lioness_panda"}
POSITIVES = ("rep-individual-communities", "ii-modules-for-each-patient")


def load(arm):
    rows = []
    for part in ("a", "b"):
        for suffix in (".json", ".json.gz"):
            path = HERE / f"live-mg-{arm}-{part}{suffix}"
            if path.exists():
                opener = gzip.open if suffix.endswith("gz") else open
                rows += json.load(opener(path, "rt"))["results"]
    return rows


def both_halves(decision):
    artifacts = {h["outcome"]["artifact_type"] for h in decision.get("outcome_hypotheses") or []}
    offered = set(decision.get("hypothesis_actions") or []) | set(decision.get("matched_actions") or [])
    return "community_assignment" in artifacts and bool(offered & {"run_lioness_panda", "run_lioness_puma"})


def gap_shape(decision):
    return (decision.get("capability_match_status") == "unsupported"
            and decision.get("mismatch_dimensions") == ["granularity"]
            and "run_condor" in (decision.get("alternative_actions") or []))


if __name__ == "__main__":
    import replay_mg
    from netzoo_agent_core.contracts import TaskDecision

    for arm in ("base", "cand"):
        rows = load(arm)
        errors = sum(any(c.get("exception") for c in r["_trace"]["calls"]) for r in rows)
        counts = collections.Counter()
        print(f"== {arm}: {len(rows)} trials, provider errors {errors}")
        for row in rows:
            trace, cid = row["_trace"], row["id"]
            decision = trace["decision"]
            if cid == "pf-patient-specific-modules":
                halves = both_halves(decision)
                counts["pf both halves"] += halves
                counts["pf trials"] += 1
                if arm == "cand" and halves:
                    _, text, _ = replay_mg.answer(trace["prompt"], TaskDecision.model_validate(decision))
                    counts["pf rendered with LIONESS and CONDOR"] += ("LIONESS" in text and "CONDOR" in text)
                print(f"   pf {decision.get('capability_match_status')} {decision.get('hypothesis_actions')} "
                      f"{[h['outcome']['artifact_type'] for h in decision.get('outcome_hypotheses') or []]} "
                      f"{trace['reason_code']}")
            elif cid in POSITIVES:
                counts["positives gap shape"] += gap_shape(decision)
            elif cid in CONTROLS:
                ok = decision.get("capability_match_status") == "exact" and \
                    CONTROLS[cid] in (decision.get("matched_actions") or [])
                counts[f"control {cid} exact"] += ok
        print("   " + json.dumps(dict(counts)))
