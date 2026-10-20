"""Summarize the frozen real CLI captures; no model calls or regenerated replies."""
from pathlib import Path
from collections import Counter
import json

ROOT = Path(__file__).resolve().parent

def analyze():
    calls = {}
    rows = []
    counts = Counter()
    for attempt, base in [(1, ROOT), (2, ROOT / "attempt-02")]:
        for job in sorted((base / "live").glob("*/job.json")):
            meta = json.loads(job.read_text())
            for folder in sorted(job.parent.glob("t*")):
                source = folder / "events.jsonl"
                if not source.exists():
                    source = folder / "trace.events.jsonl"
                events = [json.loads(line) for line in source.read_text().splitlines()] if source.exists() else []
                for event in events:
                    if event["event_type"] == "llm.completed":
                        calls[event["payload"]["call_id"]] = event["payload"]
                latest = {}
                for event in events:
                    latest[event["event_type"]] = event["payload"]
                session_path = folder / "session.json"
                session = json.loads(session_path.read_text()) if session_path.exists() else {}
                assistant = [m["content"] for m in session.get("messages", []) if m["role"] == "assistant"]
                decision = latest.get("core.decision", {})
                plan = session.get("plan") or {}
                row = {"attempt": attempt, "item":meta["item"], "turn":folder.name,
                       "exit":json.loads((folder / "manifest.json").read_text())["exit"],
                       "decision":decision,"view":latest.get("core.view"),
                       "plan":{"workflow":plan.get("workflow"),"status":plan.get("status"),
                               "steps":plan.get("steps"),"missing_inputs":plan.get("missing_inputs")},
                       "reply":assistant[-1] if assistant else None,
                       "actual_execution_events":[e["event_type"] for e in events
                           if e["event_type"].startswith("tool.")],
                       "capability_failures":[{"type":e["payload"].get("error_type"),
                                               "attempt":e["payload"].get("attempt")}
                            for e in events if e["event_type"] == "routing.capability_check_failed"]}
                rows.append(row)
                if attempt == 2:
                    counts[decision.get("kind", "NO_DECISION")] += 1
    usage={"unique_calls":len(calls),"models":dict(Counter(c["model"] for c in calls.values())),
           "actual_cost_micro_usd":sum(c["cost_micro_usd"] or 0 for c in calls.values() if c["cost_provenance"] == "actual"),
           "estimated_cost_micro_usd":sum(c["cost_micro_usd"] or 0 for c in calls.values() if c["cost_provenance"] == "estimated"),
           "unavailable_cost_calls":sum(c["cost_provenance"] == "unavailable" for c in calls.values()),
           "input_tokens":sum(c["input_tokens"] for c in calls.values()),
           "output_tokens":sum(c["output_tokens"] for c in calls.values())}
    result={"rows":rows,"attempt_02_core_counts":dict(counts),"usage_all_attempts":usage}
    (ROOT / "analysis.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"attempt_02_core_counts":dict(counts),"usage_all_attempts":usage}))
    for r in rows:
        if r["attempt"]==2:
            print(r["item"],r["turn"],r["exit"],r["decision"].get("kind"),r["plan"]["status"])

if __name__ == "__main__":
    analyze()
