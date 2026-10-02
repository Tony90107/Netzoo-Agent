"""Log 315 offline evidence: recorded condition recommendations under a per-value cohort_size witness.

Usage (repository root): python docs/research-log/cohort-witness-2026-10-02/replay_cs.py [--tree]

User decision (2026-09-27 #3, reconfirmed 2026-10-02): the agent never maps a
sample count to "a handful" or "dozens or more"; only the user's own words do.
Prototype CS: a cohort_size claim is rejected unless the request states that
value in words (`COHORT_WITNESS`); a bare number is not a witness. With --tree
the repository's `recommend_from_claims` alone is used (after CS is
implemented, the two printouts must match).
"""
import gzip
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from netzoo_agent_core.contracts.outcomes import ConditionClaim, SelectionConditionClaims  # noqa: E402
from netzoo_agent_core.graph.condition_recommender import condition_options, recommend_from_claims  # noqa: E402

_UNITS = r"(?:samples?|patients?|individuals?|subjects?|donors?|participants?|people|mice|animals?|replicates?|tumou?rs?|cases?|biops(?:y|ies))"
COHORT_WITNESS = {
    "few": (
        r"\bhandful\b|\b(?:a\s+|very\s+|only\s+(?:a\s+)?)?few\s+(?:[\w-]+\s+){0,2}" + _UNITS + r"\b|"
        r"\bsmall\s+(?:number\s+of\s+" + _UNITS + r"|cohort|sample\s+size|study)\b|"
        r"\blimited\s+(?:number\s+of\s+)?" + _UNITS + r"\b|\bonly\s+a\s+couple\b|"
        r"少數|少量(?:的)?(?:樣本|病人|患者)|幾個(?:病人|患者|樣本)|幾位|小樣本|樣本(?:數|量)?(?:很|太)?少"
    ),
    "many": (
        r"\b(?:dozens|hundreds|thousands)\b|\blarge\s+(?:number\s+of\s+" + _UNITS + r"|cohort|sample\s+size|study)\b|"
        r"\bmany\s+(?:[\w-]+\s+){0,2}" + _UNITS + r"\b|\blarge[- ]scale\s+cohort\b|"
        r"數十|數百|上百|上千|大量(?:的)?(?:樣本|病人|患者)|大型(?:世代|隊列|族群)|樣本(?:數|量)?(?:很)?多"
    ),
}


def prototype(prompt, claims, options, candidates):
    kept, rejected = [], []
    for claim in claims.claims:
        axis, _, value = claim.condition.partition(":")
        if axis == "cohort_size" and not re.search(COHORT_WITNESS.get(value, r"(?!)"), prompt, re.I):
            rejected.append({"condition": claim.condition, "reason": "condition_not_in_request"})
        else:
            kept.append(claim)
    recommendation, more = recommend_from_claims(prompt, SelectionConditionClaims(claims=kept), options, candidates)
    return recommendation, rejected + more


def traces():
    for path in sorted({*ROOT.glob("docs/research-log/**/live-*.json"), *ROOT.glob("docs/research-log/**/live-*.json.gz")}):
        if ".provider-error" in path.name or ".unpaired" in path.name:
            continue
        opener = gzip.open if path.suffix == ".gz" else open
        try:
            with opener(path, "rt", encoding="utf-8") as handle:
                report = json.load(handle)
        except (OSError, ValueError):
            continue
        for row in report.get("results", []) if isinstance(report, dict) else []:
            trace = row.get("_trace") if isinstance(row, dict) else None
            if trace:
                yield row.get("id"), trace


def main():
    seen, changed = Counter(), Counter()
    for case, trace in traces():
        for event in trace["events"]:
            payload = event["payload"]
            if event["type"] != "routing.selection_conditions_recommended" or not payload.get("conditions"):
                continue
            conditions = tuple((c["axis"], c["value"], c["text_span"]) for c in payload["conditions"])
            key = (case, trace["prompt"], conditions, tuple(payload["candidate_actions"]), payload["recommended_action"])
            seen[key] += 1
    for (case, prompt, conditions, candidates, recorded), count in seen.items():
        claims = SelectionConditionClaims(claims=[
            ConditionClaim(condition=f"{axis}:{value}", text_span=span) for axis, value, span in conditions])
        options = condition_options(list(candidates))
        if "--tree" in sys.argv:
            replayed, rejected = recommend_from_claims(prompt, claims, options, list(candidates))
        else:
            replayed, rejected = prototype(prompt, claims, options, list(candidates))
        now = replayed and replayed.action
        if now != recorded:
            changed[(case, recorded, now, tuple(c[0] + ":" + c[1] for c in conditions),
                     tuple(sorted({r["reason"] for r in rejected})))] += count
    print("distinct recorded recommendations:", len(seen), "trials:", sum(seen.values()))
    print("changed:", sum(changed.values()), "trials")
    for (case, recorded, now, conditions, reasons), count in changed.most_common():
        print(f"  {count:3d}x {case}: {recorded} -> {now} {list(conditions)} {list(reasons)}")


if __name__ == "__main__":
    main()
