"""ROUND-11 tables for RESULTS.md, from units.json (Q1, Q3 pieces) and oracle.json (Q2, Q3 calls). No model calls.

Usage: python3 report.py units.json oracle.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict

MINI = ("p4b", "p4c", "p5r")
GPT4O = ("g4o1", "g4o2")


def pieces(rows):
    print("== Q1 gold pieces and extra results, per round")
    print("round | D read / missed / as question | Q as result | P as result | extra E1 E2(first read) E2(re-read) E3 "
          "| all right")
    for name in (*MINI, *GPT4O, "v7-0", "v7-1"):
        mine = [r for r in rows if r["round"] == name and r["status"] == "read"]
        out = Counter((g["type"], g["outcome"]) for r in mine for g in r["gold"])
        extra = Counter((e["class"], (e["where"] or ["?"])[0]) for r in mine for e in r["extra"])
        e2r = extra[("E2", "read")] + extra[("E2", "wanted")]
        print(f"{name} | {out['D', 'read']}/{out['D', 'missed']}/{out['D', 'as_question']} | "
              f"{out['Q', 'as_result']}/8 | {out['P', 'as_result']}/6 | "
              f"{extra['E1', 'read'] + extra['E1', 'reread'] + extra['E1', 'wanted']} {e2r} {extra['E2', 'reread']} "
              f"{extra['E3', 'read'] + extra['E3', 'reread'] + extra['E3', 'wanted']} | "
              f"{sum(r['all_right'] for r in mine)}/{len(mine)}")


def stability(rows):
    print("\n== Q1 stability: same outcome for the same gold piece in two reads")
    by = {(r["round"], r["item"]): r for r in rows if r["status"] == "read"}
    for a, b in (("p4b", "p4c"), ("g4o1", "g4o2"), ("v7-0", "v7-1")):
        same = total = right_same = right_total = 0
        flips = []
        for (name, item), row in by.items():
            other = by.get((b, item))
            if name != a or other is None:
                continue
            for g1, g2 in zip(row["gold"], other["gold"]):
                total += 1
                same += g1["outcome"] == g2["outcome"]
                if g1["outcome"] != g2["outcome"]:
                    flips.append(f"{item}:{g1['type']} {g1['outcome']}/{g2['outcome']}")
            right_total += 1
            right_same += row["all_right"] == other["all_right"]
        print(f"{a} vs {b}: piece outcome same {same}/{total}; reading all-right agrees {right_same}/{right_total}; "
              f"flips {flips}")


def attribution(units_rows, oracle_rows):
    print("\n== Q1 attribution: readings with a piece error, by B call right / wrong (mini)")
    typed = {(r["round"], r["item"]): not r["all_right"] for r in units_rows if r["status"] == "read"}
    found = Counter()
    for row in oracle_rows:
        if row["round"] not in MINI:
            continue
        right = row["calls"]["B"]["kind"] == row["gold"]
        found[("right" if right else "wrong", typed[(row["round"], row["item"])])] += 1
    for side in ("wrong", "right"):
        n = found[(side, True)] + found[(side, False)]
        print(f"B {side}: {found[(side, True)]}/{n} readings have a piece error")


def calls(oracle_rows, variants=("O-a", "O-b", "O-c", "O-ab", "O")):
    for group, names in (("mini", MINI), ("gpt-4o", GPT4O)):
        mine = [r for r in oracle_rows if r["round"] in names]
        wrong = [r for r in mine if r["calls"]["B"]["kind"] != r["gold"]]
        print(f"\n== Q2 {group}: {len(mine)} readings, B wrong {len(wrong)}")
        for variant in variants:
            fixed = [r for r in mine if r["calls"]["B"]["kind"] != r["gold"] and r["calls"][variant]["kind"] == r["gold"]]
            broke = [r for r in mine if r["calls"]["B"]["kind"] == r["gold"] and r["calls"][variant]["kind"] != r["gold"]]
            print(f"{variant}: fixed {len(fixed)} {[r['round'] + ':' + r['item'] for r in fixed]}; "
                  f"broke {len(broke)} {[r['round'] + ':' + r['item'] for r in broke]}")
        print("B wrong calls by gold -> B kind/basis:")
        for key, n in Counter((r["gold"], r["calls"]["B"]["kind"], r["calls"]["B"]["basis"])
                              for r in wrong).most_common():
            print(f"  {n:2d} {key}")
        differ = [r for r in mine if r["calls"]["B"]["kind"] != r["recorded"]]
        print(f"B differs from the recorded call: {len(differ)}")
        for r in differ:
            print(f"  {r['round']}:{r['item']} gold {r['gold']} recorded {r['recorded']} B {r['calls']['B']['kind']} "
                  f"({r['calls']['B']['basis']})")


def changed(oracle_rows, variant, names):
    print(f"\n== every call {variant} changed ({'/'.join(names)})")
    for r in oracle_rows:
        if r["round"] not in names:
            continue
        b, o = r["calls"]["B"], r["calls"][variant]
        if b["kind"] == o["kind"]:
            continue
        tag = "FIX" if o["kind"] == r["gold"] else "BREAK" if b["kind"] == r["gold"] else "other"
        print(f"{tag:5} {r['round']}:{r['item']} gold {r['gold']}: {b['kind']}/{b['basis']} -> {o['kind']}/{o['basis']} "
              f"{o['changed']}")


def v7(rows):
    print("\n== Q3 v7 calls")
    for variant in ("forms", "extras", "O"):
        found = Counter()
        for r in rows:
            a, b = r["calls"]["B"]["outcome"] == "correct", r["calls"][variant]["outcome"] == "correct"
            found["fixed" if b and not a else "broke" if a and not b else "same"] += 1
        print(f"{variant}: {dict(found)}")
    for r in rows:
        b, o = r["calls"]["B"], r["calls"]["O"]
        if (b["outcome"] == "correct") != (o["outcome"] == "correct") or b["kind"] != o["kind"]:
            tag = "FIX" if o["outcome"] == "correct" else "BREAK" if b["outcome"] == "correct" else "other"
            print(f"{tag:5} {r['round']}:{r['item']} gold {r['gold']}: {b['kind']} -> {o['kind']} {o['changed']}")
    print(f"B right {sum(r['calls']['B']['outcome'] == 'correct' for r in rows)}/{len(rows)}; "
          f"O right {sum(r['calls']['O']['outcome'] == 'correct' for r in rows)}/{len(rows)}")


def main(units_path, oracle_path):
    rows = json.loads(open(units_path).read())["rows"]
    oracle = json.loads(open(oracle_path).read())
    pieces(rows)
    stability(rows)
    attribution(rows, oracle["live"])
    calls(oracle["live"])
    for variant in ("O-ab", "O"):
        changed(oracle["live"], variant, MINI)
    v7(oracle["v7"])


if __name__ == "__main__":
    main(*sys.argv[1:3])
