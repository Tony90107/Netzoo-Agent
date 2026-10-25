"""P2 (ROUND-H9.md): X2, Q2 and M on the h9 round, offline, and the declared gates. No model calls; no decision changed.

Each h9 session's first turn is read from its recorded trace as `signals_h7.py` reads h7: the live call is the
recorded `core.decision`; the frozen code's replay of the same trace is recorded beside it, and the declared signals
come from `signals.compute` on that replay. M is the session's item's closed-menu read (`menu-h9.json`, its final
call after the focused re-read).

Usage: python3 score_h9.py > score-h9.txt   (also writes score-h9.json)
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import signals  # noqa: E402  (sets the paths)
from signals import ACTING, SIGNALS  # noqa: E402

sys.path.insert(0, str(signals.REPAIR))
from score import kind_of  # noqa: E402

ASKING = ("ASK", "CLARIFY")
MEASURES = ("right", "FA", "FR", "MA", "wrong question kind", "extra questions", "UNCHECKED")
GATED = {"X2": ("X2",), "Q2": ("Q2",), "M": ("M",), "X2|Q2": ("X2", "Q2"), "X2|Q2|M": ("X2", "Q2", "M")}


def as_kind(call: str) -> str:
    return "DO" if call == "PARTIAL" else call


def sessions() -> list[dict]:
    sys.path.insert(0, str(signals.LOGS / "false-accept-replay-2026-10-21"))
    import replay_full  # noqa: E402
    from replay import _fits
    import netzoo_agent_core.interpretation.core_decision as core_decision

    items = {i["id"]: i for i in json.loads((HERE / "h9" / "items.json").read_text())["single"]}
    menu = {r["id"]: r for r in json.loads((HERE / "menu-h9.json").read_text())["rows"]} \
        if (HERE / "menu-h9.json").exists() else {}
    original, seen, rows = core_decision.decide_core, {}, []

    def spy(decision, task="", **kwargs):
        seen["decision"], seen["core"] = decision, original(decision, task, **kwargs)
        return seen["core"]

    for turn in sorted((HERE / "live" / "h9").glob("hb-h9-*-1/t1")):
        key = turn.parent.name.split("-")[2]
        item = items[key]
        session = json.loads((turn / "session.json").read_text()) if (turn / "session.json").exists() else {}
        found = [json.loads(line) for trace in sorted(turn.glob("trace-*.jsonl"))
                 for line in trace.read_text().splitlines() if line.strip()]
        live = next((e["payload"] for e in reversed(found) if e.get("event_type") == "core.decision"), {})
        read = menu.get(key) or {}
        row = {"id": key, "group": item["category"], "sub": item["sub"], "expected": as_kind(item["expected_call"]),
               "acceptable": sorted({as_kind(item["expected_call"]), *map(as_kind, item.get("also_acceptable") or [])}),
               "call": live.get("kind") or "no_call", "basis": live.get("basis"), "partial": bool(live.get("partial")),
               "menu_kind": (read.get("final") or {}).get("kind"), "menu_basis": (read.get("final") or {}).get("basis"),
               "menu_status": read.get("status"), "signals": {}}
        checks = [i for i, e in enumerate(found)
                  if e.get("event_type") == "routing.capability_checked" and e["payload"].get("proposal")]
        users = [m["content"] for m in session.get("messages", []) if m["role"] == "user"]
        payload = found[checks[0]]["payload"]["proposal"] if checks else None
        task = next((t for t in reversed(users) if _fits(t, payload)), None) if payload else None
        if payload is not None and task is not None:
            reread = next((e["payload"] for e in found[checks[0] + 1:]
                           if e.get("event_type") == "routing.capability_reread"), None)
            seen.clear()
            core_decision.decide_core = spy
            try:
                replay_full.replay(turn, task, payload, reread, found)
                row["replay_call"] = seen["core"].kind
                row["signals"] = signals.compute(seen["decision"], seen["core"], found, task, payload, reread)
            except Exception as error:  # noqa: BLE001 -- reported, never hidden
                row["replay_call"] = f"error: {type(error).__name__}: {error}"[:200]
            finally:
                core_decision.decide_core = original
        else:
            row["replay_call"] = "no_reading"
        if row["menu_kind"] in ASKING:
            row["signals"]["M"] = f"menu {row['menu_kind']}/{row['menu_basis']}"
        row["right"] = row["call"] in row["acceptable"]
        row["error"] = "right" if row["right"] else kind_of(row["expected"], row["call"])
        rows.append(row)
    return rows


def flagged_kind(row: dict, members) -> str | None:
    """The call a flag leaves: X2 asks the goal, then M's own kind, then Q2 asks a fact (ROUND-H9.md)."""
    if row["call"] not in ACTING:
        return None
    fired = [s for s in members if s in row["signals"]]
    if "X2" in fired:
        return "CLARIFY"
    if "M" in fired:
        return row["menu_kind"]
    return "ASK" if fired else None


def table(rows: list[dict], members) -> dict:
    acting_errors = [r for r in rows if r["call"] in ACTING and not r["right"]]
    flagged = [r for r in rows if flagged_kind(r, members)]
    hits = [r for r in flagged if not r["right"]]
    false = [r for r in flagged if r["right"]]
    before = Counter(r["error"] for r in rows)
    after = Counter("right" if (flagged_kind(r, members) or r["call"]) in r["acceptable"]
                    else kind_of(r["expected"], flagged_kind(r, members) or r["call"]) for r in rows)
    simulated = {m: [before[m], after[m]] for m in MEASURES}
    k_false = [r for r in false if r["group"] in ("K1", "K2")]
    return {
        "acting_errors": len(acting_errors), "hits": [r["id"] for r in hits], "false_alarms": [r["id"] for r in false],
        "precision": len(hits) / len(flagged) if flagged else None, "simulated": simulated,
        "k_false_alarms": [r["id"] for r in k_false],
        "gates": {"G1": len(hits) >= 3, "G2": bool(hits) and len(hits) >= len(false),
                  "G3": all(simulated[m][1] <= simulated[m][0] for m in ("FA", "FR", "MA"))
                  and simulated["wrong question kind"][1] - simulated["wrong question kind"][0]
                  <= simulated["MA"][0] - simulated["MA"][1],
                  "G5": len(k_false) <= 2}}


def main():
    rows = sessions()
    report = {"sessions": rows, "signals": {}}
    print(f"h9: {len(rows)} sessions; right {sum(r['right'] for r in rows)}; errors {dict(Counter(r['error'] for r in rows if not r['right']))}")
    print(f"replayed call = live call on {sum(r.get('replay_call') == r['call'] for r in rows)}/{len(rows)}: "
          f"{[(r['id'], r['call'], r.get('replay_call')) for r in rows if r.get('replay_call') != r['call']]}")
    vu = [r for r in rows if r["group"] in ("V", "U") and r["call"] in ACTING and not r["right"]]
    print(f"acting errors in V and U: {len(vu)} {[r['id'] for r in vu]}"
          f"{'  -> fewer than 3: case insufficient (ROUND-H9)' if len(vu) < 3 else ''}")
    print("\nper group: right / sessions; calls")
    for group in ("V", "U", "K1", "K2"):
        part = [r for r in rows if r["group"] == group]
        print(f"  {group:2} {sum(r['right'] for r in part)}/{len(part)}  {dict(Counter(r['call'] for r in part))}")
    print("\nsession | group/sub | expected | live call/basis | right | signals fired | menu")
    for r in sorted(rows, key=lambda r: (r["group"], r["id"])):
        print(f"  {r['id']} | {r['group']}/{r['sub']} | {'/'.join(r['acceptable'])} | {r['call']}/{r['basis']}"
              f"{'(p)' if r['partial'] else ''} | {'Y' if r['right'] else r['error']} | "
              f"{sorted(r['signals'])} | {r['menu_kind']}/{r['menu_basis']}")
    print("\ngated signals: hits / false alarms | precision | G1 G2 G3 G5 | simulated (before -> after)")
    for name, members in GATED.items():
        t = table(rows, members)
        report["signals"][name] = t
        g = t["gates"]
        precision = f"{t['precision']:.0%}" if t["precision"] is not None else "-"
        print(f"  {name:8} {t['hits']} / {t['false_alarms']} | {precision} | "
              + " ".join("Y" if g[k] else "-" for k in ("G1", "G2", "G3", "G5")) + " | "
              + "  ".join(f"{m} {a}->{b}" for m, (a, b) in t["simulated"].items()))
    print("\nother signals (described, not gated): fired with an acting call -> on errors / on right sessions")
    for name in SIGNALS:
        if name in GATED:
            continue
        on = [r for r in rows if r["call"] in ACTING and name in r["signals"]]
        print(f"  {name:4} {[r['id'] for r in on if not r['right']]} / {[r['id'] for r in on if r['right']]}")
    (HERE / "score-h9.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
