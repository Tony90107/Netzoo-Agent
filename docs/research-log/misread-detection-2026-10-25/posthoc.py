"""Misread detection (ROUND.md), analyses made after the declared measurement -- labelled post hoc in RESULTS.md and
never used to pass a gate. No model calls.

1. X2 and Q2 by recording era (before the fact agent: p0, p1, p1b, cj1) and by the fact agent's status;
2. the union X2|Q2 (X2 asks the goal first), simulated as `measure.py` does;
3. every labelled reading where the hypothesis reader said unclear_goal or Q2 fired: gold kinds;
4. M: the closed-menu phase-1 reading's own call (`closed-menu-phase1-2026-10-18/live/p1/score.json`, two reads per
   core item) asking while the check's call acts, per core reading;
5. the 15 X5b false alarms of ROUND.md's spot check (seed 1025) and Q2's false alarm;
6. the readings a paid per-workflow read would cover.

Usage: python3 posthoc.py > posthoc.txt
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "harness-repair-2026-10-23"))
from score import kind_of  # noqa: E402

ACTING = ("DO", "DECLINE")
ASKING = ("ASK", "CLARIFY")
MEASURES = ("right", "FA", "FR", "MA", "wrong question kind", "extra questions", "UNCHECKED")
PRE_AGENT = {"p0", "p1", "p1b", "cj1"}
ROUND = re.compile(r"^(?:cj-([^-]+)-C\d+|hb-([^-]+)-[A-Z]\d+)-\d+$")


def era(row) -> str:
    found = ROUND.match(row["session"])
    return "before fact agent" if (found.group(1) or found.group(2)) in PRE_AGENT else "fact-agent era"


def target(row) -> bool:
    return row["error"] != "right" and row.get("layer") == "reading" and row.get("subtype") != "R-fail"


def has(row, *names) -> bool:
    return any(name in (row.get("signals") or {}) for name in names)


def union_kind(row) -> str | None:
    if row["call"] not in ACTING:
        return None
    return "CLARIFY" if has(row, "X2") else "ASK" if has(row, "Q2") else None


def simulated(rows, rule) -> str:
    before = Counter(kind_of(r["gold"], r["call"]) for r in rows)
    after = Counter(kind_of(r["gold"], rule(r) or r["call"]) for r in rows)
    return "  ".join(f"{m} {before[m]}->{after[m]}" for m in MEASURES)


def fact_status(where: dict, key: str) -> str:
    for line in open(Path(where[key]) / "events.jsonl"):
        if '"core.fact_check"' in line and (event := json.loads(line)).get("event_type") == "core.fact_check":
            return event["payload"].get("status")
    return "absent"


def main():
    rows = [r for r in json.loads((HERE / "signals-replay.json").read_text()) if r.get("gold") and r.get("error")]
    h7 = json.loads((HERE / "signals-h7.json").read_text())
    where = {k: v["where"] for k, v in json.loads((HERE.parent / "harness-repair-2026-10-23/pFinal.json")
                                                 .read_text()).items()}

    print("1. X2, Q2, X2|Q2 and X5b by era (acting calls only)")
    for name in ("before fact agent", "fact-agent era"):
        part = [r for r in rows if era(r) == name]
        targets, right = [r for r in part if target(r)], [r for r in part if r["error"] == "right"]
        print(f"  {name}: {len(part)} readings, {len(right)} right, {len(targets)} targets on "
              f"{len({r['item'] for r in targets})} items, {sum(r['call'] in ACTING for r in targets)} acting")
        for label, names in (("X2", ("X2",)), ("Q2", ("Q2",)), ("X2|Q2", ("X2", "Q2")), ("X5b", ("X5b",))):
            hit = [r for r in targets if r["call"] in ACTING and has(r, *names)]
            false = [r for r in right if r["call"] in ACTING and has(r, *names)]
            print(f"    {label:6} hits {len(hit):3}/{len(targets)} on {len({r['item'] for r in hit})} items "
                  f"{dict(Counter(r['subtype'] for r in hit))}; false alarms {len(false)}/{len(right)}")
    print("  fact agent status on X2|Q2 hits:",
          dict(Counter(fact_status(where, r["key"]) for r in rows
                       if target(r) and r["call"] in ACTING and has(r, "X2", "Q2"))))
    print("  fact agent status on every acting target:",
          dict(Counter(fact_status(where, r["key"]) for r in rows if target(r) and r["call"] in ACTING)))

    print("\n2. X2|Q2 simulated (X2 asks the goal first)")
    print("  all labelled:   ", simulated(rows, union_kind))
    print("  fact-agent era: ", simulated([r for r in rows if era(r) == "fact-agent era"], union_kind))
    hit = [r for r in rows if r["error"] != "right" and union_kind(r)]
    print(f"  errors flagged {len(hit)} on items {sorted({r['item'] for r in hit})}")
    print(f"  by error {dict(Counter(r['error'] for r in hit))}; MA total {sum(r['error'] == 'MA' for r in rows)}")

    print("\n3. gold kinds where the readings say the user is unsure or the goal is unclear (any call)")
    for name in ("X2", "Q2"):
        found = [r for r in rows if has(r, name)]
        print(f"  {name}: {len(found)} labelled readings; gold {dict(Counter(r['gold'] for r in found))}; "
              f"calls {dict(Counter(r['call'] for r in found))}")
    print(f"  all labelled readings: gold {dict(Counter(r['gold'] for r in rows))}")
    h7_unclear = [r for r in h7 if has(r, "X2")]
    print(f"  h7 sessions with X2 (any call): {len(h7_unclear)}; expected {dict(Counter(r['expected'] for r in h7_unclear))};"
          f" acting {[(r['id'], r['call'], r['subtype']) for r in h7_unclear if r['call'] in ACTING]}")

    print("\n4. M (post hoc): the closed-menu reading of the same core item asks, the check's call acts")
    menu = json.loads((HERE.parent / "closed-menu-phase1-2026-10-18/live/p1/score.json").read_text())
    core = [r for r in rows if r.get("set") == "core"]
    for arm in ("first", "focused"):
        kinds = menu["arms"][arm]["kinds"]
        for mode, test in (("both reads", all), ("either read", any)):
            def flag(r):
                read = kinds.get(r["item"])
                return bool(read) and r["call"] in ACTING and test(k in ASKING for k in read[:2])
            targets, right = [r for r in core if target(r)], [r for r in core if r["error"] == "right"]
            hit, false = [r for r in targets if flag(r)], [r for r in right if flag(r)]
            print(f"  {arm:8} {mode:11}: hits {len(hit)}/{len(targets)} on {len({r['item'] for r in hit})} items "
                  f"{dict(Counter(r['subtype'] for r in hit))}; false alarms {len(false)}/{len(right)} on "
                  f"{len({r['item'] for r in false})} items {sorted({r['item'] for r in false})}")
    kinds = menu["arms"]["focused"]["kinds"]
    acting = [r for r in core if target(r) and r["call"] in ACTING]
    both = [r for r in acting if r["item"] in kinds and all(k in ASKING for k in kinds[r["item"]][:2])]
    print(f"  core acting targets {len(acting)}: X2|Q2 {sum(has(r, 'X2', 'Q2') for r in acting)}, M (focused, both) "
          f"{len(both)}, M only {dict(Counter(r['subtype'] for r in both if not has(r, 'X2', 'Q2')))}, "
          f"M or X2|Q2 {sum(has(r, 'X2', 'Q2') or r in both for r in acting)}")

    print("\n5. spot check (ROUND.md: seed 1025)")
    for r in rows:
        if r["error"] == "right" and r["call"] in ACTING and has(r, "Q2"):
            print(f"  Q2 false alarm {r['session']} gold {r['gold']} {r['call']}/{r['basis']}: {r['request'][:160]!r}")
    false = [r for r in rows if r["error"] == "right" and r["call"] in ACTING and has(r, "X5b")]
    for r in random.Random(1025).sample(false, 15):
        print(f"  X5b false alarm {r['session']} gold {r['gold']} {r['call']}/{r['basis']}")
        print(f"      request {r['request'][:200]!r}")
        print(f"      agent's words {r['signals']['X5b'][:180]}")

    print("\n6. readings a per-workflow read would cover (DO calls; X2|Q2 do not flag them)")
    errors = [r for r in rows if target(r) and r["call"] == "DO" and not has(r, "X2", "Q2")]
    print(f"  replay errors {len(errors)} on {len({r['request'] for r in errors})} requests "
          f"{dict(Counter((r['error'], r['subtype']) for r in errors))}")
    print(f"    items {sorted({r['item'] for r in errors})}")
    live = [r for r in h7 if r["part"] == "single" and r.get("layer") == "reading" and r.get("call") == "DO"]
    print(f"  h7 single errors {len(live)}: {[(r['id'], r['subtype']) for r in live]}")
    right = [r for r in rows if r["error"] == "right" and r["call"] == "DO"]
    print(f"  controls: replay right DO {len(right)} {dict(Counter(r['set'] for r in right))} on "
          f"{len({r['request'] for r in right})} requests; h7 right single DO "
          f"{sum(r['part'] == 'single' and r.get('outcome') == 'correct' and r.get('call') == 'DO' for r in h7)}")


if __name__ == "__main__":
    main()
