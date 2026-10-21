"""ROUND-15: does reading each judge call twice, and taking only what both reads say, make decisions steadier?

Four gpt-4o-mini reads of every recorded condition-check and second-opinion call with the text live sends: read 1 is
ROUND-14's arm A (usage-fields asked.json), reads 2-4 are ask_old.py's. Each reading is decided by B2 with:
  single     one read's answers (reads 1, 2, 3, 4)
  agree      two reads (1+2, 3+4); a pair both reads answer alike keeps that answer; a pair they answer differently is
             handled as live handles a call that gave no answer -- a condition pair is unchecked (`_not_checked`: its
             words unread, a run held, never a full gap), a second-opinion pair is not applied, and a second opinion
             left with no pair answers nothing (a full gap it was owed stays unconfirmed).
Measured on the readings with a re-asked call: right against gold, and steadiness -- the same decision from the two
independent runs of the same rule (single 1 vs 3 and 2 vs 4; agree 1+2 vs 3+4).

Usage: python3 simulate.py OUT.json
"""
from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "usage-fields-2026-10-21"))
import reask  # noqa: E402

harness, replay_full = reask.harness, reask.replay_full


def _reads() -> list[dict]:
    first = json.loads((HERE.parent / "usage-fields-2026-10-21/asked.json").read_text())["calls"]
    reads = [[c for c in first if c["arm"] == "A"]]
    reads += [json.loads((HERE / f"read{i}.json").read_text())["calls"] for i in (2, 3, 4)]
    return [{(c["key"], c["at"], c["call"]): c for c in read} for read in reads]


def _agree(one: dict, two: dict) -> dict:
    """The calls of two reads, each pair kept only where both reads answer it alike (None marks a dropped pair)."""
    merged = {}
    for ident, call in one.items():
        other = two[ident]["answers"]
        answers = (None if call["answers"] is None or other is None
                   else [a if a == b else None for a, b in zip(call["answers"], other)])
        merged[ident] = {**call, "answers": answers}
    return merged


def _events(found: list[dict], calls: list[dict]) -> list[dict]:
    found = copy.deepcopy(found)
    for call in calls:
        payload, answers = found[call["at"]]["payload"], call["answers"]
        if call["call"] == "condition-check":
            size = len(payload.get("pairs") or [])
            whole = (payload.get("pairs") or []) + (payload.get("own_sentence") or [])
            keep = [i for i, answer in enumerate(answers or []) if answer is not None]
            payload["pairs"] = [whole[i] for i in keep if i < size]
            payload["answers"] = [answers[i] for i in keep if i < size]
            payload["own_sentence"] = [whole[i] for i in keep if i >= size]
            payload["own_answers"] = [answers[i] for i in keep if i >= size]
        elif call["call"] == "condition-redirect":
            keep = [i for i, answer in enumerate(answers or []) if answer is not None]
            payload["redirect"] = [payload["redirect"][i] for i in keep]
            payload["redirected"] = [answers[i] for i in keep] or None
        else:
            keep = [i for i, answer in enumerate(answers or []) if answer is not None]
            if keep:
                payload["pairs"] = [payload["pairs"][i] for i in keep]
                payload["answers"] = [answers[i] for i in keep]
            else:
                payload["answers"] = None  # nothing answered: as a failed second opinion
    return found


def main(out: str):
    reads = _reads()
    rules = {f"single{i + 1}": read for i, read in enumerate(reads)}
    rules["agree12"], rules["agree34"] = _agree(reads[0], reads[1]), _agree(reads[2], reads[3])
    by_key = {}
    for ident in reads[0]:
        by_key.setdefault(ident[0], []).append(ident)
    rows = []
    for key, folder, sid, task, payload, reread, found, _n in harness.readings():
        if key not in by_key:
            continue
        gold = reads[0][by_key[key][0]]["gold"]
        row = {"session": sid, "gold": gold, "kinds": {}}
        for name, calls in rules.items():
            try:
                call = replay_full.replay(folder, task, payload, reread,
                                          _events(found, [calls[ident] for ident in by_key[key]]))
                row["kinds"][name] = call["kind"]
            except Exception as error:  # noqa: BLE001 -- the three 10-20 T01 readings of a withdrawn shape
                row["kinds"][name] = f"error:{type(error).__name__}"
        rows.append(row)
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    labelled = [r for r in rows if r["gold"]]
    print(f"{len(rows)} readings with a re-asked call; {len(labelled)} labelled")
    for name in rules:
        print(f"  {name:8} right {sum(r['kinds'][name] == r['gold'] for r in labelled)}")
    for a, b in (("single1", "single3"), ("single2", "single4"), ("agree12", "agree34")):
        same = sum(r["kinds"][a] == r["kinds"][b] for r in rows)
        print(f"  steadiness {a} vs {b}: same decision {same}/{len(rows)}")
    dropped = Counter()
    for name in ("agree12", "agree34"):
        for call in rules[name].values():
            dropped[call["call"]] += sum(answer is None for answer in call["answers"] or [])
    print(f"  pairs the two reads answered differently: {dict(dropped)}")
    moved = Counter((r["gold"], r["kinds"]["single1"], r["kinds"]["agree12"]) for r in labelled
                    if r["kinds"]["single1"] != r["kinds"]["agree12"])
    for key, n in moved.most_common():
        print(f"  single1 -> agree12 {n} x gold {key[0]}: {key[1]} -> {key[2]}")


if __name__ == "__main__":
    main(sys.argv[1])
