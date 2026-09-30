"""Pre-registered analysis for Log 288 (CC1). Written before any live trial.

Usage: python analyze.py <candidate report> ... -- <baseline report> ...

Counts, per arm and per case id, from the traced harness reports:
- narrowed: the registry match was exact on basis `registry_features` (a tag narrowed a tie);
- guidance: the final decision is `no_tool` and not executing;
- cc1_only: narrowed guidance trials that no baseline trigger would have reviewed
  (single reading, known artifact, no discourse cue in the prompt);
- reviewed: a `ResearchFraming` (hypothesis_bases) call was made;
- comparison: the final decision states >= 2 distinct registered bases;
- downgraded: the final decision was reset to `unverified_evidence` by the review;
- target: the comparison names what the case needs (see TARGETS).
"""
import collections
import gzip
import json
import re
import sys
from pathlib import Path

# The baseline discourse cue, copied from graph/hypothesis_bases.py at e85d3ba + Log 287.
_OPEN_QUESTION = re.compile(
    r"\b(?:hypothes[ie]s|explanations|alternatives?|either|whether|or|versus|vs\.?|"
    r"unclear|uncertain|undecided|compare|comparing|not sure|cannot decide|"
    r"have not decided|don't know|do not know)\b|"
    r"假設|假说|假說|還是|还是|或者|或是|不確定|不确定|不清楚|不知道|尚未決定|尚未决定",
    re.IGNORECASE,
)
TARGETS = {
    "tp-pi-vs-biostat": lambda bases: {"run_otter"} <= bases and bases & {"run_panda", "run_lioness_panda", "run_puma"},
    "tp-two-philosophies": lambda bases: {"run_otter"} <= bases and bases & {"run_panda", "run_lioness_panda", "run_puma"},
    "tp-network-vs-modules": lambda bases: "run_condor" in bases
    and bases & {"run_panda", "run_otter", "run_giraffe", "run_lioness_panda", "run_puma"},
}
SINGLE_PREFERENCE = {"ctl-objective-preference", "case2-en"}


def load(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def trial_facts(row):
    trace = row["_trace"]
    decision = trace.get("decision") or {}
    events = {}
    for event in trace.get("events", []):
        events.setdefault(event["type"], event["payload"])
    registry = events.get("routing.registry_match_completed", {})
    narrowed = registry.get("status") == "exact" and registry.get("match_basis") == "registry_features"
    guidance = decision.get("action") == "no_tool" and not decision.get("should_execute")
    readings = decision.get("outcome_hypotheses") or []
    outcome = decision.get("requested_outcome") or {}
    cue = bool(_OPEN_QUESTION.search(trace.get("prompt") or ""))
    cc1_only = narrowed and guidance and len(readings) <= 1 and outcome.get("artifact_type") != "unknown" and not cue
    reviewed = any(call.get("schema") == "ResearchFraming" for call in trace.get("calls", []))
    bases = {h["basis"] for h in decision.get("stated_hypotheses") or [] if h.get("basis") != "unsupported"}
    comparison = len(bases) >= 2
    downgraded = (decision.get("match_basis") == "unverified_evidence"
                  and "could not validate every research alternative" in (decision.get("clarification_question") or ""))
    return {
        "id": row.get("id"), "narrowed": narrowed, "guidance": guidance, "cc1_only": cc1_only, "cue": cue,
        "reviewed": reviewed, "comparison": comparison, "downgraded": downgraded, "bases": sorted(bases),
        "matched": registry.get("matched_actions") or [], "final_status": decision.get("capability_match_status"),
        "calls": len(trace.get("calls", [])),
    }


def summarize(paths, label):
    rows = [row for path in paths for row in load(path).get("results", []) if row.get("_trace")]
    facts = [trial_facts(row) for row in rows]
    by_case = collections.defaultdict(list)
    for item in facts:
        by_case[item["id"]].append(item)
    print(f"== {label}: {len(facts)} trials from {len(paths)} report(s)")
    totals = collections.Counter()
    for item in facts:
        for key in ("narrowed", "guidance", "cc1_only", "reviewed", "comparison", "downgraded"):
            totals[key] += bool(item[key])
        totals["cc1_only_reviewed"] += item["cc1_only"] and item["reviewed"]
        totals["cc1_caused_comparison"] += item["cc1_only"] and item["reviewed"] and item["comparison"]
        totals["cc1_caused_downgrade"] += item["cc1_only"] and item["reviewed"] and item["downgraded"]
        totals["calls"] += item["calls"]
    print("   totals:", dict(totals))
    target_hits = 0
    for case, items in sorted(by_case.items()):
        line = []
        for item in items:
            mark = ("N" if item["narrowed"] else "-") + ("R" if item["reviewed"] else "-") + \
                   ("C" if item["comparison"] else "-") + ("D" if item["downgraded"] else "-")
            line.append(f"{mark}:{','.join(item['bases']) or ','.join(item['matched']) or item['final_status']}")
            if case in TARGETS and item["comparison"] and TARGETS[case](set(item["bases"])):
                target_hits += 1
        print(f"   {case:28s} " + " | ".join(line))
    single = [item for case in SINGLE_PREFERENCE for item in by_case.get(case, [])]
    print("   target comparisons:", target_hits,
          "| single-preference trials:", len(single),
          "cc1-caused comparisons there:", sum(i["cc1_only"] and i["reviewed"] and i["comparison"] for i in single),
          "downgrades there:", sum(i["downgraded"] for i in single))
    return facts


if __name__ == "__main__":
    args = sys.argv[1:]
    split = args.index("--") if "--" in args else len(args)
    summarize([Path(p) for p in args[:split]], "candidate")
    if split < len(args):
        summarize([Path(p) for p in args[split + 1:]], "baseline")
