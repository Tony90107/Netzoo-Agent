"""Grade traced blind-test reports against expectations.json.

Usage: python docs/research-log/blind/score_blind.py <report.json[.gz]> [...]

Verdicts per trial, as in Logs 179 and 204:
- FALLBACK: reason code `semantic_fallback`.
- OK(exact): an exact (or fallback) match on an accepted workflow.
- OK(recommended): a tie whose advisory recommendation is an accepted workflow.
- OK(no tool): case 10, nothing matched and nothing authorized.
- PARTIAL(candidates): a tie that holds an accepted workflow but recommends none.
- WRONG: anything else, including a forbidden workflow.
LEAK marks `should_execute` or an action other than `no_tool`. For ambiguous
decisions the deterministic reply is re-rendered offline and checked for the
reply notes a case requires (case 10: the assumption note and folder discovery).
"""
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
from traces import ROOT, load_report  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

EXPECT = json.loads((HERE / "expectations.json").read_text(encoding="utf-8"))
NOTES = {
    "assumption": "does not say what the network should connect",
    "discovery": "validate for an input role",
}
POLICY = ProjectPolicyLoader(ROOT).load()


def verdict(case: dict, trace: dict) -> str:
    decision = trace["decision"]
    events = {}
    for event in trace.get("events", []):
        events.setdefault(event["type"], event["payload"])
    registry = events.get("routing.registry_match_completed", {})
    status = registry.get("status")
    matched = set(registry.get("matched_actions") or [])
    candidates = set(registry.get("hypothesis_actions") or [])
    recommended = (decision.get("advisory_recommendation") or {}).get("action")
    accept, forbid = set(case.get("accept", [])), set(case.get("forbid", []))
    if trace.get("reason_code") == "semantic_fallback":
        return "FALLBACK"
    if matched & forbid or recommended in forbid:
        return "WRONG"
    if case.get("no_tool"):
        return "OK(no tool)" if not matched and decision.get("action") == "no_tool" else "WRONG"
    if status in ("exact", "fallback") and matched & accept:
        return "OK(exact)"
    if recommended in accept:
        return "OK(recommended)"
    if status == "ambiguous" and candidates & accept:
        return "PARTIAL(candidates)"
    return "WRONG"


def missing_notes(case: dict, trace: dict) -> list[str]:
    wanted = case.get("reply_notes", [])
    if not wanted or trace["decision"].get("capability_match_status") != "ambiguous":
        return []
    reply = render_outcome_clarification(TaskDecision.model_validate(trace["decision"]), POLICY,
                                         task=trace.get("prompt", "")) or ""
    return [note for note in wanted if NOTES[note] not in reply]


def main(paths: list[str]) -> None:
    for path in paths:
        by_case = collections.defaultdict(list); totals = collections.Counter(); leaks = 0
        for row in load_report(path)["results"]:
            trace = row.get("_trace")
            if not trace:
                continue
            key = row["id"].split("-")[0]
            case = EXPECT[key]
            decision = trace["decision"]
            result = verdict(case, trace)
            leak = bool(decision.get("should_execute")) or decision.get("action") != "no_tool"
            leaks += leak
            totals[result.split("(")[0]] += 1
            shown = decision.get("matched_actions") or decision.get("hypothesis_actions") or []
            recommended = (decision.get("advisory_recommendation") or {}).get("action")
            notes = missing_notes(case, trace)
            by_case[key].append(
                f"{result} {decision.get('capability_match_status')} {shown}"
                + (f" rec={recommended}" if recommended else "") + (" LEAK" if leak else "")
                + (f" missing={notes}" if notes else "")
            )
        print(f"== {Path(path).name}")
        for key in sorted(by_case, key=lambda item: int(item[4:])):
            print(f"  {key}: " + " | ".join(by_case[key]))
        print(f"  totals {dict(totals)}  leaks {leaks}")


if __name__ == "__main__":
    main(sys.argv[1:])
