"""Closed-menu phase 1, dev rounds: the reader's schema shape is tuned here only (never on the 56-item bench).

Dev sets: heldout11-19, accept24, m3 heldout -- already seen, deduplicated by prompt, English, single-turn. They have
no gold readings, so a round is judged by what the phase-0 missed-field check said matters: doubts read as doubts and
limits read as limits.

  ask   every needs_fact item (the user's own doubt decides the workflow): asked (ASK/CLARIFY) is right; a doubt read
        anywhere in the reading is the doubt-recall proxy
  dont  not_supported items whose reason is a limit (setting, count, data the user lacks, a condition): DECLINE right
  do    supported items (plain, needs_input or with_step): DECLINE or a partial DO is a false refusal; ASK/CLARIFY is
        counted apart (the new design asks unstated intents the old labels assumed)

Usage: dev.py select                         -> dev_items.json (seeded, written once)
       dev.py read TAG [--only ids] [--focus]  -> live/TAG/dev.json (one gpt-4o-mini read per item; --focus: then
                                                  the focused re-read of the candidates, recorded beside it)
       dev.py read TAG --focus --requirements  -> also the requirement contract check on the latest reading
       dev.py read TAG --focus --requirements --probe -> and the intent-probe arm beside it (--final-probe)
       dev.py score TAG [TAG2] [--focused|--final] -> summary (--focused: the merged reading where the re-read ran;
                                                  --final: every stage), and the items whose call changed
"""
from __future__ import annotations

import json
import random
import re
import sys

from p1common import HERE, LOGS, git_head, read_many, write

SETS = ["requirement-verdicts-2026-10-10/heldout11.json", "checked-no-result-2026-10-11/heldout12.json",
        "checked-match-2026-10-11/heldout13.json", "reread-2026-10-11/heldout14.json",
        "executability-score-2026-10-11/heldout15.json", "follow-up-conditions-2026-10-12/heldout16.json",
        "rescore-2026-10-12/heldout17.json", "request-conditions-2026-10-12/heldout18.json",
        "unknown-conditions-2026-10-12/heldout19.json", "final-acceptance-2026-10-14/accept24.json",
        "m3-clarification-2026-10-15/heldout.json"]
SHORT = {name: (name.split("/")[1].removesuffix(".json") if "heldout1" in name else
                "accept24" if "accept24" in name else "m3") for name in SETS}
CJK = re.compile(r"[一-鿿]")
# Words in a not_supported item's gold note that say a limit -- a setting, a count, data, a condition -- decides it.
LIMIT = re.compile(r"(at least|requires? (more|at least)|minimum|maximum|cap\b|setting|parameter|lambda|penalty|"
                   r"no (control|option)|cannot take|single[- ]cell|individual cells|same (samples|patients)|"
                   r"different (samples|patients|mice)|binary|germline|three or more|layers|without (a|any)|"
                   r"mutation matri|expression is explicitly|dynamic|spatial|overlapping)", re.I)
DO = {"supported", "needs_input", "with_step"}
# Families whose not_supported items are a condition or limit away from a supported one (each set's `about`).
LIMIT_FAMILIES = {"N", "CS", "UN"}


def candidates() -> list[dict]:
    seen, found = set(), []
    for name in SETS:
        for item in json.loads((LOGS / name).read_text())["items"]:
            prompt = item.get("prompt")
            if not prompt or item.get("turns") or CJK.search(prompt) or prompt in seen:
                continue
            seen.add(prompt)
            expects = {r.get("expect") for r in item.get("requirements") or []}
            notes = " ".join(r.get("note", "") + " " + r.get("deciding_fact", "") for r in item["requirements"]) \
                if item.get("requirements") else ""
            limit = LIMIT.search(notes) or item["family"] in LIMIT_FAMILIES
            cls = ("ask" if expects == {"needs_fact"} else "dont" if expects == {"not_supported"} and limit
                   else "do" if expects and expects <= DO else None)
            if cls:
                found.append({"id": f"{SHORT[name]}:{item['id']}", "set": name.split("/")[0],
                              "family": item["family"], "class": cls, "prompt": prompt,
                              "workflows": sorted({w for r in item["requirements"] for w in r.get("by") or []}),
                              "note": notes[:300]})
    return found


def select() -> None:
    path = HERE / "dev_items.json"
    if path.exists():
        sys.exit("dev_items.json exists; the dev set is chosen once")
    pool, rng = candidates(), random.Random(1018)
    chosen = [i for i in pool if i["class"] == "ask"]
    for cls, size in (("dont", 22), ("do", 22)):
        chosen += rng.sample([i for i in pool if i["class"] == cls], size)
    write(path, {"about": __doc__.split("\n\n")[1], "pool": {c: sum(i["class"] == c for i in pool)
                                                              for c in ("ask", "dont", "do")}, "items": chosen})
    print({c: sum(i["class"] == c for i in chosen) for c in ("ask", "dont", "do")})


def doubt_read(reading: dict) -> list[str]:
    found = []
    for index, item in enumerate(reading.get("wanted") or []):
        for name, value in item.items():
            if isinstance(value, dict) and value.get("status") in ("unsure", "conflicting"):
                found.append(f"wanted[{index}].{name}")
    for name, value in (reading.get("conditions") or {}).items():
        if value.get("status") in ("unsure", "conflicting"):
            found.append(f"conditions.{name}")
    for name in ("sample_count", "feature_count", "claims", "delivery"):
        if (reading.get(name) or {}).get("status") in ("unsure", "conflicting"):
            found.append(name)
    found += [f"setting:{s['control']}" for s in reading.get("settings") or [] if s.get("unsure")]
    if reading.get("unsure_files"):
        found.append("unsure_files")
    return found


def read(tag: str, only=None, focus=False, requirements=False, probe=False) -> None:
    items = json.loads((HERE / "dev_items.json").read_text())["items"]
    if only:
        items = [i for i in items if i["id"] in only]
    from netzoo_agent_core.interpretation.menu_reader import READER_SHAPE
    rows = read_many([(item, 0) for item in items], focus=focus, requirements=requirements, probe=probe)
    write(HERE / "live" / tag / "dev.json", {"commit": git_head(), "shape": READER_SHAPE, "rows": rows})


def outcome(cls: str, row: dict) -> str:
    kind = row["kind"]
    if row["status"] == "failed":
        return "failed"
    if cls == "ask":
        return "asked" if kind in ("ASK", "CLARIFY") else "committed" if kind == "DO" else "refused"
    if cls == "dont":
        return "declined" if kind == "DECLINE" else "partial" if row["partial"] else \
            "asked" if kind in ("ASK", "CLARIFY") else "accepted"
    return "did" if kind == "DO" and not row["partial"] else "refused" if kind == "DECLINE" or row["partial"] else \
        "asked"


def score(tag: str, other: str | None = None) -> None:
    rows = json.loads((HERE / "live" / tag / "dev.json").read_text())["rows"]
    if "--focused" in sys.argv:  # the merged reading of the focused arm, where it ran; the first reading elsewhere
        rows = [{**row, **row["focus"]} if row.get("focus", {}).get("ran") and row["focus"].get("status") == "read"
                else row for row in rows]
    if "--final" in sys.argv:  # the last reading every stage left (first read, focused re-read, requirement check)
        rows = [{**row, **row["final"]} if "final" in row else row for row in rows]
    if "--final-probe" in sys.argv:  # the intent-probe arm (first read, re-read, intent probe, requirement check)
        rows = [{**row, **row["final_probe"]} if "final_probe" in row else row for row in rows]
    items = {i["id"]: i for i in json.loads((HERE / "dev_items.json").read_text())["items"]}
    table: dict[str, dict[str, int]] = {}
    for row in rows:
        cls = items[row["id"]]["class"]
        result = outcome(cls, row)
        table.setdefault(cls, {}).setdefault(result, 0)
        table[cls][result] += 1
        row["outcome"], row["doubts"] = result, doubt_read(row["reading"])
    asks = [r for r in rows if items[r["id"]]["class"] == "ask" and r["status"] != "failed"]
    meta = json.loads((HERE / "live" / tag / "dev.json").read_text())
    print("commit", meta["commit"], "shape", meta.get("shape", "v1"))
    print("calls:", json.dumps(table))
    print(f"ask items with a doubt read: {sum(bool(r['doubts']) for r in asks)}/{len(asks)}")
    dos = [r for r in rows if items[r["id"]]["class"] == "do" and r["status"] != "failed"]
    print(f"do items with a doubt read (precision): {sum(bool(r['doubts']) for r in dos)}/{len(dos)}")
    print(f"quotes dropped by code: {sum(len(r['dropped']) for r in rows)} in "
          f"{sum(bool(r['dropped']) for r in rows)}/{len(rows)} reads; failed {sum(r['status'] == 'failed' for r in rows)}")
    print(f"tokens in/out per read: {sum(r['input_tokens'] for r in rows) // max(1, len(rows))}/"
          f"{sum(r['output_tokens'] for r in rows) // max(1, len(rows))}; US${sum(r['usd'] for r in rows):.3f}")
    wrong = {"ask": ("committed", "refused"), "dont": ("accepted",), "do": ("refused",)}
    for row in rows:
        cls = items[row["id"]]["class"]
        if row["outcome"] in wrong[cls] or row["outcome"] == "failed":
            print(f"  {row['id']:24} {cls:4} {row['outcome']:9} {row['kind']:8} {','.join(row['workflows']) or '-':28} "
                  f"q={row['questions']} doubts={row['doubts']} {row['reasons'][:2]} {row['error'][:80]}")
    if other:
        before = {r["id"]: r for r in json.loads((HERE / "live" / other / "dev.json").read_text())["rows"]}
        flips = [(r["id"], before[r["id"]]["kind"], r["kind"]) for r in rows
                 if r["id"] in before and before[r["id"]]["kind"] != r["kind"]]
        print(f"calls changed vs {other}: {len(flips)}", flips)


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "select":
        select()
    elif command == "read":
        only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
        read(sys.argv[2], only, "--focus" in sys.argv, "--requirements" in sys.argv, "--probe" in sys.argv)
    else:
        args = [a for a in sys.argv[2:] if not a.startswith("--")]
        score(args[0], args[1] if len(args) > 1 else None)
