"""CC-c3 of Log 288: new WRONG verdicts caused by CC1, read from the final decision.

Log 288 declared CC-c3 but `analyze.py` does not compute it. This script was
written after slot 1 ran and before slots 2-3; it reuses `score_blind.verdict`
unchanged, once on the registry event (as `score_blind.py` grades, before the
hypothesis review) and once on the final decision. Pure JSON, runs anywhere.

Usage: python final_verdicts.py <candidate report> ... -- <baseline report> ...

A candidate trial counts toward CC-c3 when CC1 alone sent it to the review
(`cc1_only` and reviewed, as in analyze.py), its final verdict is WRONG while
its pre-review verdict was not, and no baseline trial of the same case ends
WRONG. The looser count (final WRONG after a CC1 review, whatever came before)
is printed too. The three two-philosophy prompts have no answer key: they are
graded only by CC-d in analyze.py and listed here as "n/a".
"""
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from analyze import load, trial_facts  # noqa: E402

EXPECT = json.loads((HERE.parent / "blind" / "expectations.json").read_text(encoding="utf-8"))
EXPECT["ctl"] = {"accept": ["run_otter"]}  # ctl-objective-preference: expected exact run_otter


def verdict(case, status, matched, candidates, recommended, action, reason_code):
    """`score_blind.verdict`, with its inputs passed in."""
    accept, forbid = set(case.get("accept", [])), set(case.get("forbid", []))
    if reason_code == "semantic_fallback":
        return "FALLBACK"
    if matched & forbid or recommended in forbid:
        return "WRONG"
    if case.get("no_tool"):
        return "OK(no tool)" if not matched and action == "no_tool" else "WRONG"
    if status in ("exact", "fallback") and matched & accept:
        return "OK(exact)"
    if recommended in accept:
        return "OK(recommended)"
    if status == "ambiguous" and candidates & accept:
        return "PARTIAL(candidates)"
    return "WRONG"


def grade(row):
    trace = row["_trace"]
    case = EXPECT.get(row["id"].split("-")[0])
    facts = trial_facts(row)
    decision = trace.get("decision") or {}
    shown = decision.get("matched_actions") or decision.get("hypothesis_actions") or []
    if case is None:
        return {**facts, "pre": "n/a", "final": "n/a", "shown": shown}
    events = {}
    for event in trace.get("events", []):
        events.setdefault(event["type"], event["payload"])
    registry = events.get("routing.registry_match_completed", {})
    recommended = (decision.get("advisory_recommendation") or {}).get("action")
    common = (recommended, decision.get("action"), trace.get("reason_code"))
    pre = verdict(case, registry.get("status"), set(registry.get("matched_actions") or []),
                  set(registry.get("hypothesis_actions") or []), *common)
    final = verdict(case, decision.get("capability_match_status"), set(decision.get("matched_actions") or []),
                    set(decision.get("hypothesis_actions") or []), *common)
    return {**facts, "pre": pre, "final": final, "shown": shown}


def arm(paths):
    rows = [row for path in paths for row in load(path).get("results", []) if row.get("_trace")]
    return [grade(row) for row in rows]


def main(args):
    split = args.index("--") if "--" in args else len(args)
    candidate, baseline = arm(args[:split]), arm(args[split + 1:])
    baseline_wrong = {item["id"] for item in baseline if item["final"] == "WRONG"}
    for label, items in (("candidate", candidate), ("baseline", baseline)):
        by_case = collections.defaultdict(list)
        for item in items:
            by_case[item["id"]].append(item)
        print(f"== {label}: {len(items)} trials; final verdicts",
              dict(collections.Counter(item["final"].split("(")[0] for item in items)))
        for case, rows in sorted(by_case.items()):
            print(f"   {case:28s} " + " | ".join(
                f"{'*' if r['cc1_only'] and r['reviewed'] else ' '}{r['pre']}->{r['final']}"
                f" {r['final_status']} {r['shown']}" for r in rows))
    reviewed = [item for item in candidate if item["cc1_only"] and item["reviewed"]]
    loose = [item for item in reviewed if item["final"] == "WRONG"]
    strict = [item for item in loose if item["pre"] != "WRONG" and item["id"] not in baseline_wrong]
    print("CC1-reviewed candidate trials (*):", len(reviewed),
          "| final WRONG among them:", len(loose), [item["id"] for item in loose],
          "| CC-c3 (new WRONG, not WRONG before the review, not WRONG in baseline):", len(strict),
          [item["id"] for item in strict])


if __name__ == "__main__":
    main(sys.argv[1:])
