"""ROUND.md measurement: each recorded answer turn after an ASK fact_agent -> the guard's judge_answer (real Jev, cached
here) on the turn-1 question's contract line and the reply, and answered_core on the recorded turn-2 call.

Usage: python3 measure.py OUT.json   (needs the Jev key from the app .env; no other model call)
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.graph.jev_guard_call import answered_core, judge_answer  # noqa: E402

CACHE = HERE / "jev-answer-cache.json"
cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
out = []
for r in json.loads((HERE / "population.json").read_text()):
    asked = r["asked"][0]
    key = hashlib.sha256(json.dumps([asked["contract_quote"], asked["user_quote"], asked["question"], r["reply"]])
                         .encode()).hexdigest()[:20]
    if key not in cache:
        cache[key] = judge_answer(asked["contract_quote"], asked["user_quote"], asked["question"], r["reply"])
        CACHE.write_text(json.dumps(cache, indent=1))
    judged = cache[key]
    core = CoreDecision(kind=r["after"]["kind"] or "UNCHECKED", basis=r["after"]["basis"] or "none",
                        workflows=r["after"]["workflows"] or [], evidence={})
    question = {"question": asked["question"], "user_quote": asked["user_quote"], "workflows": asked["workflows"],
                "labels": {"contract": asked["contract_quote"], "workflow": (asked["workflows"] or [""])[0]}}
    after, action = answered_core(core, question, r["reply"], judged) if r["after"]["kind"] else (core, "no_call")
    out.append({"session": r["session"], "turn": r["turn"], "label": r["label"], "before": r["after"]["kind"],
                "judged": {k: judged[k] for k in ("answer", "confidence")}, "action": action, "after": after.kind,
                "line": after.declined[0].line if after.kind == "DECLINE" and after.declined else None,
                "reply": r["reply"]})
Path(sys.argv[1]).write_text(json.dumps(out, indent=1, ensure_ascii=False))
for o in out:
    flag = "CHANGED" if o["after"] != o["before"] else ""
    print(f"{o['session']:26} {o['turn']} {o['label']:14} {o['before']!s:9} {o['judged']['answer']:9} "
          f"{o['judged']['confidence']:.2f} -> {o['after']} {flag} | {o['reply'][:60]}")
