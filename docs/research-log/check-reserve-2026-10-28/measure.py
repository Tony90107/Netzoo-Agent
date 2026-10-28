"""ROUND.md R1 / R2: gpt-4o-mini's recorded check-call outputs against the 4,000 cap, and every recorded budget.blocked
of the check model recomputed with a 4,000 reserve. Reads the traces under docs/research-log only.

Usage: python3 measure.py OUT.json
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

LOGS = Path(__file__).resolve().parent.parent
MODEL, CAP = "openai/gpt-4o-mini-2024-07-18", 4000
outputs, blocks = collections.defaultdict(list), []
for trace in LOGS.rglob("trace-*.jsonl"):
    for line in open(trace, errors="replace"):
        if MODEL not in line:
            continue
        event = json.loads(line)
        payload = event.get("payload") or {}
        if event.get("event_type") == "budget.blocked" and payload.get("model") == MODEL:
            new = payload["projected_tokens"] - payload["reserved_output_tokens"] + CAP
            blocks.append({"where": str(trace.parent.relative_to(LOGS)), "role": payload["role"],
                           "consumed": payload["consumed_tokens"], "projected": payload["projected_tokens"],
                           "with_cap": new, "limit": payload["hard_limit_tokens"],
                           "clears": new <= payload["hard_limit_tokens"]})
        for usage in [payload, *(payload.get("calls") or [])] if isinstance(payload, dict) else []:
            if isinstance(usage, dict) and usage.get("model") == MODEL and usage.get("output_tokens") is not None:
                outputs[usage.get("role")].append(usage["output_tokens"])
check_roles = ("capability_check", "capability_reread", "capability_second_opinion", "capability_condition_check")
r1 = {role: {"n": len(xs), "max": max(xs), "over_cap": sum(x > CAP for x in xs)} for role, xs in outputs.items()
      if role in check_roles}
r2 = {"blocked": len(blocks), "clear": sum(b["clears"] for b in blocks),
      "by_role": dict(collections.Counter((b["role"], b["clears"]) for b in blocks).items())}
Path(sys.argv[1]).write_text(json.dumps({"r1": r1, "r2": {**r2, "by_role": {f"{k[0]}:{k[1]}": v for k, v in
                                                                           r2["by_role"].items()}}, "blocks": blocks},
                                        indent=1))
print("R1", json.dumps(r1)); print("R2", r2["blocked"], "blocked,", r2["clear"], "clear;", r2["by_role"])
