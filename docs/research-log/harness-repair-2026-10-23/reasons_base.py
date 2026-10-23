"""P0 (harness repair, 2026-10-23): the wrong-reason and reasonless baselines of the frozen 91a8c2d9.

The replies come from ROUND-20's `replies.py` run with this checkout (REPLIES.json, no model calls). A reply whose stated
reasons (non-R0 lines) equal ROUND-20's for the same reading keeps ROUND-20's final category (the frozen judge plus my
review of every changed reply, by ROUND-19's standards); a reply that states no reason is `no_reason` by code, as in
ROUND-19. Every other reply is written to CHANGED.json and needs a category in REVIEW.

The 3 changed replies of 91a8c2d9 were reviewed by me against their gold reasons; the frozen judge was not run (3
replies, every one reviewed by hand, and the judge is unreliable on "false" anyway: 14 of its 43 confirmed).

Usage: python3 reasons_base.py REPLIES.json CHANGED.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROUND19 = HERE.parent / "reason-accuracy-2026-10-21"
ROUND20 = HERE.parent / "stated-reasons-2026-10-21"
sys.path.insert(0, str(ROUND19))
import final as round19  # noqa: E402

ORDER = ("wrong", "misleading", "right", "true_not_main", "no_reason")

# My category for each reply whose statements changed since ROUND-20, by ROUND-19's standards.
REVIEW = {
    "hb-h1-H27-1": ("right", "CONDOR runs only on a regulator-gene network: the gold reason (ROUND-20 said none)"),
    "hb-h3main-L44-1": ("right", "only COBRA's genes-over-samples limit, the gold reason; the R5 output-folder line is gone"),
    "hb-h3main-L48-1": ("right", "the user's 'haven't built any network' and CONDOR's network input: the gold reason"),
}


def statements(row: dict) -> list[tuple[str, str]]:
    return [(line["quote"], line["text"]) for line in row["lines"] if line["type"] != "R0"]


def round20() -> tuple[dict, dict]:
    """ROUND-20's replies by key, and the final category of each (its final.py, without printing)."""
    sys.path.insert(0, str(ROUND20))
    import importlib.util
    spec = importlib.util.spec_from_file_location("round20_final", ROUND20 / "final.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    old = {r["key"]: r for r in json.loads((ROUND19 / "judged.json").read_text())["rows"]}
    replies = {r["key"]: r for r in json.loads((ROUND20 / "replies.json").read_text())}
    changed = {r["key"] for r in json.loads((ROUND20 / "judged-changed.json").read_text())["rows"]}
    before = {key: round19.final(row) for key, row in old.items()}
    after = {key: module.REVIEW[r["session"]][0] if key in changed else before[key] for key, r in replies.items()}
    return replies, after


def main(new_path: str, changed_path: str):
    replies, categories = round20()
    new = json.loads(Path(new_path).read_text())
    found, changed, why = {}, [], Counter()
    for row in new:
        old = replies.get(row["key"])
        if not statements(row):
            found[row["key"]] = "no_reason"
            why["no reason stated (code)"] += 1
        elif old is not None and statements(old) == statements(row):
            found[row["key"]] = categories[row["key"]]
            why["same statements as ROUND-20"] += 1
        else:
            changed.append(row)
            why["new reply" if old is None else "statements changed"] += 1
    Path(changed_path).write_text(json.dumps(changed, indent=1, ensure_ascii=False))
    print(f"{len(new)} replies ({len(replies)} in ROUND-20); {dict(why)}")
    unreviewed = [row["session"] for row in changed if row["session"] not in REVIEW]
    if unreviewed:
        counts = Counter(found.values())
        print("settled  " + "  ".join(f"{name} {counts[name]:3}" for name in ORDER) + f"  -- to review: {unreviewed}")
        return
    for row in changed:
        found[row["key"]] = REVIEW[row["session"]][0]
        print(f"  changed {row['session']:18} ROUND-20 {categories.get(row['key'], '-'):13} -> "
              f"{REVIEW[row['session']][0]:13} {REVIEW[row['session']][1]}")
    gone = [key for key in replies if key not in {r["key"] for r in new}]
    print(f"  ROUND-20 replies no longer declining: {[(replies[k]['session'], categories[k]) for k in gone]}")
    for name, rows in [("all", new)] + [(f"  gold {g}", [r for r in new if r["gold"] == g])
                                         for g in ("DECLINE", "DO", "CLARIFY", "ASK")]:
        counts = Counter(found[r["key"]] for r in rows)
        print(f"{name:14} n={len(rows):3}  " + "  ".join(f"{c} {counts[c]:3}" for c in ORDER))
    for category in ("wrong", "misleading"):
        print(f"  {category}: {sorted(r['session'] for r in new if found[r['key']] == category)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
