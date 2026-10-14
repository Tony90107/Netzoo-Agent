"""Item 3 (2026-10-14): what a corrected sheet granularity plus a hard scale would change on the recorded readings.

Usage (repository root): python docs/research-log/scale-hard-2026-10-14/sheet_variant.py

Variant: the labels and tests that are read per sample and reported for the cohort get both granularities
(`BOTH`), and a stated scale then rules entries out (`narrowed`, never `narrowed or keys`). For every recorded
single-turn ask with a typed scale, the credited entries under the current code and under the variant are compared.
No model is called. Run at bef3a19 (before item 3): 654 distinct asks, 2 change, both already misread as
DRAGON; with item 3 applied it compares the code with itself.
"""
from __future__ import annotations

import dataclasses
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from scale_empties import KNOWN, WANT, gold_items, proposal_of, WORKTREES  # noqa: E402
from netzoo_agent_core.interpretation import capability_check as cc  # noqa: E402

BOTH = ("sambar.subtypes", "sambar.clinical_comparison", "giraffe.activity_tests", "lioness_panda.association_tests",
        "lioness_puma.association_tests", "lioness_dragon.association_tests", "lioness_coexpression.comparisons")


def fitting_variant(keys, item):
    original = {key: KNOWN[key] for key in BOTH}
    try:
        for key in BOTH:
            KNOWN[key] = dataclasses.replace(KNOWN[key], granularity=frozenset({"aggregate", "sample_specific"}))
        kept = cc._fitting(keys, item)
        want = WANT.get(item.scale)
        return [k for k in kept if want is None or want in KNOWN[k].granularity]
    finally:
        KNOWN.update(original)


def main():
    gold = gold_items()
    seen, changed, total = set(), [], 0
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
            continue
        task = users[0]
        conditions = cc.verified_conditions(task, proposal)
        for index in range(1, 1 + sum(1 for n in type(proposal).model_fields if re.fullmatch(r"s\d+", n))):
            for ask in getattr(proposal, f"s{index}").asks:
                item = cc._with_conditions(ask, conditions)
                if item.scale not in WANT:
                    continue
                produces = [k for k in item.delivered_by if KNOWN.get(k) and KNOWN[k].kind == "produces"]
                key = (" ".join(task.split()), item.quote, item.scale, tuple(sorted(produces)))
                if key in seen:
                    continue
                seen.add(key)
                total += 1
                old, new = cc._fitting(produces, item), fitting_variant(produces, item)
                if set(old) != set(new):
                    found = gold.get(" ".join(task.split()))
                    changed.append((item.scale, sorted(old), sorted(new), item.quote, task, found))
    print(f"{total} distinct recorded asks with a typed scale; {len(changed)} change under the variant")
    for scale, old, new, quote, task, found in changed:
        print(f"- {scale}: {old} -> {new}  quote={quote!r}\n    task={task[:200]!r}"
              + (f"\n    gold={[(r['words'], r['expect'], r.get('by')) for r in found['requirements']]}" if found else ""))


if __name__ == "__main__":
    main()
