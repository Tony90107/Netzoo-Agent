"""S1 (ROUND.md): every recorded reply with routing's scale question, against `checked_scale_question` and the turn's
recorded check (scale of each credited result). No model calls. Usage: python3 survey.py > SURVEY.txt"""
from __future__ import annotations

import glob
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from netzoo_agent_core.graph.condition_recommender import SCALE_QUESTION, checked_scale_question  # noqa: E402

LOGS = [ROOT.parents[1] / "netzoo_agent/docs/research-log", ROOT / "docs/research-log"]
seen, counts = set(), Counter()
for path in sorted({p for root in LOGS for p in glob.glob(str(root / "**/stdout.txt"), recursive=True)}):
    if SCALE_QUESTION not in open(path, errors="replace").read():
        continue
    folder = os.path.dirname(path)
    rel = path.split("research-log/")[-1]
    if rel in seen:
        continue
    seen.add(rel)
    scales = None
    for trace in glob.glob(folder + "/trace-*.jsonl") + glob.glob(folder + "/events.jsonl"):
        for line in open(trace, errors="replace"):
            if '"routing.capability_checked"' in line:
                check = json.loads(line)["payload"]["check"]
                scales = [(item.get("attrs") or {}).get("scale") for item in check.get("requirements") or []
                          if item.get("kind") == "result" and item.get("delivered_by")]
    group = ("no check" if scales is None else "nothing credited" if not scales
             else "all stated" if all(s in ("per_sample", "whole_cohort") for s in scales) else "some unstated")
    dropped = checked_scale_question(SCALE_QUESTION, scales or []) != SCALE_QUESTION
    counts[(group, "dropped" if dropped else "kept")] += 1
    print(f"{group:16} {'dropped' if dropped else 'kept   '} {scales} | {rel[:100]}")
print(dict(counts))
