"""D1 (ROUND.md): every recorded reply with the tie question's default line, re-written with `checked_default_line`
and the turn's recorded check credits. No model calls. Usage: python3 survey.py > SURVEY.txt"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from netzoo_agent_core.capability_sheet import entry  # noqa: E402
from netzoo_agent_core.graph.condition_recommender import checked_default_line  # noqa: E402

LOGS = ROOT.parents[1] / "netzoo_agent/docs/research-log"
LINE = re.compile(r"(?:Both fit|These all fit); to choose, tell me: .*?If none of these applies: [^.]*\.")

seen, changed, rows = set(), 0, 0
for path in sorted(glob.glob(str(LOGS / "**/stdout.txt"), recursive=True)):
    found = LINE.search(open(path, errors="replace").read())
    if not found:
        continue
    folder = os.path.dirname(path)
    credited = set()
    for trace in glob.glob(folder + "/trace-*.jsonl") + glob.glob(folder + "/events.jsonl"):
        for line in open(trace, errors="replace"):
            if '"routing.capability_checked"' in line:
                for item in json.loads(line)["payload"]["check"].get("requirements") or []:
                    if item.get("kind") == "result":
                        credited |= {entry(key).workflow for key in item.get("delivered_by") or []}
    session = Path(folder) / "session.json"
    request = ([m["content"] for m in json.loads(session.read_text())["messages"] if m["role"] == "user"][-1]
               if session.exists() else "")
    before = found.group(0).split("If none of these applies: ")[1]
    after = checked_default_line(found.group(0), credited)
    after = after.split("If none of these applies: ")[1] if "If none of these applies: " in after else "(line dropped)"
    rows += 1
    changed += before != after
    key = (request[:120], before, after)
    if key not in seen:
        seen.add(key)
        print(f"{'CHANGED' if before != after else 'same   '} {before} -> {after} | credited {sorted(credited)} | "
              f"{request[:120]!r}")
print(f"{rows} recorded replies with the line, {changed} changed, {len(seen)} distinct")
