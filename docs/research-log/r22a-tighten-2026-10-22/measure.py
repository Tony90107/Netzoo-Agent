"""R22-A tightened (2026-10-22): every reading replayed by the harness with the offline read caches; the labelled
corpus compared with ROUND-22's run, and h5's sessions scored by the h5 scorer before and after.

Usage: python3 measure.py OUT.json [BEFORE.json]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.path.insert(0, str(LOGS / "stability-round13-2026-10-21"))
import harness  # noqa: E402

harness.replay_full.GOAL_READS.update({d["task"]: d["read"] for d in json.loads(
    (LOGS / "goal-read-2026-10-21/reads.json").read_text())["reads"] if d["read"]})
harness.replay_full.SETTINGS_READS.update({f"{d['task']}\x00{d['workflow']}": d["read"] for d in json.loads(
    (LOGS / "input-constraints-2026-10-21/settings-reads.json").read_text())["reads"] if d["read"]})
sys.path.insert(0, str(LOGS / "heldout-h5-2026-10-21"))
import score  # noqa: E402

H5 = re.compile(r"^hb-h5main-(Q\d+)-(\d)$")


def h5(path):
    items = score.items()
    labels = json.loads((LOGS / "heldout-h5-2026-10-21/facts-checked.json").read_text())
    key = json.loads((LOGS / "heldout-h5-2026-10-21/fact-key.json").read_text())
    right = {key[s]: v for s, v in labels.items()}
    out = {}
    for row in json.loads(Path(path).read_text()).values():
        if m := H5.match(row["session"]):
            core = {"kind": row["kind"], "workflows": [], "partial": row["partial"]}
            out[(m.group(1), int(m.group(2)))] = score.outcome(items[m.group(1)], core, right.get(f"{m.group(1)}-{m.group(2)}"))
    return out


if __name__ == "__main__":
    harness.run(sys.argv[1])
    before, after = h5(sys.argv[2] if len(sys.argv) > 2 else LOGS / "heldout-h5-2026-10-21/harness-now.json"), h5(sys.argv[1])
    print(f"h5 replay: correct {sum(v == 'correct' for v in before.values())} -> "
          f"{sum(v == 'correct' for v in after.values())} of {len(after)}")
    for key in sorted(after):
        if before.get(key) != after[key]:
            print("  ", key, before.get(key), "->", after[key])
