"""Slim reading S1 gate (spec 2026-10-19, 6.1): the 56 phase-0 gold readings in the slim shape, through the decision
table (no model calls).

Arms:
- old:      the gold `MenuReading` as written (phase 0's gate, with S1's decision rules);
- full:     gold -> slim (`to_slim`) -> `to_menu`: the slim shape holds every value the gold needs;
- pipeline: the slim reading as the two reads would leave it -- the core part (A, C, D) plus only the B facts whose
            fields step 2 chooses from the candidates' contracts (`slim_needs`, `chosen`);
- b2_literal: pipeline, with B2 read only while PUMA- and PANDA-type workflows are both candidates (the spec table's
            wording), to show what that trigger alone would miss.

Usage: python3 s1_gate.py [--show]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "docs/research-log/closed-menu-phase0-2026-10-18"))

from phase0_gate import ITEMS, reading, score  # noqa: E402

from netzoo_agent_core.interpretation.menu_decision import decide_menu  # noqa: E402
from netzoo_agent_core.interpretation.slim_reader import (  # noqa: E402
    Needs, chosen, slim_needs, split_b, to_menu, to_slim,
)

PUMA_TYPE = {"PUMA", "LIONESS-PUMA"}
PANDA_TYPE = {"PANDA", "LIONESS-PANDA", "OTTER", "GIRAFFE"}


def literal_b2(needs: Needs) -> Needs:
    both = PUMA_TYPE & set(needs.candidates) and PANDA_TYPE & set(needs.candidates)
    return needs if both else Needs(intents=tuple(p for p in needs.intents if p[1] != "regulators"),
                                    conditions=needs.conditions, candidates=needs.candidates, counts=needs.counts,
                                    groups=needs.groups)


def arms(raw: dict, prompt: str) -> dict:
    gold = reading(raw)
    slim = to_slim(gold)
    core, b_facts = split_b(slim)
    needs = slim_needs(core, prompt)
    out = {"old": gold, "full": to_menu(slim)}
    for name, n in (("pipeline", needs), ("b2_literal", literal_b2(needs))):
        kept = [f for f in b_facts if chosen(f, n)]
        out[name] = to_menu(core.model_copy(update={"stated": [*core.stated, *kept]}))
        out[f"{name}_unread"] = [f"{f.field}:{f.name}={f.value or f.values}" for f in b_facts if not chosen(f, n)]
    out["needs"] = needs
    return out


def main() -> None:
    gold = yaml.safe_load((ROOT / "docs/research-log/closed-menu-phase0-2026-10-18/gold_readings.yaml").read_text())
    rows, right = [], {"old": 0, "full": 0, "pipeline": 0, "b2_literal": 0}
    for key in sorted(gold):
        item, raw = ITEMS[key], gold[key]
        found = arms(raw, item["prompt"])
        row = {"id": key, "class": item["class"], "needs": {
            "candidates": list(found["needs"].candidates), "cells": [c[0] for c in found["needs"].cells()],
            "counts": list(found["needs"].counts)}}
        for arm in right:
            decision = decide_menu(found[arm], item["prompt"])
            outcome = score(item, decision, raw.get("fact"))
            right[arm] += outcome == "correct"
            row[arm] = {"kind": decision.kind, "workflows": decision.workflows,
                        "questions": [q.dimension for q in decision.questions], "outcome": outcome}
        row["unread"] = found["pipeline_unread"]
        row["unread_b2_literal"] = found["b2_literal_unread"]
        rows.append(row)
        if "--show" in sys.argv or any(row[arm]["outcome"] != "correct" for arm in right):
            print(key, item["class"], {arm: (row[arm]["kind"], row[arm]["questions"], row[arm]["outcome"])
                                       for arm in right if row[arm]["outcome"] != "correct" or "--show" in sys.argv},
                  "unread:", row["unread"] or "-", "| cells:", row["needs"]["cells"])
    print({arm: f"{n}/{len(rows)}" for arm, n in right.items()})
    (HERE / "s1-gate.json").write_text(json.dumps({"right": right, "rows": rows}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
