"""P1/P2 live check: each session's call, questions, obligations and reply, beside what the replay expected.

Flags in the reply: the old canned line ("not matched to any registered workflow"), a "no registered workflow
produces/can give" claim (said only beside a registry-wide reason or verified limits since P2 -- each is read by
hand), and the layer-2 sentences. Writes REPLIES.md with every reply in full for reading.

Usage: python3 analyze.py
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = "not matched to any registered workflow"
CLAIM = ("No registered workflow produces", "no registered workflow produces", "No registered workflow can give")
LAYER2 = "I couldn't match"


def turn(item: dict) -> dict:
    folder = HERE / "live" / "p12live" / f"hb-p12live-{item['id']}-1" / "t1"
    if not (folder / "session.json").exists():
        return {"missing": True}
    session = json.loads((folder / "session.json").read_text())
    events = [json.loads(line) for line in (folder / "events.jsonl").read_text().splitlines() if line.strip()] \
        if (folder / "events.jsonl").exists() else []
    core = next((e["payload"] for e in reversed(events) if e.get("event_type") == "core.decision"), {})
    reply = next((m["content"] for m in reversed(session.get("messages", [])) if m.get("role") == "assistant"), "")
    calls = (session.get("token_usage") or {}).get("calls", [])
    return {"kind": core.get("kind"), "basis": core.get("basis"), "partial": core.get("partial"),
            "run_allowed": core.get("run_allowed"), "asked": [f.get("question") for f in core.get("facts") or []],
            "obligations": [(o["source"], o["status"], bool(o["asked_as"]), o["question"])
                            for o in (core.get("evidence") or {}).get("obligations") or []],
            "old_line": OLD in reply, "claims": [c for c in CLAIM if c in reply], "layer2": reply.count(LAYER2),
            "cost_usd": sum(c.get("cost_micro_usd") or 0 for c in calls) / 1e6, "reply": reply}


def main():
    items = json.loads((HERE / "items.json").read_text())["items"]
    rows, text = [], ["# P1/P2 live check: replies\n"]
    for item in items:
        found = turn(item)
        rows.append((item, found))
        if found.get("missing"):
            print(f"{item['id']:4} MISSING")
            continue
        call = f"{found['kind']}{'(p)' if found['partial'] else ''}/{found['basis']}"
        print(f"{item['id']:4} {call:36} run_allowed={found['run_allowed']!s:5} expect: {item['replay_expect']:32} "
              f"old_line={found['old_line']!s:5} claims={found['claims']} layer2={found['layer2']} "
              f"${found['cost_usd']:.4f}")
        for question in found["asked"]:
            print(f"      asks: {question}")
        for source, status, bound, question in found["obligations"]:
            print(f"      obligation: {source:9} {status:7} {'bound ' if bound else ''}| {question[:90]}")
        text += [f"## {item['id']} ({item['source']}) -- {item['check']}", "", f"Call: {call}; run_allowed "
                 f"{found['run_allowed']}; replay expected: {item['replay_expect']}", "", "```", found["reply"], "```", ""]
    total = sum(found.get("cost_usd", 0) for _, found in rows)
    print(f"sessions {sum(not f.get('missing') for _, f in rows)}/18; cost US${total:.4f}")
    (HERE / "REPLIES.md").write_text("\n".join(text))


if __name__ == "__main__":
    main()
