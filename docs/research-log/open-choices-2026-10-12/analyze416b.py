"""Log 416 blind round: code-read metrics of heldout416b (written blind by an independent writer).

Usage (repository root): python docs/research-log/open-choices-2026-10-12/analyze416b.py <tag> <repeats>

Same session reading as analyze416.py. Per item `expect`:
- ASK: success = not refused, not selected, asked, and every named option named (OPEN, RUN_OPEN with options);
- ANSWER: answered = a workflow offered and not refused;
- REFUSE: said = the reply says no registered workflow produces it, or the check found a full gap.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze416 as base  # noqa: E402

ITEMS = {item["id"]: item for item in json.loads((HERE / "heldout416b.json").read_text())["items"]}


def main():
    tag, repeats = sys.argv[1], int(sys.argv[2])
    rows = []
    for key, item in ITEMS.items():
        for rep in range(1, repeats + 1):
            for arm in base.ARMS:
                found = base.session(tag, arm, key, rep)
                row = {"id": key, "family": item["family"], "expect": item["expect"], "rep": rep, "arm": arm,
                       **base.read(item, found)}
                text = (found[0] if found else "").casefold()
                row["said_no"] = "no registered workflow" in text or row.get("refused", False)
                rows.append(row)
    (HERE / "live").mkdir(exist_ok=True)
    (HERE / "live" / f"{tag}-metrics.json").write_text(json.dumps(rows, indent=1))
    families = ["OPEN", "VAGUE", "UNKNOWN_INPUT", "RUN_OPEN", "DECIDED", "IMPOSSIBLE"]
    for arm in base.ARMS:
        mine = [r for r in rows if r["arm"] == arm]
        print(f"{arm}: missing/empty {sum(1 for r in mine if r.get('missing') or r.get('empty'))}")
        for family in families:
            group = [r for r in mine if r["family"] == family]
            if not group:
                continue
            if group[0]["expect"] == "ASK":
                print(f"  {family:14} ASK success {sum(r.get('success', False) for r in group)}/{len(group)}  "
                      f"selected {sum(r.get('selected', False) for r in group)}  refused "
                      f"{sum(r.get('refused', False) for r in group)}  choice {sum(r.get('choice', False) for r in group)}")
            elif group[0]["expect"] == "ANSWER":
                print(f"  {family:14} answered {sum(bool(r.get('offered')) and not r.get('refused') for r in group)}"
                      f"/{len(group)}  choice fired {sum(r.get('choice', False) for r in group)}")
            else:
                print(f"  {family:14} said not given {sum(r['said_no'] for r in group)}/{len(group)}  "
                      f"choice fired {sum(r.get('choice', False) for r in group)}")


if __name__ == "__main__":
    main()
