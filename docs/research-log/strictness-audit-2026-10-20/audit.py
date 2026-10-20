"""Round 01 strictness audit (collab/ROUND-01-PLAN.md): the live system's calls on the four fresh blind sets h1-h4.

Offline and read-only: no model is called. For each of the 192 items it reads the gold, the scored outcome of the live
arm and the session's own trace (core.decision, routing.capability_checked, core.fact_check, run verdict, budget and
failure events), and merges the hand classification in `labels.json` (cause, field state, relax / tighten effect).
Reruns with identical live code (h2 `h2hyb` outside the three items its gates changed; h4 smoke sessions, whose
core.decision is recorded before the veto) mark an error `flaky` when the same item came out right there.

    python3 -I audit.py            # writes audit.json and prints the summary tables
    python3 -I audit.py --dump ID  # one item's extracted trace (for classifying)
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = HERE.parent

SETS = {
    "h1": ("closed-menu-phase1b-2026-10-18/heldout/items.json",
           "closed-menu-phase1b-2026-10-18/heldout/live/h1/compare.json", "live",
           "closed-menu-phase1b-2026-10-18/heldout/live/h1", "hb-h1"),
    "h2": ("closed-menu-options-first-2026-10-18/h2/items.json",
           "closed-menu-options-first-2026-10-18/h2/live/h2/compare.json", "main",
           "closed-menu-options-first-2026-10-18/h2/live/h2main", "hb-h2main"),
    "h3": ("closed-menu-slim-2026-10-19/h3/items.json",
           "closed-menu-slim-2026-10-19/h3/live/h3/compare.json", "main",
           "closed-menu-slim-2026-10-19/h3/live/h3main", "hb-h3main"),
    "h4": ("closed-menu-hybrid-2026-10-19/h4/items.json",
           "closed-menu-hybrid-2026-10-19/h4/live/h4/compare.json", "main",
           "closed-menu-hybrid-2026-10-19/h4/live/h4main", "hb-h4main"),
}
# Identical live code run again (RESULTS-8-h2.md: the hybrid gates changed only J15, J28, J40; J11 and J19 were
# blocked by budget before the gate). h4 smoke sessions ran the live pipeline with the veto on; their core.decision
# is the live call before the veto.
RERUNS = {
    "h2": [("h2hyb", "closed-menu-options-first-2026-10-18/h2/live/h2/compare.json", "hybrid",
            {"J15", "J28", "J40"})],
}
SMOKE = ["closed-menu-hybrid-2026-10-19/h4/live/h4smoke", "closed-menu-hybrid-2026-10-19/h4/live/h4smoke2"]
WRONG_KIND_OK = {"correct"}
FAILURE_EVENTS = ("failed", "blocked", "budget.warning", "provisional", "unverified")


def _events(folder: Path) -> list[dict]:
    path = folder / "t1" / "events.jsonl"
    return [json.loads(line) for line in path.open()] if path.exists() else []


def _last(events: list[dict], kind: str) -> dict | None:
    found = [e["payload"] for e in events if e["event_type"] == kind]
    return found[-1] if found else None


def _workflow(key: str) -> str:
    return key.split(".")[0].replace("_", "-").upper()


def _row(row: dict) -> dict:
    method = row.get("method") or {}
    return {
        "kind": row["kind"], "status": row["status"], "quote": row["quote"][:160],
        "credited": sorted({_workflow(k) for k in row.get("delivered_by", [])}),
        "blank": row.get("blank", False), "second_opinion": row.get("second_opinion", False),
        "limits": row.get("limits", []), "violations": row.get("violations", []),
        "not_by": row.get("not_by", []), "instead": sorted({_workflow(k) for k in row.get("instead", [])}),
        "defaults": sorted({_workflow(k) for k in row.get("defaults", [])}),
        "depends_on": row.get("depends_on"), "unknown_quote": row.get("unknown_quote", ""),
        "by_code": row.get("by_code", False),
        "method": {k: method[k] for k in ("named", "named_quote", "samples", "features", "settings") if k in method},
        "attrs": {k: v for k, v in (row.get("attrs") or {}).items()
                  if v not in ("not_stated", [], None, False, "none", 0, "not_spatial", "not_dynamic")},
    }


def extract(folder: Path) -> dict:
    events = _events(folder)
    decision = _last(events, "core.decision") or {}
    check = (_last(events, "routing.capability_checked") or {}).get("check") or {}
    facts = _last(events, "core.fact_check") or {}
    view = _last(events, "core.view") or {}
    stdout = folder / "t1" / "stdout.txt"
    reply = [line for line in (stdout.read_text().splitlines() if stdout.exists() else [])
             if line.strip() and not line.lstrip().startswith(("●", "✓"))]
    return {
        "session": folder.name,
        "decision": {k: decision.get(k) for k in ("kind", "basis", "partial", "workflows", "run_allowed")},
        "declined": [{"quote": d.get("quote", "")[:160], "reasons": d.get("reasons", []), "line": d.get("line", "")[:300]}
                     for d in decision.get("declined", [])],
        "asked": [{"question": f.get("question", ""), "user_quote": f.get("user_quote", "")[:160],
                   "depends_on": f.get("depends_on", ""), "by_code": f.get("by_code", False)}
                  for f in decision.get("facts", [])],
        "clarify": (decision.get("clarify") or {}).get("question"),
        "run_verdict": (decision.get("evidence") or {}).get("run_verdict"),
        "reason_code": (decision.get("evidence") or {}).get("reason_code"),
        # The check the decision read (a run can drop or replace the last capability_checked event's check).
        "decided_on": {k: (decision.get("evidence") or {}).get(k) for k in ("goal", "rows", "check_unconfirmed")},
        "budget_blocked": sorted({e["payload"].get("role", "") for e in events if e["event_type"] == "budget.blocked"}),
        "check": {
            "goal": check.get("goal"), "goal_quote": check.get("goal_quote"), "full_gap": check.get("full_gap"),
            "provisional": check.get("provisional"), "gap_unconfirmed": check.get("gap_unconfirmed"),
            "unavailable": check.get("unavailable"), "unchecked": check.get("unchecked", []),
            "ruled_out": check.get("ruled_out", {}), "only_inputs": check.get("only_inputs", []),
            "uncertain_quotes": check.get("uncertain_quotes", []), "conditions": check.get("conditions", {}),
            "rows": [_row(r) for r in check.get("requirements", []) if r["kind"] != "context"],
        },
        "fact_check": {
            "status": facts.get("status"),
            "accepted": [f.get("question") for f in facts.get("accepted", [])],
            "rejected": [{"q": r["proposal"].get("question"), "quote": r["proposal"].get("user_quote", "")[:120],
                          "rule": r.get("rule")} for r in facts.get("rejected", [])],
            "open_results": facts.get("open_results", []),
        },
        "view": {k: view.get(k) for k in ("core_kind", "reply_kind", "mismatch")},
        "failures": sorted({e["event_type"] for e in events if any(s in e["event_type"] for s in FAILURE_EVENTS)}),
        "reply": reply[:14],
    }


_OK = {("vague", "CLARIFY"): ("OK_goal_unclear", "F2"), ("ask", "ASK"): ("OK_F3", "F3"),
       ("dont", "DECLINE"): ("OK_F4", "F4")}


def default_label(record: dict) -> dict:
    """A correct non-DO call is justified by its gold class (vague: no result named; ask: the user is unsure or says two
    things; dont: a stated request breaks the contract). Its declined rows were checked for contract evidence in code;
    the declines resting on no reason are overridden by hand in labels.json."""
    if record["outcome"] != "correct" or record["kind"] == "DO":
        return {}
    cause, state = _OK.get((record["class"], record["kind"]), ("X_other", "none"))
    same = {"effect": "no_change", "why": "the call already asks / declines on the field the gold names"}
    return {"cause": cause, "field_state": state, "confidence": "high", "relax_effect": same,
            "tighten_effect": same, "evidence": f'{record["trace"]["session"]} core.decision basis='
                                                f'{record["trace"]["decision"]["basis"]}'}


def load() -> dict:
    labels = json.loads((HERE / "labels.json").read_text()) if (HERE / "labels.json").exists() else {}
    items = {}
    for name, (items_path, compare_path, arm, sessions, prefix) in SETS.items():
        gold = {item["id"]: item for item in json.loads((LOG / items_path).read_text())["items"]}
        scored = json.loads((LOG / compare_path).read_text())[arm]["items"]
        reruns = {}
        for rerun, path, rerun_arm, changed in RERUNS.get(name, []):
            other = json.loads((LOG / path).read_text())[rerun_arm]["items"]
            reruns[rerun] = {k: v["outcome"] for k, v in other.items() if k not in changed}
        for item_id in sorted(gold):
            g, s = gold[item_id], scored[item_id]
            record = {
                "id": item_id, "set": name, "class": g["class"], "form": g.get("form"),
                "gold_workflows": g.get("workflows", []), "gold_reason": g.get("reason", ""),
                "gold_fact": g.get("deciding_fact") or g.get("missing_core") or "",
                "prompt": g["prompt"], "kind": s["kind"], "outcome": s["outcome"],
                "trace": extract(LOG / sessions / f"{prefix}-{item_id}-1"),
                "reruns": {r: o[item_id] for r, o in reruns.items() if item_id in o},
            }
            for smoke in SMOKE:
                folder = LOG / smoke / f"hb-{Path(smoke).name}-{item_id}-1"
                if folder.exists():
                    events = _events(folder)
                    d = _last(events, "core.decision") or {}
                    veto = _last(events, "core.contract_veto")  # the live call is the one before the veto
                    record["reruns"][Path(smoke).name] = {
                        "kind": veto["kind_before"] if veto else d.get("kind"), "basis": d.get("basis"),
                        "before_veto": bool(veto)}
            record.update(default_label(record))
            record.update(labels.get(item_id, {}))
            items[item_id] = record
    return items


def flaky(record: dict) -> bool | None:
    """An error is reading noise when an identical-code rerun got the same item right."""
    if record["outcome"] == "correct" or not record["reruns"]:
        return None
    for name, value in record["reruns"].items():
        if value == "correct":
            return True
        if isinstance(value, dict) and value.get("kind") == {"do": "DO", "dont": "DECLINE"}.get(record["class"]):
            return True
    return False


def needs_label(record: dict) -> bool:
    return record["outcome"] != "correct" or record["kind"] != "DO"


def summary(items: dict) -> dict:
    wrong = [r for r in items.values() if r["outcome"] != "correct"]
    ok_nondo = [r for r in items.values() if r["outcome"] == "correct" and r["kind"] != "DO"]
    by_cause = Counter(r.get("cause", "UNLABELLED") for r in wrong)
    strict = {c: sorted(r["id"] for r in wrong if r.get("cause", "").startswith(c))
              for c in ("S1", "S2", "S3", "S4", "S5")}
    states = Counter(r.get("field_state", "?") for r in ok_nondo)
    net = {}
    for policy in ("relax_effect", "tighten_effect"):
        table = {}
        for cls in ("do", "dont", "ask", "vague"):
            fixes = sorted(r["id"] for r in wrong if r["class"] == cls and r.get(policy, {}).get("effect") == "fixes")
            breaks = sorted(r["id"] for r in items.values()
                            if r["class"] == cls and r.get(policy, {}).get("effect") == "breaks")
            table[cls] = {"fixes": fixes, "breaks": breaks, "net": len(fixes) - len(breaks)}
        table["total"] = {k: sum(len(v[k]) if k != "net" else v[k] for v in table.values())
                          for k in ("fixes", "breaks", "net")}
        net[policy] = table
    return {
        "items": len(items), "right": len(items) - len(wrong), "wrong": len(wrong),
        "wrong_by_outcome": dict(Counter(r["outcome"] for r in wrong)),
        "wrong_by_cause": dict(sorted(by_cause.items())),
        "too_strict_by_code": strict,
        "correct_non_do": len(ok_nondo), "correct_non_do_by_state": dict(sorted(states.items())),
        "flaky": sorted(r["id"] for r in wrong if r.get("flaky")),
        "budget_blocked": {"sessions": sorted(r["id"] for r in items.values() if r["trace"]["budget_blocked"]),
                           "wrong": sorted(r["id"] for r in wrong if r["trace"]["budget_blocked"])},
        "net_effect": net,
        # Policy T read broadly (every typed condition must be explicit, the data unit among them): the correct DO
        # calls on expression data whose words never say bulk -- a rough estimate of the needless questions T adds.
        # Read narrowly (only counts and settings a contract limit uses), no correct DO lacks one (AUDIT.md, Q3).
        "tighten_broad_at_risk": sorted(
            r["id"] for r in items.values() if r["outcome"] == "correct" and r["kind"] == "DO"
            and r["class"] == "do" and "bulk" not in r["prompt"].casefold()
            and "CONDOR" not in r["trace"]["decision"]["workflows"]),
        "unlabelled": sorted(r["id"] for r in items.values() if needs_label(r) and "cause" not in r),
    }


def main() -> None:
    items = load()
    if len(sys.argv) > 2 and sys.argv[1] == "--dump":
        for item_id in sys.argv[2:]:
            print(json.dumps(items[item_id], indent=1, ensure_ascii=False))
        return
    for record in items.values():
        record["flaky"] = flaky(record)
    out = {"summary": summary(items), "items": items}
    (HERE / "audit.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(out["summary"], indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
