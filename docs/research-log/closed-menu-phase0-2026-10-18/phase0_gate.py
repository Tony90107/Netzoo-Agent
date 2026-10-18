"""Closed-menu phase 0 gate: the 56 gold readings through the decision table (spec section 6; no model calls).

Each gold reading (`gold_readings.yaml`) is turned into a `MenuReading` and decided by `decide_menu` with the item's
own prompt (named workflows are counted from it). Scoring follows core-judgment-2026-10-15/score_core.py:
do -> DO not partial, workflows a subset of gold; dont -> DECLINE; ask -> ASK whose questions target the gold fact
(or, for a file-checkable run, DO whose input check settles it); vague -> CLARIFY.

Gate: at least 52/56 right. Usage: python3 phase0_gate.py [--show]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts.menu_reading import (  # noqa: E402
    Count, MenuReading, Requirement, Said, SettingAsked, Wanted,
)
from netzoo_agent_core.interpretation.menu_decision import decide_menu  # noqa: E402

ITEMS = {item["id"]: item for item in json.loads(
    (ROOT / "docs/research-log/core-judgment-2026-10-15/items.json").read_text())["items"]}
EXPECTED = {"do": "DO", "dont": "DECLINE", "ask": "ASK", "vague": "CLARIFY"}
_SAID = ("artifact", "integration", "granularity", "regulators", "layers", "signed", "compare")


def said(raw) -> Said:
    if isinstance(raw, dict):
        return Said(**{"basis": "explicit", **raw}) if raw.get("status", "stated") == "stated" else Said(**raw)
    return Said(status="stated", value=str(raw), basis="explicit", quotes=[str(raw)])


def count(raw) -> Count:
    return Count(**raw) if isinstance(raw, dict) else Count(status="stated", value=int(raw))


def reading(raw: dict) -> MenuReading:
    wanted = []
    for item in raw.get("wanted") or []:
        fields = {k: v for k, v in item.items() if k not in (*_SAID, "requirements")}
        fields.update({k: said(item[k]) for k in _SAID if k in item})
        fields["requirements"] = [Requirement(**r) for r in item.get("requirements") or []]
        wanted.append(Wanted(**fields))
    return MenuReading(
        wanted=wanted, data=raw.get("data") or [], data_absent=raw.get("data_absent") or [],
        only_data=bool(raw.get("only_data")), groups=raw.get("groups") or [],
        conditions={k: said(v) for k, v in (raw.get("conditions") or {}).items()},
        claims=said(raw["claims"]) if "claims" in raw else Said(),
        delivery=said(raw["delivery"]) if "delivery" in raw else Said(),
        unregistered_methods=raw.get("unregistered_methods") or [], context_mentions=raw.get("context_mentions") or [],
        sample_count=count(raw["sample_count"]) if "sample_count" in raw else Count(),
        feature_count=count(raw["feature_count"]) if "feature_count" in raw else Count(),
        single_feature_count=raw.get("single_feature_count"),
        settings=[SettingAsked(**s) for s in raw.get("settings") or []],
        unsure_files=raw.get("unsure_files") or [], run_requested=bool(raw.get("run_requested")))


def score(item: dict, decision, fact) -> str:
    cls, kind = item["class"], decision.kind
    offered, gold = set(decision.workflows), set(item["workflows"])
    if cls == "do":
        if kind == "DO" and not decision.partial:
            return "correct" if not offered or offered <= gold else "extra_options" if offered & gold else "wrong_workflow"
        return "needless_question" if kind in ("ASK", "CLARIFY") else "false_refusal"
    if cls == "dont":
        return "correct" if kind == "DECLINE" else ("partly_accept" if decision.partial else "false_accept") \
            if kind == "DO" else "undecided"
    asked = {q.dimension for q in decision.questions}
    right_fact = bool(asked & set(fact or ())) or ("settled" in (fact or ()) and bool(decision.settled))
    if kind == EXPECTED[cls]:
        return "correct" if cls != "ask" or right_fact else "wrong_fact"
    if cls == "ask" and kind == "DO" and item.get("file_checkable") and decision.settled and "settled" in (fact or ()):
        return "correct"
    return "wrong_question_kind" if kind in ("ASK", "CLARIFY") else "committed_without_asking" \
        if kind == "DO" else "refused_without_asking"


def main() -> None:
    gold = yaml.safe_load((HERE / "gold_readings.yaml").read_text(encoding="utf-8"))
    rows, by_class = [], {}
    for key in sorted(gold):
        item, raw = ITEMS[key], gold[key]
        decision = decide_menu(reading(raw), item["prompt"])
        outcome = score(item, decision, raw.get("fact"))
        by_class.setdefault(item["class"], []).append(outcome == "correct")
        rows.append((key, item["class"], decision.kind, decision.workflows,
                     [q.dimension for q in decision.questions], outcome,
                     [r for d in decision.declined for r in d.reasons][:2], decision.settled))
    right = sum(row[5] == "correct" for row in rows)
    for row in rows:
        if row[5] != "correct" or "--show" in sys.argv:
            print(f"{row[0]} {row[1]:5} {row[2]:8} {','.join(row[3]) or '-':40} q={row[4]} {row[5]} "
                  f"{row[6] or ''} {'settled' if row[7] else ''}")
    print("per class:", {cls: f"{sum(v)}/{len(v)}" for cls, v in sorted(by_class.items())})
    print(f"phase 0 gate: {right}/{len(rows)} (needs >= 52) -> {'PASS' if right >= 52 else 'FAIL'}")
    out = HERE / "phase0-result.json"
    out.write_text(json.dumps([dict(zip(("id", "class", "kind", "workflows", "questions", "outcome", "reasons",
                                         "settled"), row)) for row in rows], indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
