"""Item 3 (2026-10-14): recorded readings where the user said the scale is not decided, under the soft and hard rule.

Usage (repository root): python docs/research-log/scale-hard-2026-10-14/unknown_scale.py

Verdict layer step 2 waits on an unknown fact only when the fits per value differ (`needed_facts.decisive_outcomes`).
A hard scale can make them differ where the soft rule did not. No model is called.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from scale_empties import KNOWN, WORKTREES, proposal_of  # noqa: E402
from netzoo_agent_core.interpretation import capability_check as cc  # noqa: E402
from netzoo_agent_core.interpretation.needed_facts import decisive_outcomes  # noqa: E402


def soft(keys, item):
    hard = cc._fitting(keys, item)
    if hard or getattr(item, "scale", "unstated") == "unstated":
        return hard
    return cc._fitting(keys, type(item)(**{**vars(item), "scale": "unstated"}))


def main():
    seen = set()
    for session in sorted(WORKTREES.glob("*/.netzoo/sessions/*.json")):
        try:
            data = json.loads(session.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        users = [m["content"] for m in data.get("messages", []) if m.get("role") == "user"]
        if len(users) != 1 or not data.get("run_id"):
            continue
        proposal = proposal_of(session.parents[1] / "traces" / str(data["run_id"]))
        if proposal is None or proposal == "invalid":
            continue
        unknowns = [fact for fact in getattr(proposal.conditions, "unknown_facts", []) or [] if fact.about == "scale"]
        if not unknowns:
            continue
        for index in range(1, 1 + sum(1 for n in type(proposal).model_fields if re.fullmatch(r"s\d+", n))):
            for ask in getattr(proposal, f"s{index}").asks:
                keys = [k for k in ask.delivered_by if KNOWN.get(k) and KNOWN[k].kind == "produces"]
                key = (" ".join(users[0].split()), ask.quote, tuple(keys))
                if not keys or key in seen:
                    continue
                seen.add(key)
                attrs = {name: getattr(ask, name) for name in cc._TYPED if hasattr(ask, name)}
                print(f"- {users[0][:160]!r}\n    ask={ask.quote!r} keys={keys}\n    soft={decisive_outcomes(soft, keys, attrs, 'scale')}"
                      f"\n    hard={decisive_outcomes(cc._fitting, keys, attrs, 'scale')}")
    print(f"{len(seen)} distinct asks beside an unknown scale")


if __name__ == "__main__":
    main()
