"""Misread detection (ROUND.md), h7 live: the same signals on each E (p5r1) and E' (p5r2) session's first turn, read
from its recorded trace (as `harness-repair/a1c/redecide.py` reads h8), with the frozen code's replayed call beside
the call made live. No model calls.

Usage: python3 signals_h7.py OUT.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import signals  # noqa: E402  (sets the paths)

REPAIR = signals.REPAIR
RUNS = (("p5r1", "E"), ("p5r2", "E2"))


def main(out: str):
    sys.path.insert(0, str(signals.LOGS / "false-accept-replay-2026-10-21"))
    import replay_full  # noqa: E402
    from replay import _fits
    import netzoo_agent_core.interpretation.core_decision as core_decision

    items = json.loads((REPAIR / "h7" / "items.json").read_text())
    gold = {item["id"]: item for item in items["single"] + items["multi"]}
    labels = {}
    for path in sorted((REPAIR / "attribution").glob("labels-h7-*.json")):
        labels.update(json.loads(path.read_text()))
    original, seen, rows = core_decision.decide_core, {}, []

    def spy(decision, task="", **kwargs):
        seen["decision"], seen["core"] = decision, original(decision, task, **kwargs)
        return seen["core"]

    for tag, system in RUNS:
        scored = {r["item"]: r for r in json.loads((REPAIR / "p5" / f"score-{tag}.json").read_text())["rows"]
                  if r["system"] == system}
        for turn in sorted((REPAIR / "p5" / "live" / tag).glob(f"hb-{tag}-*-{system}-1/t1")):
            item = turn.parent.name.split("-")[2]
            session = json.loads((turn / "session.json").read_text()) if (turn / "session.json").exists() else {}
            found = [json.loads(line) for trace in sorted(turn.glob("trace-*.jsonl"))
                     for line in trace.read_text().splitlines() if line.strip()]
            live = next((e["payload"] for e in reversed(found) if e.get("event_type") == "core.decision"), {})
            label = labels.get(f"{tag}:{item}")
            row = {"id": f"{tag}:{item}", "item": item, "part": "multi" if item.startswith("M") else "single",
                   "expected": gold[item].get("expected_call") or gold[item].get("t1_call"),
                   "also": gold[item].get("also_acceptable") or [],
                   "outcome": (scored.get(item) or {}).get("outcome") or (scored.get(item) or {}).get("t1"),
                   "live_call": live.get("kind"), "live_basis": live.get("basis"),
                   "layer": label and label["layer"], "subtype": label and label["subtype"],
                   "request": (gold[item].get("prompt") or "")[:400]}
            checks = [i for i, e in enumerate(found)
                      if e.get("event_type") == "routing.capability_checked" and e["payload"].get("proposal")]
            if not checks:
                rows.append({**row, "call": "no_reading"})
                continue
            payload = found[checks[0]]["payload"]["proposal"]
            reread = next((e["payload"] for e in found[checks[0] + 1:]
                           if e.get("event_type") == "routing.capability_reread"), None)
            users = [m["content"] for m in session.get("messages", []) if m["role"] == "user"]
            task = next((t for t in reversed(users) if _fits(t, payload)), None)
            if task is None:
                rows.append({**row, "call": "no_task"})
                continue
            seen.clear()
            core_decision.decide_core = spy
            try:
                replay_full.replay(turn, task, payload, reread, found)
            except Exception as error:  # noqa: BLE001 -- reported, never hidden
                rows.append({**row, "call": "error", "error_text": f"{type(error).__name__}: {error}"[:200]})
                continue
            finally:
                core_decision.decide_core = original
            core = seen["core"]
            rows.append({**row, "call": core.kind, "basis": core.basis, "partial": bool(core.partial),
                         "signals": signals.compute(seen["decision"], core, found, task, payload, reread)})
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    single = [r for r in rows if r["part"] == "single"]
    print(f"{len(rows)} sessions ({len(single)} single); replayed = live call on "
          f"{sum(r.get('call') == r['live_call'] for r in rows)}; labelled {sum(bool(r['layer']) for r in rows)}")


if __name__ == "__main__":
    main(sys.argv[1])
