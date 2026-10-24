"""Harness repair P5 error attribution (ATTRIBUTION.md), no model calls: evidence for every h7 session E (round 1,
129acb11) or E' (round 2, 5d4a19e3) got wrong -- the gold, each turn's message, call and reply opening, and the
capability check's reading of that turn from the recorded trace.

Usage: python3 evidence_h7.py OUT.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
P5 = HERE.parent / "p5"
sys.path.insert(0, str(P5))
sys.path.insert(0, str(HERE.parents[3] / "scripts"))

from score_p5 import turns  # noqa: E402

RUNS = (("p5r1", "E"), ("p5r2", "E2"))


def _names(keys) -> list[str]:
    from netzoo_agent_core.capability_sheet import entry

    out = []
    for key in keys or []:
        try:
            out.append(f"{key} ({entry(key).workflow})")
        except Exception:  # noqa: BLE001
            out.append(key)
    return out


def checked(turn: Path) -> dict | None:
    """The turn's capability check as recorded (the last `routing.capability_checked`), summarised."""
    check = None
    for trace in sorted(turn.glob("trace-*.jsonl")):
        for line in trace.read_text().splitlines():
            if '"routing.capability_checked"' in line:
                row = json.loads(line)
                if row.get("event_type") == "routing.capability_checked":
                    check = (row.get("payload") or {}).get("check")
    if check is None:
        return None
    return {"requirements": [{k: v for k, v in {
        "kind": r.get("kind"), "quote": r.get("quote"), "status": r.get("status"),
        "credited": _names(r.get("delivered_by")), "near_miss": _names(r.get("not_by")), "limits": r.get("limits"),
        "violations": r.get("violations"), "unknown_quote": r.get("unknown_quote"), "depends_on": r.get("depends_on"),
        "outcomes": {k: _names(v) for k, v in (r.get("outcomes") or {}).items()}}.items() if v not in (None, "", [], {})}
        for r in check.get("requirements") or []],
        "unknowns": check.get("unknowns"), "unchecked": check.get("unchecked"),
        "flags": {f: check.get(f) for f in ("unavailable", "provisional", "gap_unconfirmed", "full_gap") if check.get(f)}}


def main(out: str):
    data = json.loads((HERE.parent / "h7" / "items.json").read_text())
    known = {item["id"]: item for item in data["single"] + data["multi"]}
    rows = []
    for tag, system in RUNS:
        scored = {r["item"]: r for r in json.loads((P5 / f"score-{tag}.json").read_text())["rows"]
                  if r["system"] == system}
        for item_id, result in sorted(scored.items()):
            if result["success"]:
                continue
            item = known[item_id]
            sid = f"hb-{tag}-{item_id}-{system}-1"
            found = []
            for t in turns(P5 / "live" / tag / sid):
                core = t["core"] or {}
                found.append({"turn": t["turn"], "sent": t["sent"], "exit": t["exit"], "call": t["call"],
                              "basis": core.get("basis"), "core_workflows": core.get("workflows"),
                              "questions_asked": [f.get("question") for f in core.get("facts") or []],
                              "clarify_question": (core.get("clarify") or {}).get("question"),
                              "reply_opening": t["reply"][:1500], "check": checked(P5 / "live" / tag / sid / t["turn"])})
            gold = {k: v for k, v in item.items() if k not in ("interpretation_facts",)}
            rows.append({"id": f"{tag}:{item_id}", "round": tag, "system": system, "item": item_id,
                         "part": result["part"], "outcome": result.get("outcome") or result.get("final"),
                         "scored": {k: v for k, v in result.items() if k in ("t1", "final", "why", "sent", "turns")},
                         "gold": gold, "turns": found})
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False, default=str))
    from collections import Counter
    print(f"{len(rows)} wrong h7 sessions; by round {dict(Counter(r['round'] for r in rows))}; "
          f"by part {dict(Counter(r['part'] for r in rows))}")


if __name__ == "__main__":
    main(sys.argv[1])
