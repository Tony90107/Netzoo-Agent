"""A1' confirmation scoring (ROUND-A1C.md; the pass conditions declared at the end of RESULTS-A.md, before any h8 data).

The A1' arm is the call E3 made live (`core.decision` of the turn); the A3-only arm is the same recorded reading decided
by the A3-only snapshot (`redecide.py`). E3's own replay must reproduce the live call; every mismatch is listed.

Calls: DO, PARTIAL (a DO whose core marks part not available), DECLINE, ASK, CLARIFY, UNCHECKED. Outcomes as P5's
`score_p5.outcome` on the call kind: FA = false_accept, partly_accept; FR = false_refusal, partial_refusal,
over_refusal; MA = committed_without_asking, refused_without_asking; a needless question is a cost, not an error.

Usage: python3 score_a1c.py E3.json A3.json [E3b.json A3b.json]   (pairs of redecide outputs; the second pair is the
       conditional second round)
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ITEMS = HERE.parent / "h8" / "items.json"
WAITING = ("ASK", "CLARIFY")
FAMILY = {"false_accept": "FA", "partly_accept": "FA", "false_refusal": "FR", "partial_refusal": "FR",
          "over_refusal": "FR", "committed_without_asking": "MA", "refused_without_asking": "MA",
          "needless_question": "cost", "wrong_question_kind": "kind"}


def call(kind, partial) -> str:
    return "PARTIAL" if kind == "DO" and partial else (kind or "NONE")


def outcome(expected: str, also: list, got: str) -> str:
    if got in {expected, *(also or [])}:
        return "correct"
    if got == "UNCHECKED":
        return "unchecked"
    if got in ("NONE", "no_reading", "error"):
        return "no_call"
    if expected == "DO":
        return {"PARTIAL": "partial_refusal", "DECLINE": "false_refusal"}.get(got, "needless_question")
    if expected == "PARTIAL":
        return {"DO": "false_accept", "DECLINE": "over_refusal"}.get(got, "needless_question")
    if expected == "DECLINE":
        return {"DO": "false_accept", "PARTIAL": "partly_accept"}.get(got, "undecided")
    if got in WAITING:
        return "wrong_question_kind"
    return "committed_without_asking" if got == "DO" else "refused_without_asking"


def item_of(session: str) -> str:
    return next(part for part in session.split("-") if part.startswith("Y"))


def rows(e3_path: str, a3_path: str, items: dict) -> list[dict]:
    e3 = {r["session"]: r for r in json.loads(Path(e3_path).read_text())}
    a3 = {r["session"]: r for r in json.loads(Path(a3_path).read_text())}
    found = []
    for session, live in sorted(e3.items()):
        item = items[item_of(session)]
        live_call = call(live["recorded"], live.get("recorded_partial"))
        replayed = call(live["kind"], live.get("partial"))
        other = a3[session]
        a3_call = call(other["kind"], other.get("partial"))
        found.append({"session": session, "item": item["id"], "category": item["category"], "sub": item["sub"],
                      "gold": item["expected_call"], "a1": live_call, "a1_basis": live.get("recorded_basis"),
                      "e3_replay": replayed, "a3": a3_call, "a3_basis": other.get("basis"),
                      "a1_outcome": outcome(item["expected_call"], item.get("also_acceptable"), live_call),
                      "a3_outcome": outcome(item["expected_call"], item.get("also_acceptable"), a3_call)})
    return found


def main(paths: list[str]):
    items = {i["id"]: i for i in json.loads(ITEMS.read_text())["single"]}
    found = [row for e3, a3 in zip(paths[::2], paths[1::2]) for row in rows(e3, a3, items)]
    mismatch = [r for r in found if r["e3_replay"] != r["a1"]]
    changed = [r for r in found if r["a1"] != r["a3"]]
    right = [r for r in changed if r["a1_outcome"] == "correct" and r["a3_outcome"] != "correct"]
    wrong = [r for r in changed if r["a3_outcome"] == "correct" and r["a1_outcome"] != "correct"]
    new_fa = [r for r in found if FAMILY.get(r["a1_outcome"]) == "FA" and FAMILY.get(r["a3_outcome"]) != "FA"]
    open_choice = [r for r in found if r["category"] == "C" and r["sub"] != "stated_result"]
    choice_do = [r for r in open_choice if r["a1"] in ("DO", "PARTIAL")]
    print(f"{len(found)} readings; E3 replay reproduces the live call on {len(found) - len(mismatch)}")
    for r in mismatch:
        print(f"  MISMATCH {r['session']}: live {r['a1']} ({r['a1_basis']}) vs replay {r['e3_replay']}")
    print(f"\nchanged decisions (A1' vs A3-only on the same reading): {len(changed)}")
    for r in changed:
        tag = "RIGHT" if r in right else "WRONG" if r in wrong else "other"
        print(f"  {tag:5} {r['session']} [{r['category']}/{r['sub']}] gold {r['gold']}: A3-only {r['a3']} "
              f"({r['a3_basis']}) -> A1' {r['a1']} ({r['a1_basis']})")
    print("\nconditions (RESULTS-A, declared before the data):")
    print(f"  1. new FA in the A1' arm: {len(new_fa)} {[r['session'] for r in new_fa]}")
    print(f"  2. open-choice C items run as DO in the A1' arm: {len(choice_do)} of {len(open_choice)} "
          f"{[r['session'] for r in choice_do]}")
    print(f"  3. changed decisions right {len(right)} vs wrong {len(wrong)} "
          f"(neither {len(changed) - len(right) - len(wrong)})")
    print(f"  4. wrong changes listed above: {[r['session'] for r in wrong]}")
    verdict = ("INCONCLUSIVE (fewer than 4 changed decisions)" if len(changed) < 4
               else "PASS" if not new_fa and not choice_do and len(right) > len(wrong) else "FAIL")
    print(f"  verdict: {verdict}")
    print("\nabsolute (not a gate): correct per category, A1' arm vs A3-only arm")
    for cat in "RFCK":
        mine = [r for r in found if r["category"] == cat]
        print(f"  {cat}: {sum(r['a1_outcome'] == 'correct' for r in mine)}/{len(mine)} vs "
              f"{sum(r['a3_outcome'] == 'correct' for r in mine)}/{len(mine)}")
    for arm in ("a1", "a3"):
        fam = Counter(FAMILY.get(r[f"{arm}_outcome"], r[f"{arm}_outcome"]) for r in found)
        print(f"  {arm}: {dict(sorted(fam.items()))}")
    out = HERE / "score-a1c.json"
    out.write_text(json.dumps({"rows": found, "verdict": verdict, "changed": len(changed), "right": len(right),
                               "wrong": len(wrong), "new_fa": len(new_fa), "choice_do": len(choice_do),
                               "mismatch": len(mismatch)}, indent=1) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
