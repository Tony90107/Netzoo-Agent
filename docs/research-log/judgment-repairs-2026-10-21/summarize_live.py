"""Summarize captured CLI judgments and usage without rerunning any model."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    calls, rounds = {}, []
    for name, folder in [("initial", HERE), ("verification-02", HERE / "verification-02"),
                         ("verification-03", HERE / "verification-03"),
                         ("verification-04", HERE / "verification-04"),
                         ("verification-05", HERE / "verification-05")]:
        jobs = folder / "live-jobs.json"
        if not jobs.exists():
            continue
        rows, execution = [], []
        for job in json.loads(jobs.read_text()):
            source = folder / "live" / job["session"] / "t1/events.jsonl"
            events = [json.loads(line) for line in source.read_text().splitlines()] if source.exists() else []
            for event in events:
                if event["event_type"] == "llm.completed":
                    calls[event["payload"]["call_id"]] = event["payload"]
                if event["event_type"].startswith("tool."):
                    execution.append({"id": job["id"], "type": event["event_type"]})
            core = job.get("core") or {}
            rows.append({"id": job["id"], "expected": job["expected"], "kind": core.get("kind"),
                         "basis": core.get("basis"), "correct_kind": core.get("kind") == job["expected"],
                         "questions": [fact["question"] for fact in core.get("facts", [])],
                         "reasons": [reason for part in core.get("declined", []) for reason in part["reasons"]],
                         "declined_lines": [part["line"] for part in core.get("declined", [])],
                         "codes": job.get("codes"), "source": str(source.relative_to(HERE))})
        finished = folder / "live-finished.json"
        rounds.append({"name": name, "sessions": len(rows), "correct_kinds": sum(r["correct_kind"] for r in rows),
                       "finished": json.loads(finished.read_text()) if finished.exists() else None,
                       "rows": rows, "actual_tool_events": execution})
    usage = {"unique_calls": len(calls), "models": dict(Counter(call["model"] for call in calls.values())),
             "cost_micro_usd": sum(call.get("cost_micro_usd") or 0 for call in calls.values()),
             "cost_provenance": dict(Counter(call.get("cost_provenance") for call in calls.values())),
             "input_tokens": sum(call.get("input_tokens", 0) for call in calls.values()),
             "output_tokens": sum(call.get("output_tokens", 0) for call in calls.values())}
    result = {"rounds": rounds, "usage": usage, "fresh_blind_test": False}
    (HERE / "live-summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"rounds": [{k: r[k] for k in ["name", "sessions", "correct_kinds"]} for r in rounds],
                      "usage": usage}))


if __name__ == "__main__":
    main()
