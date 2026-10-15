"""Rebuild every distinct recorded capability check in `.worktrees/*/.netzoo` with one checkout's code (A/B).

Usage: REPLAY_CODE_ROOT=<checkout> python docs/research-log/m3-method-fitting-2026-10-15/replay_all.py <out.json>

As `method-conditions-2026-10-14/replay_checks.py`, but every turn of a session (a follow-up's request is its last
user message), and with the condition-check pairs the check would send. No model is called; run it once per checkout
and diff the two files. Recordings state no request-level count, so only the other round-m3 rules can change them.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE_ROOT = Path(os.environ.get("REPLAY_CODE_ROOT") or HERE.parents[2])
WORKTREES = Path(os.environ.get("REPLAY_WORKTREES") or "/Users/chenzhonghan/Documents/LLM AGENT/.worktrees")
sys.path.insert(0, str(CODE_ROOT / "scripts"))

from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import (  # noqa: E402
    build_capability_check, condition_pairs, stated_requirements, understanding_paragraph,
)


def recordings():
    seen = set()
    for session in sorted(WORKTREES.glob("*/.netzoo/sessions/*.json")):
        try:
            data = json.loads(session.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        users = [m["content"] for m in data.get("messages", []) if m.get("role") == "user"]
        if not users or not isinstance(users[-1], str) or not data.get("run_id"):
            continue
        events = session.parents[1] / "traces" / str(data["run_id"]) / "events.jsonl"
        if not events.exists():
            continue
        for line in events.read_text().splitlines():
            if '"routing.capability_checked"' not in line:
                continue
            payload = json.loads(line)["payload"].get("proposal")
            if not payload:
                break
            key = hashlib.sha256(json.dumps([users[-1], payload], sort_keys=True).encode()).hexdigest()
            if key not in seen:
                seen.add(key)
                yield key, f"{session.parents[2].name}/{session.stem}", users[-1], payload
            break


def main(out: str) -> None:
    rows, invalid = {}, 0
    for key, where, task, payload in recordings():
        count = sum(1 for name in payload if re.fullmatch(r"s\d+", name))
        try:
            proposal = proposal_model(count).model_validate(payload)
        except Exception:  # noqa: BLE001
            try:
                proposal = proposal_model(count, compact=True).model_validate(payload)
            except Exception:  # noqa: BLE001 -- recordings from before a schema change
                invalid += 1
                continue
        check, _rejected = build_capability_check(task, proposal)
        pairs = [[check.requirements[i].quote, action, quote] for i, action, _keys, quote in
                 condition_pairs(check, stated_requirements(task, proposal, check))
                 + condition_pairs(check, stated_requirements(task, proposal, check, own_sentence=True))]
        rows[key] = {"where": where, "task": task, "full_gap": check.full_gap, "unchecked": check.unchecked,
                     "results": [[item.quote, item.status, sorted(item.delivered_by), sorted(item.defaults)]
                                 for item in check.results()],
                     "pairs": pairs, "paragraph": understanding_paragraph(check)}
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    print(f"{CODE_ROOT}: {len(rows)} distinct checks rebuilt, {invalid} recordings from before a schema change")


if __name__ == "__main__":
    main(sys.argv[1])
