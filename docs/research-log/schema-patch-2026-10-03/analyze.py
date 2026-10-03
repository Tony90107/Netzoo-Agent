"""Pre-registered analysis for Log 325 (SP: schema-failed first passes are patched).

Usage (repository root): python docs/research-log/schema-patch-2026-10-03/analyze.py

Reads live-sp-{base,cand}-{a,b}.json(.gz). Per arm, for trials whose first pass
failed the schema on confidence or artifact_type: the second call's schema and
how the trial ended. Safety: in the candidate, every placeholder confidence is
written by a patch, or its hypothesis dropped, or the trial failed. Known
answers: ctl-condor-aggregate -> CONDOR, ctl-per-sample-tf -> LIONESS-PANDA,
case5/case10 by the blind rule.
"""
import collections
import gzip
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "preference-witness-2026-10-03"))
from replay_pw import BLIND, verdict  # noqa: E402

KNOWN = {"ctl-condor-aggregate": "run_condor", "ctl-per-sample-tf": "run_lioness_panda"}


def load(arm):
    rows = []
    for part in ("a", "b"):
        for suffix in (".json", ".json.gz"):
            path = HERE / f"live-sp-{arm}-{part}{suffix}"
            if path.exists():
                opener = gzip.open if suffix.endswith("gz") else open
                rows += json.load(opener(path, "rt"))["results"]
    return rows


def schema_failed(trace):
    for event in trace["events"]:
        if event["type"] == "routing.semantic_interpretation_rejected" and event["payload"].get("attempt") == 1:
            issues = event["payload"].get("issues", [])
            if any(("schema_validation" in i and ("confidence" in i or "artifact_type" in i))
                   or "schema_missing" in i or "schema_invalid_value" in i for i in issues):
                return True
    return False


def known(row, decision, reason):
    cid = row["id"]
    if cid in KNOWN:
        return "OK" if KNOWN[cid] in (decision.get("matched_actions") or []) else (
            "FALLBACK" if reason == "semantic_fallback" else "WRONG")
    key = cid.split("-")[0]
    return verdict(BLIND[key], decision, reason) if key in BLIND else "-"


def safety(trace):
    placeholders = next((e["payload"].get("placeholders") for e in trace["events"]
                         if e["type"] == "routing.semantic_first_pass_salvaged"), None)
    waiting = set((placeholders or {}).get("confidence", []))
    if not waiting:
        return "n/a"
    if trace["reason_code"] == "semantic_fallback":
        return "failed"
    written = set()
    for call in trace["calls"]:
        parsed = call.get("parsed") or {}
        if call.get("schema") in ("SemanticPatch", "SiblingSemanticPatch") and isinstance(parsed, dict) \
                and parsed.get("confidence") is not None:
            written.add(parsed.get("hypothesis_index", 0))
    dropped = {i for e in trace["events"] if e["type"] == "routing.schema_placeholders_unwritten"
               for i in e["payload"].get("dropped", [])}
    return "ok" if waiting <= written | dropped else f"VIOLATION waiting={sorted(waiting)} written={sorted(written)}"


def main():
    for arm in ("base", "cand"):
        rows = load(arm)
        by = collections.Counter()
        second = collections.Counter()
        ends = collections.Counter()
        known_v = collections.Counter()
        safe = collections.Counter()
        errors = 0
        for row in rows:
            trace = row["_trace"]
            errors += any(c.get("exception") for c in trace["calls"])
            decision, reason = trace["decision"], trace["reason_code"]
            known_v[(row["id"], known(row, decision, reason))] += 1
            if schema_failed(trace):
                by[row["id"]] += 1
                second[trace["calls"][1]["schema"] if len(trace["calls"]) > 1 else "none"] += 1
                ends[reason] += 1
            safe[safety(trace)] += 1
        print(f"== {arm}: {len(rows)} trials, provider errors {errors}")
        print(f"   schema-failed first passes {sum(by.values())} by prompt {dict(by)}")
        print(f"   their second call {dict(second)}; their ends {dict(ends)}")
        print(f"   placeholder safety {dict(safe)}")
        for key, n in sorted(known_v.items()):
            print(f"   {n} {key}")


if __name__ == "__main__":
    main()
