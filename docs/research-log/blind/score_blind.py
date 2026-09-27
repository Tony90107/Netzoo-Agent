"""Grade traced blind-test reports against expectations.json.

Usage: python docs/research-log/blind/score_blind.py <report.json[.gz]> [...]

Verdicts per trial, as in Logs 179 and 204:
- FALLBACK: reason code `semantic_fallback`.
- OK(exact): an exact (or fallback) match on an accepted workflow.
- OK(recommended): a tie whose advisory recommendation is an accepted workflow.
- OK(no tool): case 10, nothing matched and nothing authorized.
- PARTIAL(candidates): a tie that holds an accepted workflow but recommends none.
- WRONG: anything else, including a forbidden workflow.
LEAK marks `should_execute` or an action other than `no_tool`. The deterministic
reply is re-rendered offline and checked for the reply notes a case requires
(case 10, on ambiguous decisions: the assumption note and folder discovery;
case 4, on every decision since Log 219: both per-sample readings, LIONESS-PANDA
wiring and GIRAFFE activity, whatever was chosen -- its "one path" is an exact
match, rendered through the response node).
Since Log 223 each trial also lists the concerns its reply answers
(`concerns=`), and a case's `concerns` in expectations.json names those the
request states: `missed=` are expected but unanswered, `extra=` answered but
not expected. Neither changes the verdict.
"""
import collections
import json
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
from traces import ROOT, load_report  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from langchain_core.messages import HumanMessage  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.graph.response import respond  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

EXPECT = json.loads((HERE / "expectations.json").read_text(encoding="utf-8"))
NOTES = {  # every string must appear
    "assumption": ("does not say what the network should connect",),
    "discovery": ("validate for an input role",),
    "both_readings": ("LIONESS-PANDA", "GIRAFFE", "activity"),
}
# Checked on every decision; the others only on ambiguous ones, as in Logs 179-204.
ANY_STATUS = {"both_readings"}
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


def reply_for(trace: dict) -> str:
    decision = TaskDecision.model_validate(trace["decision"])
    task = trace.get("prompt", "")
    if decision.capability_match_status == "ambiguous":
        return render_outcome_clarification(decision, POLICY, task=task) or ""
    plan = WorkflowPlan(workflow="NO-TOOL", objective="Blind scoring", decision=decision.model_dump(),
                        status="respond_only")
    state = {"messages": [HumanMessage(content=task)], "decision": decision.model_dump(),
             "plan": plan.model_dump(), "tool_results": []}
    return str(respond(SimpleNamespace(project_policy=POLICY, response_llm=None), state)["messages"][0].content)


def missing_notes(case: dict, trace: dict) -> list[str]:
    ambiguous = trace["decision"].get("capability_match_status") == "ambiguous"
    wanted = [note for note in case.get("reply_notes", []) if ambiguous or note in ANY_STATUS]
    if not wanted or trace.get("reason_code") == "semantic_fallback":
        return []
    reply = reply_for(trace)
    return [note for note in wanted if not all(part in reply for part in NOTES[note])]


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
            addressed = sorted({item["concern"] for item in decision.get("addressed_concerns") or []})
            expected = set(case.get("concerns", {}).get(next(iter(sorted(set(shown))), ""), []))
            missed = sorted(expected - set(addressed))
            extra = sorted(set(addressed) - expected)
            for concern in addressed:
                totals[f"concern:{concern}"] += 1
            by_case[key].append(
                f"{result} {decision.get('capability_match_status')} {shown}"
                + (f" rec={recommended}" if recommended else "") + (" LEAK" if leak else "")
                + (f" missing={notes}" if notes else "")
                + (f" concerns={addressed}" if addressed else "")
                + (f" missed={missed}" if missed and result.startswith("OK(exact)") else "")
                + (f" extra={extra}" if extra else "")
            )
        print(f"== {Path(path).name}")
        for key in sorted(by_case, key=lambda item: int(item[4:])):
            print(f"  {key}: " + " | ".join(by_case[key]))
        print(f"  totals {dict(totals)}  leaks {leaks}")


if __name__ == "__main__":
    main(sys.argv[1:])
