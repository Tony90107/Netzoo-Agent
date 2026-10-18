"""Closed-menu phase 0: what one missed field does to each gold reading (no model calls).

Phase 1's reader will miss fields. For every gold reading and every field it states, the field is dropped (an intent or
condition becomes not stated; a count, setting, requirement, data item or doubt is removed) and the item decided again.
Each change is one of:
- same: the call does not move;
- safe: the call becomes a question (ASK or CLARIFY) -- the user is asked instead of being answered wrongly;
- unsafe: a wrong DO or DECLINE -- what the design must keep rare.

Usage: python3 phase0_missed_fields.py
"""

from __future__ import annotations

import copy
import sys
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase0_gate import ITEMS, reading, score  # noqa: E402

from netzoo_agent_core.interpretation.menu_decision import decide_menu  # noqa: E402

HERE = Path(__file__).resolve().parent
_WANTED = ("artifact", "integration", "granularity", "regulators", "layers", "signed", "compare", "requirements")
_TOP = ("conditions", "data", "data_absent", "only_data", "sample_count", "feature_count", "single_feature_count",
        "settings", "unsure_files", "claims", "groups")


def drops(raw: dict):
    """(label, reading with that one field dropped) for every field the gold reading states."""
    for index, wanted in enumerate(raw.get("wanted") or []):
        for name in _WANTED:
            if name in wanted:
                changed = copy.deepcopy(raw)
                del changed["wanted"][index][name]
                yield f"wanted[{index}].{name}", changed
    for name in _TOP:
        value = raw.get(name)
        if isinstance(value, (list, dict)) and not isinstance(value, str) and len(value) > 1 and name != "sample_count":
            keys = list(value) if isinstance(value, dict) else range(len(value))
            for key in keys:
                changed = copy.deepcopy(raw)
                if isinstance(value, dict):
                    del changed[name][key]
                else:
                    changed[name] = [v for i, v in enumerate(value) if i != key]
                yield f"{name}[{key}]", changed
        elif name in raw:
            changed = copy.deepcopy(raw)
            del changed[name]
            yield name, changed


def main() -> None:
    gold = yaml.safe_load((HERE / "gold_readings.yaml").read_text(encoding="utf-8"))
    tally, unsafe = Counter(), []
    for key in sorted(gold):
        item, raw = ITEMS[key], gold[key]
        base = decide_menu(reading(raw), item["prompt"])
        for label, changed in drops(raw):
            decision = decide_menu(reading(changed), item["prompt"])
            if (decision.kind, decision.workflows) == (base.kind, base.workflows):
                tally["same"] += 1
            elif score(item, decision, raw.get("fact")) == "correct":
                tally["same"] += 1
            elif decision.kind in ("ASK", "CLARIFY"):
                tally["safe"] += 1
            else:
                tally["unsafe"] += 1
                unsafe.append((key, item["class"], label, decision.kind, decision.workflows))
    total = sum(tally.values())
    print(f"{total} single-field misses: " + ", ".join(f"{k} {v} ({v / total:.0%})" for k, v in tally.most_common()))
    for row in unsafe:
        print("  unsafe:", *row)


if __name__ == "__main__":
    main()
