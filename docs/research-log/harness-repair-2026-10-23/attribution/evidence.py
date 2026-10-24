"""Harness repair P5 error attribution (ATTRIBUTION.md), no model calls: the evidence for every labelled B2 reading the
current code gets wrong -- the request, the item's gold, the call, and what the recorded reading said -- so each error
can be put in the reading, decision or reply layer.

The reading summary is the model's own output as this code's check typed it: each requirement's quote, status,
credited and near-miss entries, limits, violations and unknown words; the unknowns; the questions the call asks.

Usage: python3 evidence.py OUT.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parents[1]
sys.path.insert(0, str(LOGS / "stability-round13-2026-10-21"))
sys.path.insert(0, str(HERE.parent))


def items() -> dict:
    """(set, item id) -> gold details, from the core set and the h1-h4 audit."""
    found = {}
    core = json.loads((LOGS / "core-judgment-2026-10-15/items.json").read_text())["items"]
    for item in (core.values() if isinstance(core, dict) else core):
        found[("core", item["id"])] = {"class": item["class"], "workflows": item.get("workflows"),
                                       "reason": item.get("reason", ""), "evidence": item.get("evidence", ""),
                                       "deciding_fact": "", "missing_core": item.get("missing_core", "")}
    for item in json.loads((LOGS / "strictness-audit-2026-10-20/audit.json").read_text())["items"].values():
        found[("h", item["id"])] = {"class": item["class"], "workflows": item.get("gold_workflows"),
                                    "reason": item.get("gold_reason", ""), "evidence": item.get("evidence", ""),
                                    "deciding_fact": item.get("gold_fact", ""), "missing_core": ""}
    return found


def _names(keys) -> list[str]:
    from netzoo_agent_core.capability_sheet import entry

    out = []
    for key in keys or []:
        try:
            out.append(f"{key} ({entry(key).workflow})")
        except Exception:  # noqa: BLE001 -- an id the current sheet no longer has
            out.append(key)
    return out


def reading(decision, core) -> dict:
    check = decision.capability_check
    rows = []
    for row in (check.requirements if check else []):
        rows.append({k: v for k, v in {
            "kind": row.kind, "quote": row.quote, "status": row.status, "credited": _names(row.delivered_by),
            "near_miss": _names(row.not_by), "limits": row.limits, "violations": row.violations,
            "unknown_quote": row.unknown_quote, "depends_on": row.depends_on,
            "outcomes": {k: _names(v) for k, v in (row.outcomes or {}).items()},
            "method": {k: row.method.get(k) for k in ("named", "named_quote", "settings") if row.method.get(k)}}.items()
            if v not in (None, "", [], {})})
    return {
        "action": decision.action, "matched_actions": list(decision.matched_actions or []),
        "capability_match_status": decision.capability_match_status,
        "requirements": rows,
        "unknowns": [list(item) for item in (check.unknowns if check else [])],
        "unchecked": list(check.unchecked) if check else [],
        "check_flags": {flag: getattr(check, flag) for flag in ("unavailable", "provisional", "gap_unconfirmed",
                                                                "full_gap") if check and getattr(check, flag)}
        if check else "no capability check",
        "core_basis": core.basis, "core_workflows": list(core.workflows or []),
        "questions_asked": [{"question": f.question, "about": f.depends_on or ("count" if f.by_code else "agent"),
                             "user_quote": f.user_quote} for f in core.facts],
        "clarify_question": (core.clarify.question if core.clarify else ""),
        "declined": [list(item) if isinstance(item, (list, tuple)) else item for item in (core.declined or [])],
    }


def main(out: str):
    import harness  # noqa: E402  (sets the import paths)
    import netzoo_agent_core.interpretation.core_decision as core_decision
    from score import kind_of

    relabels = json.loads((HERE.parent / "gold-p2.json").read_text())["relabels"]
    by_session, core_gold = harness._gold()
    known = items()
    original, seen, rows = core_decision.decide_core, {}, []

    def spy(decision, task="", **kwargs):
        seen["decision"], seen["core"] = decision, original(decision, task, **kwargs)
        return seen["core"]

    for key, folder, sid, task, payload, reread, found, _n in harness.readings():
        gold = harness._label(sid, by_session, core_gold)
        if (relabel := relabels.get(sid)) and folder.name == "t1":
            gold = relabel["to"]
        if not gold:
            continue
        core_decision.decide_core = spy
        try:
            harness.replay_full.replay(folder, task, payload, reread, found)
        except Exception:  # noqa: BLE001 -- the three old-schema readings harness.py reports
            continue
        finally:
            core_decision.decide_core = original
        call = seen["core"]
        error = kind_of(gold, call.kind)
        if error == "right":
            continue
        where = harness._item(sid)
        item = known.get(("core", where[1]) if where and where[0] == "core" else ("h", where[1]) if where else None)
        rows.append({"key": key, "session": sid, "turn": folder.name, "item": where[1] if where else None,
                     "set": where[0] if where else None, "gold": gold, "call": call.kind,
                     "partial": bool(call.partial), "error": error, "request": task[:2500],
                     "gold_detail": item, "reading": reading(seen["decision"], call)})
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False, default=str))
    from collections import Counter
    print(f"{len(rows)} wrong labelled readings; by error {dict(Counter(r['error'] for r in rows))}; "
          f"items {len({(r['set'], r['item']) for r in rows})}")


if __name__ == "__main__":
    main(sys.argv[1])
