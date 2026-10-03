"""Pre-registered analysis for Log 332 (CW: a sample-clustering reading needs clustering words).

Usage (repository root): python docs/research-log/cluster-witness-2026-10-03/analyze.py

Reads live-cw-{base,cand}-{a,b}.json(.gz). Gates as declared in Log 332:
- validity: no provider exception in either arm;
- soundness: candidate test4-en final decisions with a sample_cluster_assignment
  reading beside another reading = 0;
- effect: baseline >= 1 such decision and candidate 0 (baseline 0: judged by replay);
- controls: test5-en and hist-expression-then-mutation-en exact SAMBAR,
  candidate >= baseline - 1 each;
- test4-en validation fallbacks: candidate <= baseline + 1.
"""
import collections
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTROLS = ("test5-en", "hist-expression-then-mutation-en")


def load(arm):
    rows = []
    for part in ("a", "b"):
        for suffix in (".json", ".json.gz"):
            path = HERE / f"live-cw-{arm}-{part}{suffix}"
            if path.exists():
                opener = gzip.open if suffix.endswith("gz") else open
                rows += json.load(opener(path, "rt"))["results"]
    return rows


def misread(decision):
    artifacts = [h["outcome"]["artifact_type"] for h in decision.get("outcome_hypotheses") or []]
    return len(artifacts) >= 2 and "sample_cluster_assignment" in artifacts


def main():
    summary = {}
    for arm in ("base", "cand"):
        rows = load(arm)
        errors = sum(any(c.get("exception") for c in r["_trace"]["calls"]) for r in rows)
        test4 = [r["_trace"] for r in rows if r["id"] == "test4-en"]
        dropped = sum(any(e["type"] == "routing.unwitnessed_readings_dropped"
                          and "sample_cluster_assignment" in e["payload"].get("artifact_types", [])
                          for e in t["events"]) for t in test4)
        controls = collections.Counter(
            r["id"] for r in rows if r["id"] in CONTROLS
            and r["_trace"]["decision"].get("capability_match_status") == "exact"
            and r["_trace"]["decision"].get("matched_actions") == ["run_sambar"])
        summary[arm] = dict(
            trials=len(rows), errors=errors, test4=len(test4),
            misread=sum(misread(t["decision"]) for t in test4), cw_fired=dropped,
            fallback=sum(t.get("reason_code") == "semantic_fallback" for t in test4),
            controls={cid: f"{controls[cid]}/{sum(r['id'] == cid for r in rows)}" for cid in CONTROLS})
        print(arm, json.dumps(summary[arm]))
        for t in test4:
            d = t["decision"]
            print("   test4", d.get("capability_match_status"),
                  [h["outcome"]["artifact_type"] for h in d.get("outcome_hypotheses") or []],
                  d.get("hypothesis_actions") or d.get("matched_actions"), t.get("reason_code"))
    base, cand = summary["base"], summary["cand"]
    gates = {
        "validity": base["errors"] == 0 and cand["errors"] == 0,
        "soundness": cand["misread"] == 0,
        "effect": ("by replay" if base["misread"] == 0 else base["misread"] >= 1 and cand["misread"] == 0),
        "controls": all(int(cand["controls"][c].split("/")[0]) >= int(base["controls"][c].split("/")[0]) - 1
                        for c in CONTROLS),
        "fallbacks": cand["fallback"] <= base["fallback"] + 1,
    }
    print("gates", json.dumps(gates))


if __name__ == "__main__":
    main()
