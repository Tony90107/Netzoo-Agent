"""Log 416: code-read metrics of a heldout416 round, per arm (no model is called).

Usage (repository root): python docs/research-log/open-choices-2026-10-12/analyze416.py <tag> <repeats>

Per session (`ve-<tag>-<arm>-<id>-<rep>` in the arm's worktree): the last reply and the recorded decision.
- offered: workflows the turn presents (matched, tied, recommended, advised, or a planned run);
- selected: the turn decided a workflow for the user -- a planned or run workflow, one exact match, a
  recommendation or an advice;
- refused: a full gap, or "No registered workflow produces" with nothing offered;
- named: every option of the item is named in the reply (any of its words, case-insensitive);
- asked: the reply asks something ("?");
- choice: the candidate's open-choice reply fired.
Target success (OC, ON, OR) = not refused, not selected, named and asked.
Writes live/<tag>-metrics.json and prints the frozen gates.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREES = HERE.parents[3] / ".worktrees"
ARMS = {"base": "netzoo-oc-base", "cand": "netzoo-oc-cand"}
ITEMS = {item["id"]: item for item in json.loads((HERE / "heldout416.json").read_text())["items"]}
CHOICE = "You have left this choice open"


def session(tag, arm, key, rep):
    path = WORKTREES / ARMS[arm] / ".netzoo" / "sessions" / f"ve-{tag}-{arm}-{key}-{rep}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    replies = [m["content"] for m in data["messages"] if m["role"] == "assistant"]
    plan = data.get("plan") or {}
    return (replies[-1] if replies else ""), plan, plan.get("decision") or {}


def read(item, found):
    if found is None:
        return {"missing": True}
    reply, plan, decision = found
    text = reply.casefold()
    advice = (decision.get("advisory_recommendation") or {}).get("action")
    planned = decision.get("action") not in (None, "no_tool")
    offered = list(dict.fromkeys([*decision.get("matched_actions", []), *decision.get("hypothesis_actions", []),
                                  *decision.get("recommended_actions", []), *([advice] if advice else []),
                                  *([decision["action"]] if planned else [])]))
    check = decision.get("capability_check") or {}
    selected = (planned or bool(decision.get("recommended_actions")) or bool(advice)
                or (len(decision.get("matched_actions", [])) == 1 and decision.get("capability_match_status") == "exact"))
    refused = bool(check.get("full_gap")) or ("no registered workflow produces" in text and not offered)
    named = all(any(word.casefold() in text for word in words) for words in item.get("options", []))
    asked = "?" in reply
    return {"offered": offered, "selected": selected, "refused": refused, "named": named, "asked": asked,
            "choice": CHOICE in reply, "plan_status": plan.get("status"), "workflow": plan.get("workflow"),
            "success": not refused and not selected and named and asked, "empty": not reply.strip()}


def main():
    tag, repeats = sys.argv[1], int(sys.argv[2])
    rows = []
    for key, item in ITEMS.items():
        for rep in range(1, repeats + 1):
            for arm in ARMS:
                rows.append({"id": key, "family": item["family"], "rep": rep, "arm": arm,
                             **read(item, session(tag, arm, key, rep))})
    (HERE / "live").mkdir(exist_ok=True)
    (HERE / "live" / f"{tag}-metrics.json").write_text(json.dumps(rows, indent=1))

    def count(arm, families, field):
        return sum(1 for r in rows if r["arm"] == arm and r["family"] in families and r.get(field))

    def total(arm, families):
        return sum(1 for r in rows if r["arm"] == arm and r["family"] in families)

    for arm in ARMS:
        missing = sum(1 for r in rows if r["arm"] == arm and (r.get("missing") or r.get("empty")))
        answered = sum(1 for r in rows if r["arm"] == arm and r["family"] in ("XC", "XM", "XD")
                       and r.get("offered") and not r.get("refused"))
        print(f"{arm}: missing/empty {missing}")
        print(f"  targets OC+ON success {count(arm, ('OC', 'ON'), 'success')}/{total(arm, ('OC', 'ON'))}  "
              f"selected {count(arm, ('OC', 'ON'), 'selected')}  refused {count(arm, ('OC', 'ON'), 'refused')}")
        print(f"  controls XC+XM+XD answered {answered}/{total(arm, ('XC', 'XM', 'XD'))}  "
              f"choice fired {count(arm, ('XC', 'XM', 'XD'), 'choice')}  refused {count(arm, ('XC', 'XM', 'XD'), 'refused')}")
        op1 = sum(1 for r in rows if r["arm"] == arm and r["id"] == "OP1" and "which string network type"
                  in (session(tag, arm, "OP1", r["rep"]) or ("",))[0].casefold())
        print(f"  OP refused {count(arm, ('OP',), 'refused')}/{total(arm, ('OP',))}  OP1 asks the type {op1}")
        print(f"  OR (report only) success {count(arm, ('OR',), 'success')}/{total(arm, ('OR',))}  "
              f"selected {count(arm, ('OR',), 'selected')}")


if __name__ == "__main__":
    main()
