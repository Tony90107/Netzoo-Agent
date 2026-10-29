"""P4 scoring (ROUND.md): j7, arms j7off / j7on paired by item. No model calls.

Right / FA / FR / MA as j4-j6 (`harness-repair-2026-10-23/score.kind_of`; PARTIAL counted as DO; final gold =
`final_after_fact` / `final_after_result` when that reply was sent, else the opening expected_call). Also reported:
strict right (a DO final whose workflows are within the gold's), and Jev's link vs the reading's per ask.

Usage: python3 score_j7.py > RESULTS-J7.txt   (also writes score-j7.json)
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "harness-repair-2026-10-23"))
sys.path.insert(0, str(HERE.parent / "jev-j6-2026-10-29"))
from score import kind_of  # noqa: E402
from score_j6 import GROUPS, MEASURES, events, kind  # noqa: E402


def sessions(tag: str, items: dict) -> dict:
    rows = {}
    for folder in sorted((HERE / "live" / tag).glob(f"hb-{tag}-*-1")):
        item = items[folder.name.split("-")[2]]
        job = json.loads((folder / "job.json").read_text())
        turns = sorted(folder.glob("t*"), key=lambda p: int(p.name[1:]))
        cores = [(events(t, "core.decision") or [{}])[-1] for t in turns]
        final = "fact" if "fact" in job["sent"] else "result" if "result" in job["sent"] else None
        gold_item = item[f"final_after_{final}"] if final else {"call": item["expected_call"],
                                                                "workflows": item["workflows"]}
        gold = kind(gold_item["call"])
        last = cores[-1] if cores else {}
        allowed = set(gold_item.get("workflows") or []) | set(item.get("also_acceptable_workflows") or [])
        verdict = kind_of(gold, last.get("kind") or "none")
        strict = verdict == "right" and (gold != "DO" or (bool(last.get("workflows"))
                                                          and set(last["workflows"]) <= allowed))
        links = [read for t in turns for e in events(t, "core.jev_links_first") for read in e.get("reads", [])]
        rows[item["id"]] = {"id": item["id"], "group": item["category"], "gold": gold,
                            "gold_workflows": sorted(allowed), "sent": job["sent"],
                            "t1": f"{cores[0].get('kind')}/{cores[0].get('basis')}" if cores else "none",
                            "final": last.get("kind") or "none", "workflows": last.get("workflows") or [],
                            "verdict": verdict, "strict": strict, "links": links}
    return rows


def main():
    items = {i["id"]: i for i in json.loads((HERE / "j7" / "items.json").read_text())["single"]}
    arms = {tag: sessions(tag, items) for tag in ("j7off", "j7on")}
    keys = sorted(set(arms["j7off"]) & set(arms["j7on"]))
    print(f"j7: {len(keys)} paired conversations of {len(items)}")
    summary = {}
    for tag, rows in arms.items():
        s = Counter(rows[k]["verdict"] for k in keys)
        strict = sum(rows[k]["strict"] for k in keys)
        summary[tag] = {"counts": s, "strict": strict}
        print(f"  {tag}: right {s['right']}/{len(keys)}  strict {strict}  " +
              "  ".join(f"{m} {s[m]}" for m in MEASURES[1:]))
    off, on = arms["j7off"], arms["j7on"]
    changed = [k for k in keys if (off[k]["verdict"], off[k]["workflows"]) != (on[k]["verdict"], on[k]["workflows"])]
    print("\nchanged items (off -> on):")
    for k in changed:
        print(f"  {k} | {off[k]['group']} | gold {off[k]['gold']} {off[k]['gold_workflows']} | "
              f"{off[k]['final']} {off[k]['workflows']} {off[k]['verdict']} -> {on[k]['final']} {on[k]['workflows']} "
              f"{on[k]['verdict']}")
    applied = [(k, read) for k in keys for read in on[k]["links"] if read.get("pick") is not None]
    print(f"\nJev links in arm on: {sum(len(on[k]['links']) for k in keys)} reads, {len(applied)} confident "
          f"(>= 0.7), errors {sum('error' in r for k in keys for r in on[k]['links'])}")
    print("\nid | group | gold | off: t1 -> final [workflows] verdict | on: t1 -> final [workflows] verdict")
    for k in sorted(keys, key=lambda k: (GROUPS.index(off[k]["group"]) if off[k]["group"] in GROUPS else 99, k)):
        print(f"  {k} | {off[k]['group']} | {off[k]['gold']} | {off[k]['t1']} -> {off[k]['final']} {off[k]['workflows']} "
              f"{off[k]['verdict']} | {on[k]['t1']} -> {on[k]['final']} {on[k]['workflows']} {on[k]['verdict']}")
    (HERE / "score-j7.json").write_text(json.dumps({"summary": summary, "changed": changed,
                                                    "rows": arms}, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
