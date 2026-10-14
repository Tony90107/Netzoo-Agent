"""M1 step 4.2 (2026-10-14): rebuild every recorded capability check with one checkout's code, for an A/B diff.

Usage (repository root of either checkout):
  REPLAY_CODE_ROOT=<checkout> python docs/research-log/method-conditions-2026-10-14/replay_checks.py <out.json>

Every single-turn recorded session in `.worktrees/*/.netzoo` whose `routing.capability_checked` event holds the
model's proposal is rebuilt with `build_capability_check` of the checkout named by REPLAY_CODE_ROOT, and its
understanding paragraph rendered. Copies of one (request, proposal) are kept once. No model is called. Run it once
per checkout and compare the two files (`compare_checks.py`): recordings from before M1 state no method, setting or
count, so every row should be identical.
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
# The recordings: the .worktrees folder this checkout is in, or the one beside the main checkout.
REPO = HERE.parents[2]
WORKTREES = REPO.parent if REPO.parent.name == ".worktrees" else REPO.parent / ".worktrees"
sys.path.insert(0, str(CODE_ROOT / "scripts"))

from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import (  # noqa: E402
    build_capability_check, understanding_paragraph,
)


def recordings():
    seen = set()
    for session in sorted(WORKTREES.glob("*/.netzoo/sessions/*.json")):
        try:
            data = json.loads(session.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        users = [m["content"] for m in data.get("messages", []) if m.get("role") == "user"]
        if len(users) != 1 or not isinstance(users[0], str) or not data.get("run_id"):
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
            key = hashlib.sha256(json.dumps([users[0], payload], sort_keys=True).encode()).hexdigest()
            if key not in seen:
                seen.add(key)
                yield key, f"{session.parents[2].name}/{session.stem}", users[0], payload
            break


def main(out: str) -> None:
    rows, invalid = {}, 0
    for key, where, task, payload in recordings():
        count = sum(1 for name in payload if re.fullmatch(r"s\d+", name))
        try:
            proposal = proposal_model(count).model_validate(payload)
        except Exception:  # noqa: BLE001 -- recordings from before a schema change
            invalid += 1
            continue
        check, _rejected = build_capability_check(task, proposal)
        rows[key] = {"where": where, "full_gap": check.full_gap, "unchecked": check.unchecked,
                     "results": [[item.quote, item.status, sorted(item.delivered_by)] for item in check.results()],
                     "paragraph": understanding_paragraph(check)}
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    print(f"{CODE_ROOT}: {len(rows)} distinct checks rebuilt, {invalid} recordings from before a schema change")


if __name__ == "__main__":
    main(sys.argv[1])
