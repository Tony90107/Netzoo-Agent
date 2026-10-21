"""ROUND-11 (collab/ROUND-11-PLAN.md) Q1 and Q3: which request pieces each recorded reading files as results, scored
against the 56 gold readings of closed-menu phase 0. No model calls.

Gold pieces (gold_readings.yaml `wanted`): D a result asked for (no form; a question about which method gives a named
result is D too), Q a question to us that names no result (question_to_us), P a purpose. Live-shape reading pieces:
every ask, first read or re-read, is D; every about_methods quote is Q; the live shape has no per-piece purpose.
Two quotes match when their spans in the request overlap by at least half of the shorter one (`--any` scores any
overlap instead, as the plan's sensitivity check). Each read piece is paired with at most one gold piece, largest
overlap first. The rule was fixed in the plan before any reading was scored.

Usage:
  python3 units.py --self-test          the gold readings scored as readings: 64/64 right, no extra result
  python3 units.py score OUT.json [--any]
"""
from __future__ import annotations

import glob
import json
import sys
from collections import Counter
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
WT = HERE.parents[2]
MAIN = WT.parents[1] / "netzoo_agent"
sys.path.insert(0, str(WT / "scripts"))
GOLD = WT / "docs/research-log/closed-menu-phase0-2026-10-18/gold_readings.yaml"
ITEMS = WT / "docs/research-log/core-judgment-2026-10-15/items.json"
LIVE = MAIN / "docs/research-log/core-judgment-2026-10-15/live"
V7 = WT / "docs/research-log/closed-menu-phase1-2026-10-18/live/p1/bench.json"
ROUNDS = {"p4b": "gpt-4o-mini", "p4c": "gpt-4o-mini", "p5r": "gpt-4o-mini", "g4o1": "gpt-4o", "g4o2": "gpt-4o"}
KIND = {"do": "DO", "dont": "DECLINE", "ask": "ASK", "vague": "CLARIFY"}
FORM = {"deliverable": "D", "question_to_us": "Q", "purpose": "P", "data_description": "N", "context": "N"}


def items() -> dict:
    return {i["id"]: {"task": i["prompt"], "gold": KIND[i["class"]]}
            for i in json.loads(ITEMS.read_text())["items"]}


def gold() -> dict:
    found = {}
    for item, reading in yaml.safe_load(GOLD.read_text()).items():
        found[item] = {
            "units": [{"quote": w["quote"], "type": FORM[w.get("form", "deliverable")]} for w in reading["wanted"]],
            "settings": [s["quote"] for s in reading.get("settings", []) if s.get("quote")],
        }
    return found


def span(task: str, quote: str):
    """The quote's span in the request; a quote eliding its middle with "..." spans its first to its last part."""
    from netzoo_agent_core.interpretation.request_spans import _span
    if not quote:
        return None
    parts = [part.strip() for part in quote.replace("…", "...").split("...") if part.strip()]
    if len(parts) < 2:
        return _span(task, quote)
    found, start = [], 0
    for part in parts:
        place = _span(task[start:], part)
        if place is None:
            return None
        found.append((start + place[0], start + place[1]))
        start += place[1]
    return found[0][0], found[-1][1]


def overlap(a, b) -> int:
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


def matches(a, b, rule: str) -> int:
    """The overlap of two spans when it counts as a match under `rule`, else 0."""
    if a is None or b is None:
        return 0
    shared = overlap(a, b)
    if rule == "any":
        return shared
    return shared if shared and shared * 2 >= min(a[1] - a[0], b[1] - b[0]) else 0


def live_units(proposal: dict, reread: dict | None) -> list[dict]:
    """The reading's pieces: each ask is D, each about_methods quote is Q (first read, then the re-read's asks)."""
    units = []
    for source, payload in (("read", proposal), ("reread", (reread or {}).get("reread") or {})):
        for name, sentence in payload.items():
            if not name[1:].isdigit():
                continue
            for index, ask in enumerate(sentence.get("asks") or []):
                units.append({"quote": ask["quote"], "type": "D", "where": [source, name, "asks", index]})
            for index, quote in enumerate(sentence.get("about_methods") or []):
                units.append({"quote": quote, "type": "Q", "where": [source, name, "about_methods", index]})
    return units


def score(task: str, truth: dict, units: list[dict], rule: str = "half") -> dict:
    """Each gold piece's outcome and each extra result piece's class, for one reading.

    Gold D: `read` (a D piece paired with it), `as_question` (only a Q piece matches it), `missed`.
    Gold Q / P: `as_result` (a D piece paired with it), `right` otherwise.
    Extra D pieces (paired with no gold piece), in reading order: E2 a repeat -- on an already paired gold piece or on
    an earlier extra piece; otherwise E1 a gold setting's words, E3 anything else (background or data filed as a
    result). The first copy of an extra piece is classed by its words; only later copies are repeats.
    """
    golds = [{**g, "span": span(task, g["quote"])} for g in truth["units"]]
    reads = [{**u, "span": span(task, u["quote"])} for u in units]
    settings = [span(task, quote) for quote in truth["settings"]]
    # Largest overlap first; on a tie the earlier piece (the first read before its re-read) is paired.
    pairs = sorted(((matches(r["span"], g["span"], rule), ri, gi)
                    for ri, r in enumerate(reads) if r["type"] == "D"
                    for gi, g in enumerate(golds)), key=lambda p: (-p[0], p[1], p[2]))
    paired_read, paired_gold = {}, {}
    for shared, ri, gi in pairs:
        if shared and ri not in paired_read and gi not in paired_gold:
            paired_read[ri], paired_gold[gi] = gi, ri
    outcomes = []
    for gi, g in enumerate(golds):
        if g["type"] == "D":
            if gi in paired_gold:
                outcome = "read"
            elif any(matches(r["span"], g["span"], rule) for r in reads if r["type"] == "Q"):
                outcome = "as_question"
            else:
                outcome = "missed"
        else:
            outcome = "as_result" if gi in paired_gold else "right"
        outcomes.append({"quote": g["quote"], "type": g["type"], "outcome": outcome,
                         "read_as": reads[paired_gold[gi]]["quote"] if gi in paired_gold else None})
    extras, earlier, pieces = [], [], []
    for ri, r in enumerate(reads):
        if r["type"] != "D":
            continue
        if ri in paired_read:
            pieces.append({"where": r.get("where"), "paired": golds[paired_read[ri]]["type"], "extra": None})
            continue
        repeats = next((golds[gi]["type"] for gi in paired_gold if matches(r["span"], golds[gi]["span"], rule)), None)
        if repeats is None and any(matches(r["span"], s, rule) for s in earlier):
            repeats = "extra"
        if repeats is not None:
            label = "E2"
        elif any(matches(r["span"], s, rule) for s in settings):
            label = "E1"
        else:
            label = "E3"
        earlier.append(r["span"])
        extras.append({"quote": r["quote"], "class": label, "where": r.get("where"), "located": r["span"] is not None})
        pieces.append({"where": r.get("where"), "paired": None, "extra": label, "repeats": repeats})
    right = all(o["outcome"] in ("read", "right") for o in outcomes) and not extras
    return {"gold": outcomes, "extra": extras, "all_right": right, "pieces": pieces,
            "unlocated": [r["quote"] for r in reads if r["span"] is None]}


def recorded(round_name: str):
    """(item, folder, task, first-read proposal, re-read payload or None, check-failed flag) per session."""
    for path in sorted(glob.glob(str(LIVE / round_name / "cj-*" / "t1" / "events.jsonl"))):
        folder = Path(path).parent
        item = folder.parent.name.split("-")[2]
        events = [json.loads(line) for line in open(path) if line.strip()]
        users = [m["content"] for m in json.loads((folder / "session.json").read_text())["messages"]
                 if m["role"] == "user"]
        proposal = reread = None
        for index, event in enumerate(events):
            if event["event_type"] == "routing.capability_checked" and event["payload"].get("proposal"):
                proposal = event["payload"]["proposal"]
                for later in events[index + 1:]:
                    if later["event_type"] == "routing.capability_checked":
                        break
                    if later["event_type"] == "routing.capability_reread":
                        reread = later["payload"]
                        break
                break
        failed = any(e["event_type"] == "routing.capability_check_failed" for e in events)
        yield item, folder, users[0], proposal, reread, failed


def v7_units(reading: dict) -> list[dict]:
    return [{"quote": w["quote"], "type": FORM[w.get("form", "deliverable")], "where": ["wanted", index]}
            for index, w in enumerate(reading.get("wanted") or [])]


def score_v7(task: str, truth: dict, units: list[dict], rule: str = "half") -> dict:
    """Q3: the live-shape view (only D pieces are results) plus each gold piece's read form (D/Q/P/N/none)."""
    found = score(task, truth, [u for u in units if u["type"] == "D"], rule)
    golds = [span(task, g["quote"]) for g in truth["units"]]
    reads = [(span(task, u["quote"]), u["type"]) for u in units]
    for g, gold_span in zip(found["gold"], golds):
        best = max(((matches(s, gold_span, rule), t) for s, t in reads), default=(0, None))
        g["form_read"] = best[1] if best[0] else "none"
    return found


def run(out: str, rule: str):
    truth, tasks = gold(), items()
    rows = []
    for name, model in ROUNDS.items():
        for item, folder, task, proposal, reread, failed in recorded(name):
            if item not in truth:
                continue
            row = {"round": name, "model": model, "item": item, "gold_kind": tasks[item]["gold"],
                   "where": str(folder.relative_to(MAIN)), "check_failed": failed}
            if task != tasks[item]["task"]:
                row["task_differs"] = True
            if proposal is None:
                row["status"] = "no_proposal"
            else:
                row["status"] = "read"
                row["goal"] = (proposal.get("conditions") or {}).get("goal")
                row.update(score(task, truth[item], live_units(proposal, reread), rule))
            rows.append(row)
    bench = json.loads(V7.read_text())
    for found in bench["rows"]:
        if found["id"] not in truth:
            continue
        task = tasks[found["id"]]["task"]
        row = {"round": f"v7-{found['rep']}", "model": "gpt-4o-mini", "item": found["id"],
               "gold_kind": tasks[found["id"]]["gold"], "status": found["status"], "kind": found["kind"]}
        row.update(score_v7(task, truth[found["id"]], v7_units(found.get("reading") or {}), rule))
        rows.append(row)
    Path(out).write_text(json.dumps({"rule": rule, "rows": rows}, indent=1, ensure_ascii=False))
    report(rows)


def report(rows: list[dict]):
    for name in [*ROUNDS, "v7-0", "v7-1"]:
        mine = [r for r in rows if r["round"] == name]
        read = [r for r in mine if r["status"] == "read"]
        outcomes = Counter((g["type"], g["outcome"]) for r in read for g in r["gold"])
        extras = Counter(e["class"] for r in read for e in r["extra"])
        right = sum(r["all_right"] for r in read)
        unlocated = sum(len(r["unlocated"]) for r in read)
        print(f"{name:5} readings {len(read)}/{len(mine)} all right {right}  "
              f"D read {outcomes[('D', 'read')]} missed {outcomes[('D', 'missed')]} "
              f"as_question {outcomes[('D', 'as_question')]}  "
              f"Q as_result {outcomes[('Q', 'as_result')]}/{outcomes[('Q', 'as_result')] + outcomes[('Q', 'right')]}  "
              f"P as_result {outcomes[('P', 'as_result')]}/{outcomes[('P', 'as_result')] + outcomes[('P', 'right')]}  "
              f"extra {dict(sorted(extras.items()))}  unlocated {unlocated}")


def self_test(rule: str):
    truth, tasks = gold(), items()
    total = right = extra = unlocated = 0
    for item, reading in truth.items():
        units = [{"quote": u["quote"], "type": u["type"]} for u in reading["units"] if u["type"] in ("D", "Q")]
        found = score(tasks[item]["task"], reading, units, rule)
        total += len(found["gold"])
        right += sum(g["outcome"] in ("read", "right") for g in found["gold"])
        extra += len(found["extra"])
        unlocated += sum(span(tasks[item]["task"], q) is None for q in [u["quote"] for u in reading["units"]]
                         + reading["settings"])
    print(f"self-test ({rule}): {right}/{total} gold pieces right, {extra} extra, {unlocated} gold quotes unlocated")
    return right == total and not extra and not unlocated


if __name__ == "__main__":
    args = sys.argv[1:]
    mode = "any" if "--any" in args else "half"
    if args[0] == "--self-test":
        sys.exit(0 if self_test(mode) else 1)
    run(args[1], mode)
