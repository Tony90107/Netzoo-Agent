"""G1-G4 (ROUND.md): each DO answer turn of `population.json` through the built step's parts -- the anchor
(`answer_anchor.anchored`), the guard's `judge_answer` (real Jev, cached here; R01's cache copied in, same key) and
`answered_core` on the recorded call. Labels per ROUND.md (unlabelled X02 / R21 rows: gold DO by their items; X22:
gold DECLINE by its item).

Usage: python3 measure.py   (writes measure.json and MEASURE.txt)
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
from netzoo_agent_core.interpretation.answer_anchor import anchored  # noqa: E402

UNLABELLED = {"X02": "meets", "R21": "meets_or_none", "X22": "fails_other_rule"}
CACHE = HERE / "jev-answer-cache.json"
cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
rows = []
for r in json.loads((HERE / "population.json").read_text()):
    if r["after"]["kind"] != "DO":
        continue
    label = r["label"] or UNLABELLED[r["session"].split("-")[2]]
    asked = r["asked"][0]
    workflow = anchored(asked["contract_quote"], asked["workflows"])
    row = {"session": r["session"], "turn": r["turn"], "label": label, "anchored": workflow, "reply": r["reply"],
           "contract": asked["contract_quote"], "after": "DO", "judged": None, "line": None}
    if workflow:
        key = hashlib.sha256(json.dumps([asked["contract_quote"], asked["user_quote"], asked["question"], r["reply"]])
                             .encode()).hexdigest()[:20]
        if key not in cache:
            cache[key] = judge_answer(asked["contract_quote"], asked["user_quote"], asked["question"], r["reply"])
            CACHE.write_text(json.dumps(cache, indent=1))
        judged = cache[key]
        core = CoreDecision(kind="DO", basis=r["after"]["basis"] or "none", workflows=r["after"]["workflows"] or [],
                            evidence={})
        question = {"question": asked["question"], "user_quote": asked["user_quote"], "workflows": asked["workflows"],
                    "labels": {"contract": asked["contract_quote"], "workflow": workflow}}
        after, _action = answered_core(core, question, r["reply"], judged)
        row.update(judged={k: judged[k] for k in ("answer", "confidence")}, after=after.kind,
                   line=after.declined[0].line if after.kind == "DECLINE" else None)
    rows.append(row)
(HERE / "measure.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
gold_do = [r for r in rows if r["label"] in ("meets", "meets_or_none")]
fails = [r for r in rows if r["label"] == "fails" and r["anchored"]]
lines = [f"DO answer turns {len(rows)}; anchored {sum(bool(r['anchored']) for r in rows)}",
         f"G1 gold-DO turns turned DECLINE: {sum(r['after'] == 'DECLINE' for r in gold_do)} of {len(gold_do)} "
         f"(anchored {sum(bool(r['anchored']) for r in gold_do)})",
         f"G2 anchored fails turned DECLINE: {sum(r['after'] == 'DECLINE' for r in fails)} of {len(fails)}",
         "G4 S15 anchored: " + str([r["anchored"] for r in rows if "-S15-" in r["session"]])]
for r in rows:
    if r["anchored"]:
        lines.append(f"  {r['session']:24} {r['label']:15} {r['anchored']:15} {str(r['judged']):45} -> {r['after']}"
                     f" | {r['reply'][:60]}")
text = "\n".join(lines)
(HERE / "MEASURE.txt").write_text(text + "\n")
print(text)
