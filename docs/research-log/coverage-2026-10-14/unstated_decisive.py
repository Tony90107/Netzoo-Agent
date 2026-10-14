"""Item 5 (2026-10-14): how often an unstated condition decides a recorded result, by gold.

Usage (repository root): python docs/research-log/coverage-2026-10-14/unstated_decisive.py

For every recorded single-turn reading (sessions from 2026-10-11 on) of a held-out item, each ask the check credited
is fitted once per value of each condition the reading left unstated (`needed_facts.decisive_outcomes`, as for a
stated unknown). A condition is decisive when the fits differ: asking about every decisive unstated condition is the
rule the 90-point plan proposes. By gold, an ask on a supported result is a needless question; on a not-supported
result, one the answer could rescue. No model is called.
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "scale-hard-2026-10-14"))
from coverage import gold_items, overlaps  # noqa: E402
from recent_misses import SINCE  # noqa: E402
from scale_empties import KNOWN, WORKTREES, proposal_of  # noqa: E402
from netzoo_agent_core.interpretation import capability_check as cc  # noqa: E402
from netzoo_agent_core.interpretation.needed_facts import decisive_outcomes  # noqa: E402

UNSTATED = {"data_unit": "not_stated", "samples_matched": "not_stated", "scale": "unstated"}


def main():
    gold = gold_items()
    counts, examples, seen = collections.Counter(), collections.defaultdict(list), set()
    for session in sorted(WORKTREES.glob("*/.netzoo/sessions/*.json")):
        try:
            data = json.loads(session.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if float(data.get("created_at") or 0) < SINCE:
            continue
        users = [m["content"] for m in data.get("messages", []) if m.get("role") == "user"]
        item = gold.get(" ".join(users[0].split())) if len(users) == 1 else None
        if item is None or not data.get("run_id"):
            continue
        proposal = proposal_of(session.parents[1] / "traces" / str(data["run_id"]))
        if proposal is None or proposal == "invalid":
            continue
        task = users[0]
        conditions = cc.verified_conditions(task, proposal)
        for index in range(1, 1 + sum(1 for n in type(proposal).model_fields if re.fullmatch(r"s\d+", n))):
            for ask in getattr(proposal, f"s{index}").asks:
                item_ask = cc._with_conditions(ask, conditions)
                keys = [k for k in item_ask.delivered_by if KNOWN.get(k) and KNOWN[k].kind == "produces"]
                if not cc._fitting(keys, item_ask):
                    continue
                span = cc._span(task, ask.quote)
                expect = next((r["expect"] for r in item["requirements"] if overlaps(span, cc._span(task, r["words"]))),
                              None)
                if expect is None:
                    continue
                attrs = {name: getattr(item_ask, name) for name in cc._TYPED if hasattr(item_ask, name)}
                if attrs.get("omics_layers", 0) >= 2:
                    attrs.setdefault("samples_matched", "not_stated")
                key = (" ".join(task.split()), ask.quote)
                if key in seen:
                    continue
                seen.add(key)
                counts[("asks", expect)] += 1
                for about, unstated in UNSTATED.items():
                    if attrs.get(about) != unstated:
                        continue
                    if decisive_outcomes(cc._fitting, keys, attrs, about) is not None:
                        counts[(about, expect)] += 1
                        examples[(about, expect)].append(f"{item['id']}: {ask.quote}")
    for (about, expect), n in sorted(counts.items()):
        print(f"{about:16} {expect:14} {n}")
    for key, rows in sorted(examples.items()):
        print(key, rows[:6])


if __name__ == "__main__":
    main()
