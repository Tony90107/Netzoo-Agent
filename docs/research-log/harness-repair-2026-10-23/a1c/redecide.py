"""A1' confirmation (ROUND-A1C.md): each recorded h8 turn's reading decided again by one checkout's code, no model calls.

ROUND-12's B2 replay (`replay_full.replay`) on the turn's recorded events, as `stability-round13/harness.py` runs it on
events.jsonl readings; the live runner saves a turn's events as trace-*.jsonl, so this walks those. With `--scripts`
the call is decided by another checkout (the E3 snapshot to check that replay reproduces the live call, the A3-only
snapshot for the paired arm).

Usage: python3 redecide.py OUT.json TAG [TAG ...] --scripts DIR
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parents[1]
sys.path.insert(0, str(LOGS / "false-accept-replay-2026-10-21"))
import replay_full  # noqa: E402  (sets the import paths; honours --scripts)
from replay import _fits  # noqa: E402


def readings(tags):
    for tag in tags:
        for turn in sorted((HERE / "live" / tag).glob("*/t1")):
            session = json.loads((turn / "session.json").read_text()) if (turn / "session.json").exists() else {}
            found = [json.loads(line) for trace in sorted(turn.glob("trace-*.jsonl"))
                     for line in trace.read_text().splitlines() if line.strip()]
            checks = [i for i, e in enumerate(found)
                      if e.get("event_type") == "routing.capability_checked" and e["payload"].get("proposal")]
            recorded = next((e["payload"] for e in reversed(found) if e.get("event_type") == "core.decision"), {})
            row = {"tag": tag, "session": turn.parent.name, "recorded": recorded.get("kind"),
                   "recorded_basis": recorded.get("basis"), "recorded_partial": recorded.get("partial")}
            if not checks:
                yield row, None
                continue
            payload = found[checks[0]]["payload"]["proposal"]
            reread = next((e["payload"] for e in found[checks[0] + 1:]
                           if e.get("event_type") == "routing.capability_reread"), None)
            users = [m["content"] for m in session.get("messages", []) if m["role"] == "user"]
            task = next((t for t in reversed(users) if _fits(t, payload)), None)
            yield row, (turn, task, payload, reread, found) if task is not None else None


def main(out: str, tags: list[str]):
    rows = []
    for row, args in readings(tags):
        if args is None:
            row.update(kind="no_reading")
        else:
            try:
                call = replay_full.replay(*args)
                row.update(kind=call["kind"], basis=call.get("basis"), partial=call.get("partial"),
                           unrecorded=call.get("unrecorded", {}))
            except Exception as error:  # noqa: BLE001 -- reported, never hidden
                row.update(kind="error", error=f"{type(error).__name__}: {error}"[:300])
        rows.append(row)
    Path(out).write_text(json.dumps(rows, indent=1) + "\n")
    import netzoo_agent_core

    print(f"code: {Path(netzoo_agent_core.__file__).parents[2]}")
    print(f"{len(rows)} turns; {sum(r['kind'] == 'no_reading' for r in rows)} without a reading; "
          f"{sum(r['kind'] == 'error' for r in rows)} errors")


if __name__ == "__main__":
    args = [a for i, a in enumerate(sys.argv[1:], 1) if a != "--scripts" and sys.argv[i - 1] != "--scripts"]
    main(args[0], args[1:])
