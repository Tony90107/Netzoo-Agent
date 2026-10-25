"""Misread detection (ROUND.md): recall, false alarms, the simulated first-turn call and the gates, from
`signals.py` (replay) and `signals_h7.py` (h7) outputs. No model calls.

A flag acts only when the call is DO or DECLINE (ROUND.md's shared condition). Flagged, the call becomes CLARIFY for the
goal signals (X1-X3) and ASK for the others; a union with both asks the goal first, as `decide_core` puts CLARIFY
before ASK. The simulated call is scored with `score.kind_of` against the relabelled gold.

Usage: python3 measure.py signals-replay.json signals-h7.json > measure.txt   (also writes measure.json)
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "harness-repair-2026-10-23"))
from score import kind_of  # noqa: E402

sys.path.insert(0, str(HERE))
from signals import ACTING, GOAL_SIGNALS, SIGNALS  # noqa: E402

X = tuple(s for s in SIGNALS if s.startswith("X"))
Q = tuple(s for s in SIGNALS if s.startswith("Q"))
UNIONS = {"ANY_X": X, "ANY_Q": Q, "ANY": SIGNALS}
SUBTYPES = ("R-goal", "R-unc", "R-cond", "R-link", "R-type")
ERRORS = ("FA", "FR", "MA", "wrong question kind", "extra questions", "UNCHECKED")
MEASURES = ("right", "FA", "FR", "MA", "wrong question kind", "extra questions", "UNCHECKED")


def fires(row: dict, members) -> list[str]:
    return [s for s in members if s in (row.get("signals") or {})]


def acts(row: dict, members) -> bool:
    return row.get("call") in ACTING and bool(fires(row, members))


def flagged_kind(row: dict, members) -> str:
    return "CLARIFY" if any(s in GOAL_SIGNALS for s in fires(row, members)) else "ASK"


def target(row: dict) -> bool:
    """A reading-level error that is not R-fail: the recall denominator."""
    return row["error"] != "right" and row.get("layer") == "reading" and row.get("subtype") != "R-fail"


def item_of(row: dict) -> str:
    return f"{row.get('set')}:{row.get('item')}"


def replay_table(rows: list[dict], members) -> dict:
    errors = [r for r in rows if r["error"] != "right"]
    right = [r for r in rows if r["error"] == "right"]
    targets = [r for r in errors if target(r)]
    hit = [r for r in targets if acts(r, members)]
    false = [r for r in right if acts(r, members)]
    flagged_errors = [r for r in errors if acts(r, members)]
    out = {
        "target_hits": len(hit), "targets": len(targets),
        "target_items_hit": len({item_of(r) for r in hit}),
        "target_items": len({item_of(r) for r in targets}),
        "by_subtype": {s: f"{sum(r['subtype'] == s for r in hit)}/{sum(r['subtype'] == s for r in targets)}"
                       for s in SUBTYPES},
        "by_error": {e: f"{sum(r['error'] == e for r in hit)}/{sum(r['error'] == e for r in targets)}"
                     for e in ERRORS if any(r["error"] == e for r in targets)},
        "decision_layer_hits": sum(acts(r, members) for r in errors if r.get("layer") == "decision"),
        "r_fail_hits": sum(acts(r, members) for r in errors if r.get("subtype") == "R-fail"),
        "false_alarms": len(false), "right": len(right),
        "false_by_gold": dict(Counter(r["gold"] for r in false)),
        "right_items_flagged": len({item_of(r) for r in false}),
        "flagged_errors": len(flagged_errors),
        "precision": (len(flagged_errors) / (len(flagged_errors) + len(false))) if flagged_errors or false else None,
        "co_fire_on_asking_calls": sum(bool(fires(r, members)) and r["call"] not in ACTING for r in rows),
    }
    before = Counter(kind_of(r["gold"], r["call"]) for r in rows)
    after = Counter(kind_of(r["gold"], flagged_kind(r, members) if acts(r, members) else r["call"]) for r in rows)
    out["simulated"] = {m: [before[m], after[m]] for m in MEASURES}
    out["new_errors"] = [f"{r['session']}/{r['turn']} gold {r['gold']}: {r['call']} -> {flagged_kind(r, members)}"
                         for r in rows if acts(r, members) and r["error"] == "right"
                         and kind_of(r["gold"], flagged_kind(r, members)) in ("FA", "FR", "MA", "wrong question kind")]
    s = out["simulated"]
    out["gates"] = {
        "G1": len(hit) >= 10 and out["target_items_hit"] >= 5,
        "G2": len(flagged_errors) >= len(false) and bool(flagged_errors),
        "G3": all(s[m][1] <= s[m][0] for m in ("FA", "FR", "MA"))
              and s["wrong question kind"][1] - s["wrong question kind"][0] <= s["MA"][0] - s["MA"][1],
    }
    return out


def h7_table(rows: list[dict], members) -> dict:
    single = [r for r in rows if r["part"] == "single" and r.get("call") not in ("no_reading", "no_task", "error")]
    errors = [r for r in single if r.get("layer")]
    right = [r for r in single if r.get("outcome") == "correct"]
    hit_targets = [r for r in errors if r["layer"] == "reading" and r["subtype"] != "R-fail" and acts(r, members)]
    flagged_errors = [r for r in errors if acts(r, members)]
    false = [r for r in right if acts(r, members)]
    precision = len(flagged_errors) / (len(flagged_errors) + len(false)) if flagged_errors or false else None
    multi = [r for r in rows if r["part"] == "multi" and acts(r, members)]
    return {"errors": len(errors), "right": len(right), "target_hits": len(hit_targets),
            "flagged_errors": len(flagged_errors), "false_alarms": len(false), "precision": precision,
            "by_subtype": dict(Counter(r["subtype"] for r in hit_targets)),
            "hit_ids": sorted(r["id"] for r in flagged_errors), "false_ids": sorted(r["id"] for r in false),
            "multi_t1_flagged": sorted(r["id"] for r in multi),
            "G4": precision is not None and precision >= 0.3 and len(flagged_errors) >= 3}


def fmt(value) -> str:
    return f"{value:.0%}" if isinstance(value, float) else str(value)


def main(replay_path: str, h7_path: str):
    rows = [r for r in json.loads(Path(replay_path).read_text()) if r.get("gold") and r.get("error")]
    h7 = json.loads(Path(h7_path).read_text())
    report = {}
    names = [*SIGNALS, *UNIONS]
    for name in names:
        members = UNIONS.get(name, (name,))
        report[name] = {"replay": replay_table(rows, members), "h7": h7_table(h7, members)}
    passing = tuple(name for name in SIGNALS
                    if all(report[name]["replay"]["gates"].values()) and report[name]["h7"]["G4"])
    if passing:
        report["PASS"] = {"members": passing, "replay": replay_table(rows, passing), "h7": h7_table(h7, passing)}

    targets = [r for r in rows if target(r)]
    print(f"replay: {len(rows)} labelled readings, {sum(r['error'] == 'right' for r in rows)} right, "
          f"{len(targets)} reading-level non-R-fail errors on {len({item_of(r) for r in targets})} items "
          f"{dict(Counter(r['subtype'] for r in targets))}; R-fail {sum(r.get('subtype') == 'R-fail' for r in rows)}, "
          f"decision layer {sum(r.get('layer') == 'decision' for r in rows)}")
    print(f"targets whose call is DO or DECLINE (a flag can act): {sum(r['call'] in ACTING for r in targets)}; "
          f"by error {dict(Counter(r['error'] for r in targets if r['call'] in ACTING))}")
    print()
    print("signal | target hits (items) | R-goal R-unc R-cond R-link R-type | dec R-fail | false alarms /right "
          "(items) | precision | co-fire | G1 G2 G3 | h7 hits/err false/right prec G4")
    for name in [*names, *(["PASS"] if passing else [])]:
        t, h = report[name]["replay"], report[name]["h7"]
        g = t["gates"]
        print(f"{name:6} | {t['target_hits']:3}/{t['targets']} ({t['target_items_hit']}/{t['target_items']}) | "
              f"{' '.join(t['by_subtype'][s] for s in SUBTYPES)} | {t['decision_layer_hits']} {t['r_fail_hits']} | "
              f"{t['false_alarms']:3}/{t['right']} ({t['right_items_flagged']}) | {fmt(t['precision'])} | "
              f"{t['co_fire_on_asking_calls']} | {'Y' if g['G1'] else '-'} {'Y' if g['G2'] else '-'} "
              f"{'Y' if g['G3'] else '-'} | {h['flagged_errors']}/{h['errors']} {h['false_alarms']}/{h['right']} "
              f"{fmt(h['precision'])} {'Y' if h['G4'] else '-'}")
    print()
    print("simulated first-turn score (before -> after), replay labelled readings:")
    for name in [*names, *(["PASS"] if passing else [])]:
        s = report[name]["replay"]["simulated"]
        print(f"{name:6} " + "  ".join(f"{m} {s[m][0]}->{s[m][1]}" for m in MEASURES))
    print()
    print("false alarms by gold:")
    for name in names:
        print(f"{name:6} {report[name]['replay']['false_by_gold']}  new errors: {len(report[name]['replay']['new_errors'])}")
    print()
    print(f"passing every gate: {list(passing) or 'none'}")

    # examples: three hits and three false alarms per signal (seed 1025)
    pick = random.Random(1025)
    examples = {}
    for name in SIGNALS:
        hits = [r for r in rows if target(r) and acts(r, (name,))]
        false = [r for r in rows if r["error"] == "right" and acts(r, (name,))]
        examples[name] = {
            "hits": [{k: r[k] for k in ("session", "turn", "gold", "call", "basis", "error", "subtype", "request")}
                     | {"detail": r["signals"][name]} for r in pick.sample(hits, min(3, len(hits)))],
            "false_alarms": [{k: r[k] for k in ("session", "turn", "gold", "call", "basis", "request")}
                             | {"detail": r["signals"][name]} for r in pick.sample(false, min(3, len(false)))]}
    report["examples"] = examples
    (HERE / "measure.json").write_text(json.dumps(report, indent=1, ensure_ascii=False, default=list))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
