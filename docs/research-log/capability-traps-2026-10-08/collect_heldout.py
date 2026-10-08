"""Log 387: collect both arms' held-out sessions, structural counters, and a blinded labelling file.

Usage (any directory): python3 docs/research-log/capability-traps-2026-10-08/collect_heldout.py <tag> <repeats>
Writes heldout-live/<tag>-structure.json (per session: status, candidates, calls, whether the capability
check ran, its full_gap and lines), <tag>-blinded.md (arms and ids shuffled; the item's kind, core and
accept/nearest shown, as in Log 385) and <tag>-blind-key.json. Nothing calls a model.
"""
import json
import os
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREES = Path("/Users/chenzhonghan/Documents/LLM AGENT/.worktrees")
ARMS = {"base": WORKTREES / "netzoo-trap-base", "cand": WORKTREES / "netzoo-cc-cand"}
ITEMS = {item["id"]: item for item in json.loads((HERE / os.environ.get("HELDOUT", "heldout1.json")).read_text())["items"]}
KIND = {"U": "UNSUPPORTED_CORE", "N": "UNSUPPORTED_CORE", "P": "HALF", "C": "SUPPORTED"}


def main(tag, repeats):
    rows, blocks = {}, []
    for arm, root in ARMS.items():
        for key, item in ITEMS.items():
            for rep in range(1, repeats + 1):
                sid = f"ce-{tag}-{arm}-{key}-{rep}"
                path = root / ".netzoo" / "sessions" / f"{sid}.json"
                if not path.exists():
                    rows[sid] = {"missing": True}
                    continue
                session = json.loads(path.read_text())
                decision = (session.get("plan") or {}).get("decision") or {}
                reply = next((m.get("content") for m in reversed(session.get("messages", []))
                              if m.get("type") in ("ai", "AIMessage") or m.get("role") == "assistant"), "")
                calls = (session.get("token_usage") or {}).get("calls", [])
                check = decision.get("capability_check") or {}
                rows[sid] = {
                    "arm": arm, "item": key, "family": item["family"],
                    "status": decision.get("capability_match_status"), "action": decision.get("action"),
                    "matched": decision.get("matched_actions"), "candidates": decision.get("hypothesis_actions"),
                    "recommended": decision.get("recommended_actions"),
                    "roles": [c.get("role") for c in calls],
                    "check_call": next((c.get("status") for c in calls if c.get("role") == "capability_check"), None),
                    "budget_exhausted": (session.get("token_usage") or {}).get("budget_exhausted"),
                    "model_written": any(c.get("role") == "response" for c in calls),
                    "errors": [c.get("exception") for c in calls if c.get("exception")],
                    "full_gap": check.get("full_gap"),
                    "requirements": check.get("requirements"), "unchecked": check.get("unchecked"),
                    "cost": sum((c.get("cost_micro_usd") or 0) for c in calls) / 1e6,
                }
                header = [f"- kind: {KIND[item['family']]}", f"- core: {item['core']}"]
                if item["family"] in "UN":
                    header.append(f"- nearest (may be offered only with the core stated as not produced): {item['nearest']}")
                if item.get("accept"):
                    header.append(f"- accept: {item['accept']}")
                blocks.append((sid, "\n".join([f"> {item['prompt']}", "", *header, "", "Full reply:", "", "```",
                                                 str(reply), "```", ""])))
    random.seed(387)
    random.shuffle(blocks)
    key_map, out = {}, ["# Blinded held-out sessions for labelling", ""]
    for index, (sid, body) in enumerate(blocks, 1):
        code = f"H{index:03d}"
        key_map[code] = sid
        out += [f"## {code}", "", body]
    (HERE / "heldout-live" / f"{tag}-structure.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    (HERE / "heldout-live" / f"{tag}-blinded.md").write_text("\n".join(out), encoding="utf-8")
    (HERE / "heldout-live" / f"{tag}-blind-key.json").write_text(json.dumps(key_map, indent=1))
    print("sessions", len(rows), "missing", sum(1 for r in rows.values() if r.get("missing")))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
