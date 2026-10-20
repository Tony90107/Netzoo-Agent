"""ROUND-06 offline replay (collab/ROUND-06-PLAN.md section 2): no model calls.

For every recorded turn that planned a run -- routing's own run (`routing.run_check_shadow`) or one adopted on a
guidance turn (`routing.requested_run_adopted`) -- the turn's final check (after any re-read) is bound to the run's
workflow by the code given (--scripts DIR, else this checkout): the controls the run takes, and the stated settings
that hold it. A control the request set as name=value is the run's already (read from the request text, as the
routing parameters are). Old code bound nothing on the adoption path, which this replay reports apart.

Usage: python3 replay.py OUT.json [--scripts DIR]
       python3 replay.py compare OLD.json NEW.json
"""
from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREE = HERE.parents[2]
ROOTS = [WORKTREE / "docs" / "research-log", WORKTREE.parents[1] / "netzoo_agent" / "docs" / "research-log"]


def _turns():
    seen = set()
    for root in ROOTS:
        for path in sorted(glob.glob(str(root / "**" / "events.jsonl"), recursive=True)):
            events = [json.loads(line) for line in open(path) if line.strip()]
            kinds = {e["event_type"] for e in events}
            adopted = next((e["payload"]["action"] for e in events if e["event_type"] == "routing.requested_run_adopted"), None)
            shadow = next((e["payload"]["action"] for e in events if e["event_type"] == "routing.run_check_shadow"), None)
            action = adopted or shadow
            if action is None:
                continue
            check = None
            for e in events:
                if e["event_type"] in ("routing.capability_checked", "routing.capability_reread") and e["payload"].get("check"):
                    check = e["payload"]["check"]
            session = Path(path).with_name("session.json")
            if check is None or not session.exists():
                continue
            task = [m["content"] for m in json.loads(session.read_text())["messages"] if m["role"] == "user"][-1]
            key = str(Path(path).parent.relative_to(root.parent.parent))
            if key in seen:
                continue
            seen.add(key)
            yield key, task, action, check, "adopted" if adopted else "run"


def bind(out: str):
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck
    from netzoo_agent_core.interpretation.method_conditions import unbound_settings, verified_controls

    found = {}
    for key, task, action, raw, path in _turns():
        check = CapabilityCheck.model_validate({k: v for k, v in raw.items() if k in CapabilityCheck.model_fields})
        set_by_request = lambda name, task=task: re.search(rf"\b{re.escape(name)}\s*=", task, re.I) is not None  # noqa: E731
        found[key] = {"action": action, "path": path, "task": task,
                      "controls": {k: str(v) for k, v in verified_controls(check, action).items()
                                   if not set_by_request(k)},
                      "unbound": unbound_settings(check, action, set_by_request)}
    Path(out).write_text(json.dumps(found, indent=1))
    print(f"{len(found)} run turns -> {out}")


def compare(old_path: str, new_path: str):
    old, new = json.loads(Path(old_path).read_text()), json.loads(Path(new_path).read_text())
    changed = 0
    for key in sorted(new):
        a, b = old[key], new[key]
        # before ROUND-06 the adoption path bound nothing and held nothing
        before_controls = a["controls"] if a["path"] == "run" else {}
        before_unbound = a["unbound"] if a["path"] == "run" else []
        if (before_controls, before_unbound) == (b["controls"], b["unbound"]):
            continue
        changed += 1
        print(f"{key.split('research-log/')[-1][:70]} [{b['path']} {b['action']}]")
        if before_controls != b["controls"]:
            print(f"    controls {before_controls} -> {b['controls']}")
        if before_unbound != b["unbound"]:
            print(f"    held by  {before_unbound} -> {b['unbound']}")
    print(f"{changed} of {len(new)} run turns change")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[0] == "compare":
        compare(args[1], args[2])
    else:
        sys.path.insert(0, args[args.index("--scripts") + 1] if "--scripts" in args else str(WORKTREE / "scripts"))
        bind(args[0])
