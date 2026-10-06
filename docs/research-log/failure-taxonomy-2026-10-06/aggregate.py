"""Failure taxonomy: aggregate classify.py's rows (outcome x cause), per corpus and per item."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
GROUPS = {"base (current system: s19+s20+s21)": ["s19-base", "s20-base", "s21-base"],
          "item-4 candidates (s20 b536b95 + s21 2015646)": ["s20-cand", "s21-cand"]}


def load(name):
    return [json.loads(line) for line in (HERE / "out" / f"{name}.jsonl").read_text().splitlines() if line]


for title, names in GROUPS.items():
    rows = [dict(r, corpus=n) for n in names for r in load(n)]
    fails = [(r, o, c) for r in rows for o, c in r["fails"]]
    print(f"## {title}: {len(rows)} sessions, {sum(1 for r in rows if r['fails'])} with a failure, {len(fails)} failures")
    by = Counter((o.split("-")[0] if o.startswith("O3") else o, c) for _, o, c in fails)
    outcome = Counter(o.split("-")[0] if o.startswith("O3") else o for _, o, _ in fails)
    for o in sorted(outcome):
        print(f"  {o}: {outcome[o]}")
        for (oo, c), n in sorted(by.items(), key=lambda kv: -kv[1]):
            if oo == o:
                items = Counter(f"{r['corpus'][:3]}:{r['item']}" for r, ooo, cc in fails
                                if (ooo.split('-')[0] if ooo.startswith('O3') else ooo) == o and cc == c)
                print(f"     {n:3}  {c:38} {dict(items.most_common(12))}")
    print()
