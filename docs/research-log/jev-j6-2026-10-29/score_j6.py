"""j6 one-arm scoring (PLAN-J6.md): a baseline, no gates. No model calls.

Adapted from score_j4.py (same right/FA/FR/MA rules: PARTIAL counted as DO; final gold = `final_after_fact` when the
fact reply was sent, `final_after_result` when the result reply was sent, else the opening expected_call). Adds check
health per conversation. Cause classes for wrong finals are assigned by hand from the traces (RESULTS-J6.md).

Usage: python3 score_j6.py > RESULTS-J6.txt   (also writes score-j6.json)
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "harness-repair-2026-10-23"))
from score import kind_of  # noqa: E402

MEASURES = ("right", "FA", "FR", "MA", "wrong question kind", "extra questions", "UNCHECKED")
REASONS = {"group_membership": "none returns overlapping memberships",
           "time_model": "models how the system changes from one time point to the next",
           "spatial": "uses where samples sit in space or which samples are neighbours"}
FORMS = ("group_membership", "time_model", "spatial", "input_network")
CONTROLS = {"GO": "group_membership", "FD": "time_model", "FS": "spatial", "FG": None}
TRAPS = ("GT", "FT", "FSN", "FN")
GROUPS = ("GT", "GO", "FT", "FD", "FSN", "FS", "FN", "FG", "T", "TC", "MF", "SA", "SP", "U", "N", "V", "P")


def kind(call):
    return "DO" if call == "PARTIAL" else call


def events(turn: Path, name: str) -> list[dict]:
    return [json.loads(line)["payload"] for trace in sorted(turn.glob("trace-*.jsonl"))
            for line in trace.read_text().splitlines()
            if f'"{name}"' in line and json.loads(line).get("event_type") == name]


def form_asked(core: dict) -> bool:
    return any(f.get("depends_on") in FORMS for f in core.get("facts") or [])


def sessions(tag: str, items: dict) -> dict:
    rows = {}
    for folder in sorted((HERE / "live" / tag).glob(f"hb-{tag}-*-1")):
        item = items[folder.name.split("-")[2]]
        job = json.loads((folder / "job.json").read_text())
        turns = sorted(folder.glob("t*"), key=lambda p: int(p.name[1:]))
        cores = [(events(t, "core.decision") or [{}])[-1] for t in turns]
        if "fact" in job["sent"]:
            gold = kind(item["final_after_fact"]["call"])
        elif "result" in job["sent"]:
            gold = kind(item["final_after_result"]["call"])
        else:
            gold = kind(item["expected_call"])
        reply = (turns[-1] / "stdout.txt").read_text(errors="replace") if turns else ""
        rows[item["id"]] = {
            "id": item["id"], "group": item["category"], "gold": gold, "sent": job["sent"],
            "t1": f"{cores[0].get('kind')}/{cores[0].get('basis')}" if cores else "none",
            "final": cores[-1].get("kind") or "none", "final_basis": cores[-1].get("basis") or "",
            "reasons": [name for name, words in REASONS.items() if words in reply],
            "form_asked": any(form_asked(c) for c in cores),
            "waiting": (cores[-1].get("kind") in ("ASK", "CLARIFY")) if cores else False,
            "jev": {name: [e for t in turns for e in events(t, f"core.{name}")]
                    for name in ("jev_guard", "jev_condition", "jev_answer", "jev_link", "jev_overlap", "jev_forms")}}
    return rows


CHECK_ROLES = ("capability_check", "capability_reread", "capability_second_opinion", "capability_condition_check",
               "fact_check")


def health(folder: Path) -> dict:
    found = {"enum_400": 0, "check_blocked": [], "provisional": 0}
    for turn in sorted(folder.glob("t*")):
        found["enum_400"] += sum("enum values" in e.get("error_message", "")
                                 for e in events(turn, "routing.capability_check_failed"))
        found["check_blocked"] += [e["role"] for e in events(turn, "budget.blocked") if e.get("role") in CHECK_ROLES]
        found["provisional"] += len(events(turn, "routing.capability_check_provisional"))
    return found


def main():
    items = {i["id"]: i for i in json.loads((HERE / "j6" / "items.json").read_text())["single"]}
    A = sessions("j6a", items)
    keys = sorted(A)
    s = Counter(kind_of(A[k]["gold"], A[k]["final"]) for k in keys)
    by = lambda g: [A[k] for k in keys if A[k]["group"] == g]  # noqa: E731
    wrong_reasons = [r["id"] for r in A.values() if r["final"] == "DECLINE"
                     and any(reason != CONTROLS.get(r["group"]) for reason in r["reasons"])]
    checks = {k: health(HERE / "live" / "j6a" / f"hb-j6a-{k}-1") for k in keys}
    print(f"j6: {len(keys)} of {len(items)} conversations")
    print(f"  final right {s['right']}/{len(keys)}  " + "  ".join(f"{m} {s[m]}" for m in MEASURES[1:]))
    print("  by group " + str({g: f"{sum(kind_of(r['gold'], r['final']) == 'right' for r in by(g))}/{len(by(g))}"
                               for g in GROUPS}))
    print(f"  check health: enum 400s {sum(c['enum_400'] for c in checks.values())}, check-family refusals "
          f"{[(k, c['check_blocked']) for k, c in checks.items() if c['check_blocked']] or 'none'}, provisional "
          f"{sum(c['provisional'] for c in checks.values())}")
    print(f"  form reasons said on a DECLINE the item did not ask for: {wrong_reasons or 'none'}")
    print("\nid | group | gold | t1 -> final/basis [reasons] | sent | verdict")
    for k in sorted(keys, key=lambda k: (GROUPS.index(A[k]["group"]), k)):
        r = A[k]
        print(f"  {k} | {r['group']} | {r['gold']} | {r['t1']} -> {r['final']}/{r['final_basis']} {r['reasons'] or ''}"
              f" | {','.join(r['sent'])} | {kind_of(r['gold'], r['final'])}")
    (HERE / "score-j6.json").write_text(json.dumps({"summary": s, "rows": {k: {x: A[k][x] for x in (
        "group", "gold", "t1", "final", "final_basis", "sent", "reasons")} | {"verdict": kind_of(A[k]["gold"], A[k]["final"]),
        "health": checks[k]} for k in keys}, "wrong_reasons": wrong_reasons}, indent=1) + "\n")


if __name__ == "__main__":
    main()
