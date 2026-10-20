"""ROUND-09 offline core replay (collab/ROUND-09-PLAN.md section 2): no model calls.

`cores CHECKS.json OUT.json [--scripts DIR]`: for each rebuilt check (request-facts-round03 `replay.py checks`), the
recorded session's decision with that check, its archived fact-agent answers and run verdict, through the given code's
`without_legacy_waits` and `decide_core` (as judgment-consistency-2026-10-20/replay.py does). `compare OLD NEW`: every
core that changed, beside the gold class where one exists (h1-h4 strictness audit; core-judgment items). The rebuilt
check has no second opinion or condition check, so changes are read as direction, not end-to-end accuracy.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parents[2]
MAIN = WT.parents[1] / "netzoo_agent"
KIND = {"do": "DO", "dont": "DECLINE", "ask": "ASK", "vague": "CLARIFY"}


def cores(checks_path: str, out: str):
    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck
    from netzoo_agent_core.graph.fact_check_call import without_legacy_waits
    from netzoo_agent_core.interpretation.core_decision import decide_core

    found = {}
    for key, row in json.loads(Path(checks_path).read_text()).items():
        folder = next((p for root in (WT, MAIN) if (p := root / row["where"]).joinpath("session.json").exists()), None)
        if folder is None:
            continue
        session = json.loads((folder / "session.json").read_text())
        try:
            decision = TaskDecision.model_validate(session["plan"]["decision"])
        except Exception:  # noqa: BLE001 -- a session without a plan decision
            continue
        events = [json.loads(line) for line in (folder / "events.jsonl").read_text().splitlines() if line.strip()]
        recorded = next((e["payload"] for e in reversed(events) if e.get("event_type") == "core.decision"), {})
        reason = recorded.get("evidence", {}).get("reason_code", "") or ""
        fields = set(CapabilityCheck.model_fields)
        check = CapabilityCheck.model_validate({k: v for k, v in row["check"].items() if k in fields})
        if decision.fact_check is not None and decision.fact_check.status == "checked":
            check = without_legacy_waits(check)
        core = decide_core(decision.model_copy(update={"capability_check": check}), row["task"], reason_code=reason)
        found[key] = {"where": row["where"], "session": session.get("session_id", ""), "kind": core.kind,
                      "basis": core.basis, "asked": [f.question for f in core.facts],
                      "count_owned": core.evidence.get("count_owned", [])}
    Path(out).write_text(json.dumps(found, indent=1))
    print(f"{len(found)} cores -> {out}")


def _gold():
    gold = {}
    audit = WT / "docs/research-log/strictness-audit-2026-10-20/audit.json"
    for item in json.loads(audit.read_text())["items"].values():
        gold[item["trace"]["session"]] = KIND[item["class"]]
    items = json.loads((WT / "docs/research-log/core-judgment-2026-10-15/items.json").read_text())["items"]
    items = {i["id"]: i for i in items} if isinstance(items, list) else items
    return gold, {k: KIND[v["class"]] for k, v in items.items()}


def compare(old_path: str, new_path: str):
    old, new = json.loads(Path(old_path).read_text()), json.loads(Path(new_path).read_text())
    gold, core_items = _gold()
    changed, right = [], {"before": 0, "after": 0, "labelled": 0}
    for key in sorted(new):
        a, b = old.get(key), new[key]
        if a is None:
            continue
        label = gold.get(b["session"])
        if label is None and (m := re.match(r"cj-[^-]+-(C\d+)-1", b["session"])):
            label = core_items.get(m.group(1))
        if label:
            right["labelled"] += 1
            right["before"] += a["kind"] == label
            right["after"] += b["kind"] == label
        if (a["kind"], a["asked"]) != (b["kind"], b["asked"]):
            changed.append((b["where"].split("research-log/")[-1], label, a["kind"], b["kind"], a["asked"],
                            b["asked"], b["count_owned"]))
    for row in changed:
        print(f"{row[0][:62]} gold={row[1]} {row[2]} -> {row[3]}")
        print(f"    asked before {row[4]}\n    asked after  {row[5]}\n    count_owned  {row[6]}")
    print(f"{len(changed)} of {len(new)} cores changed (kind or questions); right vs gold on {right['labelled']} "
          f"labelled: before {right['before']}, after {right['after']}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[0] == "cores":
        sys.path.insert(0, args[args.index("--scripts") + 1] if "--scripts" in args else str(WT / "scripts"))
        cores(args[1], args[2])
    else:
        compare(args[1], args[2])
