"""Item 3 (2026-10-14): every recorded check reading whose typed scale rules out all the entries it credited.

Usage (repository root): python docs/research-log/scale-hard-2026-10-14/scale_empties.py [out.json]

Until item 3, `capability_check._fitting` let a scale narrow the credited entries but never empty them (Log 388: a
misread scale must not turn a deliverable result into a gap). A hard scale changes exactly the asks where narrowing
empties the list, so this lists them, with the sheet of the checkout it runs in: every single-turn recorded session in
`.worktrees/*/.netzoo`, its `routing.capability_checked` proposal, each ask whose scale empties its credited entries
after the other typed filters. Copies of one request (archive copies, repeats) are kept once per (request, quote,
scale, entries). No model is called. Gold, when the session belongs to a held-out set, is that item's requirements.

At bef3a19 (sheet before item 3): 35 distinct asks, 33 of them supported (`scale_empties.json`). With item 3's sheet
these are the asks the hard scale now refuses.
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORKTREES = ROOT.parent / ".worktrees"
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.capability_sheet import sheet_entries  # noqa: E402
from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import _fitting, verified_conditions  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import _with_conditions  # noqa: E402

KNOWN = sheet_entries()
WANT = {"per_sample": "sample_specific", "whole_cohort": "aggregate"}


def gold_items():
    items = {}
    for path in (ROOT / "docs" / "research-log").rglob("heldout*.json"):
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        for item in data.get("items", []) if isinstance(data, dict) else []:
            if isinstance(item, dict) and "prompt" in item and "requirements" in item:
                items[" ".join(item["prompt"].split())] = item
    return items


def proposal_of(run_dir: Path):
    path = run_dir / "events.jsonl"
    if not path.exists():
        return None
    for line in path.read_text().splitlines():
        if '"routing.capability_checked"' not in line:
            continue
        payload = json.loads(line)["payload"].get("proposal")
        count = sum(1 for name in payload if re.fullmatch(r"s\d+", name))
        try:
            return proposal_model(count).model_validate(payload)
        except Exception:  # noqa: BLE001 -- recordings from before a schema change
            return "invalid"
    return None


def main():
    gold = gold_items()
    seen, rows, counts = set(), [], collections.Counter()
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
            counts["no_or_invalid_proposal"] += 1
            continue
        task = users[0]
        counts["sessions"] += 1
        conditions = verified_conditions(task, proposal)
        for index in range(1, 1 + sum(1 for n in type(proposal).model_fields if re.fullmatch(r"s\d+", n))):
            for ask in getattr(proposal, f"s{index}").asks:
                counts["asks"] += 1
                item = _with_conditions(ask, conditions)
                if item.scale not in WANT:
                    continue
                counts[f"scale_{item.scale}"] += 1
                produces = [k for k in item.delivered_by if KNOWN.get(k) and KNOWN[k].kind == "produces"]
                kept = _fitting(produces, SimpleNamespace(**{**vars(item), "scale": "unstated"}))
                if not kept or any(WANT[item.scale] in KNOWN[k].granularity for k in kept):
                    continue
                key = (" ".join(task.split()), item.quote, item.scale, tuple(sorted(kept)))
                counts["empties_copies"] += 1
                if key in seen:
                    continue
                seen.add(key)
                found = gold.get(" ".join(task.split()))
                rows.append({"session": f"{session.parents[2].name}/{session.stem}", "task": task,
                             "quote": item.quote, "scale": item.scale, "kept": sorted(kept),
                             "gold": found["requirements"] if found else None,
                             "gold_id": found.get("id") if found else None})
    print(json.dumps(dict(counts), indent=1))
    print(f"{len(rows)} distinct asks whose scale empties the credited entries")
    for row in rows:
        print(f"- [{row['gold_id'] or '-'}] {row['scale']} {row['kept']} quote={row['quote']!r}\n    task={row['task'][:220]!r}"
              + (f"\n    gold={[(r['words'], r['expect'], r.get('by')) for r in row['gold']]}" if row["gold"] else ""))
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(json.dumps(rows, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
