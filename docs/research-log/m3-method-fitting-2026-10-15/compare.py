"""Compare two or three `replay.py` outputs on round m3's gold and blind labels.

Usage: python docs/research-log/m3-method-fitting-2026-10-15/compare.py <base.json> <new.json> [<injected.json>] \
           [--out <changes.json>]

For every session's final turn, each gold requirement is matched to the check's result rows as round m3 scored
requirement reading (`m3-clarification-2026-10-15/collect.py`: both quotes in the request, overlapping at least half
the gold words), and its verdict is summarised as the rows' statuses plus, for a run, the run verdict. The recorded
blind label (after adjudication) is shown beside it. A supported requirement whose rows lose `available`, or whose run
loses an approving verdict, is listed as a new refusal.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
M3 = HERE.parent / "m3-clarification-2026-10-15"
sys.path.insert(0, str(M3))

from collect import quote_match  # noqa: E402

APPROVING = {"agrees"}
FALSE_ACCEPTS = ["K02", "K05", "N03", "N07", "N08", "N15", "N20", "N26", "N28"]
FALSE_REFUSALS = ["MX12", "MX18", "P05", "P08", "MX15", "P17", "P18", "P06"]


def final_turns(rows: dict) -> dict[str, str]:
    last: dict[str, str] = {}
    for key in rows:
        session, turn = key.split("/")
        if session not in last or turn > last[session].split("/")[1]:
            last[session] = key
    return last


def verdicts(task: str, gold: list[dict], row: dict) -> list[dict]:
    results = row["final"]["rows"]
    out = []
    for requirement in gold:
        matched = [r for r in results if quote_match(task, requirement["words"], r["quote"])]
        out.append({"words": requirement["words"], "expect": requirement["expect"],
                    "rows": [[r["quote"], r["status"], r["workflows"], r["limits"][:1]] for r in matched]})
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument("--out")
    args = parser.parse_args()
    runs = [json.loads(Path(name).read_text()) for name in args.files]
    names = ["base", "new", "injected"][:len(runs)]
    items = {item["id"]: item for item in json.loads((M3 / "heldout.json").read_text())["items"]}
    key = json.loads((M3 / "live/m3/blind-key.json").read_text())
    checked = json.loads((M3 / "live/m3/labels-checked.json").read_text())
    blind = json.loads((M3 / "live/m3/labels-A.json").read_text())
    labels = {entry["session"]: (checked.get(code) or blind.get(code) or {}).get("R") for code, entry in key.items()}
    changes, refused = {}, []
    for session, turn in sorted(final_turns(runs[0]).items()):
        item = items[session.removeprefix("ve-m3-live-").rsplit("-", 1)[0]]
        found = {}
        for name, rows in zip(names, runs):
            row = rows[turn]
            task = "\n".join(item.get("turns") or [item["prompt"]])
            found[name] = {"requirements": verdicts(task, item["requirements"], row),
                           "full_gap": row["final"]["full_gap"], "unchecked": row["final"]["unchecked"],
                           "run": (row["run"] or {}).get("verdict"), "needs_live": row["needs_live"],
                           "paragraph": row["final"]["paragraph"]}
        base = found["base"]
        moved = {name: value for name, value in found.items() if name != "base" and (
            value["requirements"] != base["requirements"] or value["full_gap"] != base["full_gap"]
            or value["run"] != base["run"] or value["unchecked"] != base["unchecked"])}
        if moved:
            changes[session] = {"item": item["id"], "label": labels.get(session), "base": base, **moved}
        for name, value in moved.items():
            for before, after in zip(base["requirements"], value["requirements"]):
                lost = (any(r[1] == "available" for r in before["rows"])
                        and not any(r[1] == "available" for r in after["rows"]))
                if after["expect"] == "supported" and (lost or (base["run"] in APPROVING
                                                                 and value["run"] not in APPROVING)):
                    refused.append((name, session, after["words"]))
    print(f"{len(changes)} sessions change; new refusals of a supported requirement: {refused or 'none'}")
    for session, change in changes.items():
        print(f"\n{session} ({change['item']}) label {change['label']}")
        for name in names:
            if name in change:
                value = change[name]
                print(f"  {name:8} run={value['run']} gap={value['full_gap']} live={len(value['needs_live'])}")
                for requirement in value["requirements"]:
                    print(f"           [{requirement['expect']}] {requirement['words']!r}: "
                          f"{[(r[0][:60], r[1]) for r in requirement['rows']] or 'no row'}")
    for group, ids in (("false accepts", FALSE_ACCEPTS), ("false refusals", FALSE_REFUSALS)):
        print(f"\n{group}:")
        for item_id in ids:
            session = f"ve-m3-live-{item_id}-1"
            change = changes.get(session)
            print(f"  {item_id}: " + ("unchanged" if change is None else
                                     ", ".join(name for name in names if name in change)))
    if args.out:
        Path(args.out).write_text(json.dumps({"changes": changes, "new_refusals": refused}, indent=1,
                                             ensure_ascii=False))


if __name__ == "__main__":
    main()
