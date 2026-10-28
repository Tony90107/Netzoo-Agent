"""The recorded runs where each live item's bug hit (before the fixes), scored like score_live.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.path.insert(0, str(HERE))
import run_live  # noqa: E402
from score_live import turn_facts  # noqa: E402

BEFORE = {"J20": "jev-guard-2026-10-27/live/j1a/hb-j1a-J20-1", "J48": "jev-guard-2026-10-27/live/j1a/hb-j1a-J48-1",
          "Q02": "jev-overlap-2026-10-27/live/jo1/hb-jo1-Q02-1", "R21": "jev-j3-2026-10-27/live/j3g/hb-j3g-R21-1",
          "S05": "jev-j4-2026-10-27/live/j4g/hb-j4g-S05-1", "S35": "jev-j4-2026-10-27/live/j4g/hb-j4g-S35-1",
          "Q10": "jev-guard-2026-10-27/live/j2g/hb-j2g-Q10-1", "Q25": "jev-guard-2026-10-27/live/j2g/hb-j2g-Q25-1",
          "Q26": "jev-guard-2026-10-27/live/j2g/hb-j2g-Q26-1", "R03": "jev-j3-2026-10-27/live/j3g/hb-j3g-R03-1",
          "S03": "jev-j4-2026-10-27/live/j4g/hb-j4g-S03-1", "J34": "jev-guard-2026-10-27/live/j1/hb-j1-J34-1",
          "J46": "jev-guard-2026-10-27/live/j1/hb-j1-J46-1", "J06": "jev-guard-2026-10-27/live/j1u/hb-j1u-J06-1"}
items = {i["id"]: i for i in run_live.items()}
rows = []
for item, where in BEFORE.items():
    folder = LOGS / where
    job = json.loads((folder / "job.json").read_text()) if (folder / "job.json").exists() else {"sent": ["prompt"]}
    turns = [turn_facts(t) for t in sorted(folder.glob("t*")) if t.is_dir()]
    final = (turns[-1]["call"] or "None/None").split("/")[0] if turns else None
    want = run_live.expected(items[item], job.get("sent") or ["prompt"])
    rows.append({"item": item, "where": where, "sent": job.get("sent"), "turns": turns, "final": final,
                 "expected": want, "right": final == want})
(HERE / "score-before.json").write_text(json.dumps(rows, indent=1))
for r in rows:
    print(f"{r['item']:4} expected {r['expected']:8} final {r['final']!s:9} {'RIGHT' if r['right'] else 'wrong'} | "
          + " -> ".join(f"{t['call']}" + (f" ENUM400x{t['enum_400']}" if t["enum_400"] else "")
                         + (f" BLOCKED{t['blocked']}" if t["blocked"] else "") + (" PROV" if t["provisional"] else "")
                         for t in r["turns"]))
print("enum 400s:", sum(t["enum_400"] for r in rows for t in r["turns"]),
      "| check-model blocks:", sum(len(t["blocked"]) for r in rows for t in r["turns"]),
      "| provisional:", sum(t["provisional"] for r in rows for t in r["turns"]),
      "| UNCHECKED finals:", sum(r["final"] == "UNCHECKED" for r in rows),
      "| right:", sum(r["right"] for r in rows), "of", len(rows))
