"""Score the live check (RESULTS-LIVE.md): per conversation, each turn's call, check failures from the enum limit,
budget refusals of the check model's calls, provisional checks and the final against the item's expected call.

Usage: python3 score_live.py TAG
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_live  # noqa: E402

CHECK_ROLES = ("capability_check", "capability_reread", "capability_second_opinion", "capability_condition_check")


def turn_facts(turn: Path) -> dict:
    found = {"call": None, "enum_400": 0, "blocked": [], "provisional": False, "second_opinion": None}
    for trace in sorted(turn.glob("trace-*.jsonl")):
        for line in trace.read_text().splitlines():
            row = json.loads(line)
            kind, payload = row.get("event_type"), row.get("payload") or {}
            if kind == "core.decision":
                found["call"] = f"{payload.get('kind')}/{payload.get('basis')}"
            elif kind == "routing.capability_check_failed" and "enum values" in payload.get("error_message", ""):
                found["enum_400"] += 1
            elif kind == "budget.blocked" and payload.get("role") in CHECK_ROLES:
                found["blocked"].append(payload["role"])
            elif kind == "routing.capability_check_provisional":
                found["provisional"] = True
            elif kind == "routing.capability_second_opinion":
                found["second_opinion"] = "answered" if payload.get("answers") is not None else "none"
    return found


def main():
    tag = sys.argv[1]
    items = {i["id"]: i for i in run_live.items()}
    rows = []
    for job in sorted((HERE / "live" / tag).glob("*/job.json")):
        record = json.loads(job.read_text())
        turns = [turn_facts(t) for t in sorted(job.parent.glob("t*")) if t.is_dir()]
        final = (turns[-1]["call"] or "None/None").split("/")[0] if turns else None
        want = run_live.expected(items[record["item"]], record["sent"])
        rows.append({"item": record["item"], "sent": record["sent"], "turns": turns, "final": final, "expected": want,
                     "right": final == want})
    (HERE / f"score-{tag}.json").write_text(json.dumps(rows, indent=1))
    for r in rows:
        print(f"{r['item']:4} expected {r['expected']:8} final {r['final']!s:9} {'RIGHT' if r['right'] else 'wrong'} | "
              + " -> ".join(f"{t['call']}" + (f" ENUM400x{t['enum_400']}" if t["enum_400"] else "")
                             + (f" BLOCKED{t['blocked']}" if t["blocked"] else "") + (" PROV" if t["provisional"] else "")
                             for t in r["turns"]))
    print("enum 400s:", sum(t["enum_400"] for r in rows for t in r["turns"]),
          "| check-model blocks:", sum(len(t["blocked"]) for r in rows for t in r["turns"]),
          "| provisional:", sum(t["provisional"] for r in rows for t in r["turns"]),
          "| UNCHECKED finals:", sum(r["final"] == "UNCHECKED" for r in rows),
          "| right:", sum(r["right"] for r in rows), "of", len(rows))


if __name__ == "__main__":
    main()
