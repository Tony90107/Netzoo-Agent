"""ROUND-20 step 4: each reply's stated reasons beside ROUND-19's (same readings, same decisions -- harness 0 changes).

A reply whose statements (non-R0 lines) are unchanged keeps its ROUND-19 final category (the judge's, with my review of
every judge-'wrong' reply); a changed one is written to CHANGED.json for the frozen judge and my review.

Usage: python3 compare.py NEW_REPLIES.json CHANGED.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROUND19 = HERE.parent / "reason-accuracy-2026-10-21"
sys.path.insert(0, str(ROUND19))
import final as round19  # noqa: E402


def statements(row: dict) -> list[tuple[str, str]]:
    return [(line["quote"], line["text"]) for line in row["lines"] if line["type"] != "R0"]


def main(new_path: str, changed_path: str):
    old = {row["key"]: row for row in json.loads((ROUND19 / "judged.json").read_text())["rows"]}
    new = json.loads(Path(new_path).read_text())
    assert {row["key"] for row in new} == set(old), "the same 209 replies"
    changed = [row for row in new if statements(row) != statements(old[row["key"]])]
    Path(changed_path).write_text(json.dumps(changed, indent=1, ensure_ascii=False))
    print(f"{len(new)} replies; statements changed in {len(changed)}")
    print("ROUND-19 category of the changed:", dict(Counter(round19.final(old[r['key']]) for r in changed)))
    for row in changed:
        before, after = statements(old[row["key"]]), statements(row)
        print(f"== {row['session']} gold {row['gold']} ROUND-19 {round19.final(old[row['key']])}"
              f"{' -> no reason' if not after else ''}")
        for quote, text in before:
            if (quote, text) not in after:
                print(f"   - {text[:150]}")
        for quote, text in after:
            if (quote, text) not in before:
                print(f"   + {text[:150]}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
