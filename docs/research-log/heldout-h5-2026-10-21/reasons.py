"""h5 metric 3 (ROUND.md), no model calls: every h5main session whose call says something cannot be done (DECLINE, or
DO with a part not available), its stated reasons tagged by source exactly as ROUND-20's `replies.py` tags them (this
checkout's `stated()` path), with the item's gold class, reason and evidence -- the input of ROUND-19's frozen
`judge.py`. Each session is B2-replayed from its own recording (the frozen code is this code); a replayed call that
differs from the live one is listed and left out.

Usage: python3 reasons.py OUT.json
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
spec = importlib.util.spec_from_file_location("replies20", LOGS / "stated-reasons-2026-10-21/replies.py")
replies20 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replies20)  # sets the harness import paths
harness = replies20.harness
GOLD = {"do": "DO", "dont": "DECLINE", "ask": "ASK", "vague": "CLARIFY"}
SESSION = re.compile(r"^hb-h5main-(Q\d+)-(\d)$")


def main(out: str):
    import netzoo_agent_core.interpretation.core_decision as core_decision
    from types import SimpleNamespace

    from netzoo_agent_core.graph.response import respond
    from netzoo_agent_core.policy import ProjectPolicyLoader

    items = {i["id"]: i for i in json.loads((HERE / "items.json").read_text())["items"]}
    context = SimpleNamespace(project_policy=ProjectPolicyLoader(LOGS.parents[1]).load())
    original, seen, rows, mismatched = core_decision.decide_core, {}, [], []

    def spy(decision, task="", **kwargs):
        seen["decision"], seen["core"] = decision, original(decision, task, **kwargs)
        return seen["core"]

    for key, folder, sid, task, payload, reread, found, _n in harness.readings():
        match = SESSION.match(sid)
        if not match:
            continue
        item = items[match.group(1)]
        live = next((e["payload"] for e in reversed(found) if e["event_type"] == "core.decision"), {})
        core_decision.decide_core = spy
        try:
            harness.replay_full.replay(folder, task, payload, reread, found)
        finally:
            core_decision.decide_core = original
        call = seen["core"]
        if call.kind != live.get("kind"):
            mismatched.append((sid, live.get("kind"), call.kind))
            continue
        if not (call.kind == "DECLINE" or (call.kind == "DO" and call.partial)):
            continue
        final = core_decision.with_core(seen["decision"], call)
        try:
            reply = respond(context, {"decision": final.model_dump(mode="json"), "messages": []})["messages"][-1].content
        except KeyError:
            from netzoo_agent_core.interpretation.capability_check import understanding_paragraph
            reply = "[paragraph only] " + (understanding_paragraph(final.capability_check) or "")
        lines = []
        for row in (final.capability_check.results() if final.capability_check else []):
            if row.status in ("not_available", "partial"):
                for kind, text in replies20.tagged(row, final.capability_check) or [("R0", "")]:
                    lines.append({"quote": row.quote, "status": row.status, "type": kind, "text": text})
        if not lines:
            lines.append({"quote": task, "status": "not_available", "type": "R0", "text": ""})
        rows.append({"key": key, "session": sid, "item": item["id"], "task": task, "gold": GOLD[item["class"]],
                     "gold_reason": item["reason"], "gold_evidence": item["evidence"], "kind": call.kind,
                     "basis": call.basis, "partial": call.partial, "lines": lines, "reply": reply})
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    print(f"{len(rows)} replies saying something cannot be done; replay differs from live on {len(mismatched)}: "
          f"{mismatched}")


if __name__ == "__main__":
    main(sys.argv[1])
