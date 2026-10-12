"""Verdict layer step 1: what the live run path did with each run17 request, and what the shadow check said.

Usage (repository root): python docs/research-log/run-path-2026-10-12/analyze_run17.py <tag> <repeats>

Gold comes from heldout17 (Log 411): an item is `neg` when every requirement is not_supported, `pos` when every
requirement is supported, with_step or needs_input, else `mixed`. Per session:
- path: run (routing selected a run or download action) or guidance;
- live_fa: a neg item on the run path, or a run of a workflow outside a pos item's gold `by`;
- shadow: the recorded `routing.run_check_shadow` verdict (run path only).
No model is called.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TREE = ROOT.parent / ".worktrees" / "netzoo-rp-shadow" / ".netzoo"
sys.path.insert(0, str(ROOT / "scripts"))
from workflow_registry import ACTION_DEFINITIONS  # noqa: E402

GOLD = {item["id"]: item for item in json.loads((ROOT / "docs/research-log/rescore-2026-10-12/heldout17.json")
                                                .read_text())["items"]}


def gold_class(item):
    expects = {r["expect"] for r in item["requirements"]}
    return "neg" if expects == {"not_supported"} else "pos" if "not_supported" not in expects else "mixed"


def shadow_event(run_id):
    path = TREE / "traces" / run_id / "events.jsonl"
    if not path.exists():
        return None
    for line in path.read_text().splitlines():
        event = json.loads(line)
        if event.get("type") == "routing.run_check_shadow":
            return event.get("payload")
    return None


def main():
    tag, repeats = sys.argv[1], int(sys.argv[2])
    rows = []
    for item in json.loads((HERE / "run17.json").read_text()):
        gold = GOLD[item["id"]]
        for rep in range(1, repeats + 1):
            path = TREE / "sessions" / f"ve-{tag}-shadow-{item['id']}-{rep}.json"
            if not path.exists():
                rows.append({"id": item["id"], "rep": rep, "missing": True})
                continue
            data = json.loads(path.read_text())
            plan = data.get("plan") or {}
            action = (plan.get("decision") or {}).get("action")
            run = action not in (None, "no_tool")
            by = {w for r in gold["requirements"] for w in r.get("by", [])}
            workflow = ACTION_DEFINITIONS[action].workflow if run and action in ACTION_DEFINITIONS else None
            klass = gold_class(gold)
            shadow = shadow_event(data.get("run_id", "")) if run else None
            rows.append({"id": item["id"], "rep": rep, "family": gold["family"], "gold": klass, "action": action,
                         "path": "run" if run else "guidance", "plan_status": plan.get("status"),
                         "live_fa": run and (klass == "neg" or (klass == "pos" and bool(by) and workflow not in by)),
                         "shadow": (shadow or {}).get("verdict"), "shadow_results": (shadow or {}).get("results")})
    (HERE / "live").mkdir(exist_ok=True)
    (HERE / "live" / f"{tag}-metrics.json").write_text(json.dumps(rows, indent=1))
    done = [r for r in rows if not r.get("missing")]
    print(f"sessions {len(done)}/{len(rows)}")
    print("path by gold:", dict(collections.Counter((r["gold"], r["path"]) for r in done)))
    print("live run-path false accepts:", sum(r["live_fa"] for r in done))
    for klass in ("neg", "mixed", "pos"):
        verdicts = collections.Counter(r["shadow"] for r in done if r["path"] == "run" and r["gold"] == klass)
        print(f"shadow on run path, gold {klass}:", dict(verdicts))
    fa = [r for r in done if r["live_fa"]]
    caught = sum(r["shadow"] in ("gap", "other_workflow", "partial_gap") for r in fa)
    print(f"false accepts the shadow would flag: {caught}/{len(fa)}")
    pos_run = [r for r in done if r["path"] == "run" and r["gold"] == "pos" and not r["live_fa"]]
    wrong = sum(r["shadow"] in ("gap", "other_workflow", "partial_gap") for r in pos_run)
    print(f"correct runs the shadow would flag (cost): {wrong}/{len(pos_run)}")


if __name__ == "__main__":
    main()
