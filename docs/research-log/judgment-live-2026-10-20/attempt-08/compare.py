"""Attempt 08 vs attempt 07 on the frozen items (no model calls): per turn the core call, the capability model's
calls, the questions asked and the reply's opening, beside the expectation written before attempt 01."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def turns(base: Path):
    found = {}
    for job in sorted((base / "live").glob("*/job.json")):
        meta = json.loads(job.read_text())
        for folder in sorted(job.parent.glob("t*")):
            events = [json.loads(line) for line in (folder / "events.jsonl").read_text().splitlines()] \
                if (folder / "events.jsonl").exists() else []
            latest = {e["event_type"]: e["payload"] for e in events}
            session = json.loads((folder / "session.json").read_text()) if (folder / "session.json").exists() else {}
            calls = (session.get("token_usage") or {}).get("calls", [])
            replies = [m["content"] for m in session.get("messages", []) if m["role"] == "assistant"]
            decision = latest.get("core.decision", {})
            found[(meta["item"], folder.name)] = {
                "core": decision.get("kind"), "basis": decision.get("basis"),
                "facts": [f.get("question") for f in decision.get("facts") or []],
                "check": [(c["role"], c["model"].split("/")[-1], c["status"]) for c in calls
                          if c["role"].startswith("capability")],
                "provisional": ((session.get("plan") or {}).get("decision") or {}).get("capability_check", {}) and
                ((session["plan"]["decision"]["capability_check"] or {}).get("provisional")),
                "executed": any(e["event_type"].startswith("tool.") for e in events),
                "reply": (replies[-1] if replies else "")[:300].replace("\n", " "),
                "usd": sum((c.get("cost_micro_usd") or 0) for c in calls) / 1e6,
            }
    return found


def main():
    items = {item["id"]: item for item in json.loads((HERE / "items.json").read_text())["items"]}
    before, after = turns(ROOT / "attempt-07"), turns(HERE)
    total = 0.0
    for key in sorted(after):
        item, turn = key
        expected = items[item]["expected"][int(turn[1:]) - 1] if len(items[item]["expected"]) >= int(turn[1:]) \
            else items[item]["expected"][-1]
        a, b = before.get(key, {}), after[key]
        total += b["usd"]
        mark = "MATCH" if b["core"] == expected else "differs"
        print(f"{item} {turn}: expected {expected:8} | attempt-07 {a.get('core')!s:9} | attempt-08 {b['core']!s:9} "
              f"({b['basis']}) {mark}")
        print(f"    check calls: {b['check']}  provisional={b['provisional']}  executed={b['executed']}")
        if b["facts"]:
            print(f"    questions: {b['facts']}")
        print(f"    reply: {b['reply']}")
    print(f"provider-reported cost attempt 08: US${total:.4f}")


if __name__ == "__main__":
    main()
