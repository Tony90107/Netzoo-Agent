"""ROUND-19 step 2: each stated reason judged by gpt-4o-mini against the request and the gold call and reason; R0
lines (no reason) are labelled by code, never sent. The rubric (SYSTEM) is frozen after the 10-reply pilot.

Usage:
  python3 judge.py run REPLIES.json OUT.json [--pilot N]    model calls (announce first)
  python3 judge.py summary JUDGED.json                     per-reply categories and per-type verdicts
"""
from __future__ import annotations

import json
import os
import random
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "usage-fields-2026-10-21"))
import reask  # noqa: E402  (sets the import paths; reads the model settings)

VERDICT = Literal["true_main", "true_other", "false", "not_a_reason", "unsure"]
SYSTEM = (
    "You audit the statements an assistant made when it said that part of a bioinformatics analysis request cannot be "
    "done. You are given the user's request, the correct decision and the correct reason written by experts (and, "
    "when present, the workflow contract text it rests on), and numbered statements from the assistant's reply, each "
    "under the request words it is about. Judge each statement only on whether it is TRUE for this request; never "
    "judge style or completeness.\n"
    "- true_main: true, and it gives the same reason as the expert reason (the same fact, in any words).\n"
    "- true_other: true -- consistent with the user's own words and with the expert reason or contract -- but not the "
    "expert's main reason.\n"
    "- false: it misstates the request (a value, a setting, a data type or a requirement the user did not state, or "
    "attributes the user's words to the wrong setting or quantity), misstates what a workflow can do, or says "
    "something cannot be done when the correct decision is DO.\n"
    "- not_a_reason: it gives no reason (for example an offer of an alternative) and states nothing false. An offer "
    "such as 'X itself can still run, with its own settings instead' is false only if X cannot in fact give what is "
    "asked with its own settings.\n"
    "- unsure: the request and the expert reason do not let you decide.\n"
    "Give each verdict with one short sentence saying why."
)


def _model(count: int):
    from pydantic import ConfigDict, Field, create_model

    fields = {}
    for index in range(1, count + 1):
        fields[f"s{index}_verdict"] = (VERDICT, Field(description=f"Verdict on statement {index}."))
        fields[f"s{index}_why"] = (str, Field(description=f"One short sentence: why, for statement {index}."))
    return create_model("ReasonAudit", __config__=ConfigDict(extra="forbid"), **fields)


def _shown(row: dict, statements: list[dict]) -> str:
    evidence = f"\nContract text: {row['gold_evidence']}" if row["gold_evidence"] else ""
    listed = "\n".join(f'{i}. [about: "{s["quote"][:160]}"] {s["text"]}' for i, s in enumerate(statements, 1))
    return (f"User request: {row['task']}\nCorrect decision: {row['gold']}\nExpert reason: {row['gold_reason']}"
            f"{evidence}\nAssistant's decision: {row['kind']}{' (part of it run)' if row['partial'] else ''}\n"
            f"Statements:\n{listed}")


def judge_one(llm, row: dict) -> dict:
    from netzoo_agent_core.contracts import HumanMessage, SystemMessage
    from netzoo_agent_core.interpretation.semantic_repair import semantic_payload

    statements = [line for line in row["lines"] if line["type"] != "R0"]
    if not statements:
        return {**row, "judged": [], "tokens": [0, 0]}
    schema = _model(len(statements))
    messages = [SystemMessage(content=SYSTEM), HumanMessage(content=_shown(row, statements))]
    try:
        adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
        payload, raw = semantic_payload(adapter.invoke(messages))
        payload = payload.model_dump() if hasattr(payload, "model_dump") else payload
        parsed = schema.model_validate(payload)
        usage = getattr(raw, "usage_metadata", None) or {}
        judged = [{**s, "verdict": getattr(parsed, f"s{i}_verdict"), "why": getattr(parsed, f"s{i}_why")}
                  for i, s in enumerate(statements, 1)]
        return {**row, "judged": judged, "tokens": [usage.get("input_tokens", 0), usage.get("output_tokens", 0)]}
    except Exception as error:  # noqa: BLE001 -- a failed judgement is recorded and judged by hand
        return {**row, "judged": None, "error": f"{type(error).__name__}: {error}"[:300], "tokens": [0, 0]}


def category(row: dict) -> str:
    verdicts = [line["verdict"] for line in row.get("judged") or []]
    if row.get("judged") is None:
        return "failed"
    if "false" in verdicts:
        return "wrong"
    if "true_main" in verdicts:
        return "right"
    if "true_other" in verdicts:
        return "true_not_main"
    if "unsure" in verdicts:
        return "unsure"
    return "no_reason"


def run(replies_path: str, out: str, pilot: int | None):
    reask._env()
    from netzoo_agent_core.graph.capability_check_call import _own_llm

    rows = json.loads(Path(replies_path).read_text())
    if pilot:
        rows = random.Random(19).sample(rows, pilot)
    model = os.environ["OPENROUTER_CAPABILITY_MODEL"]
    llm = _own_llm(model, 4000)
    with ThreadPoolExecutor(6) as pool:
        done = list(pool.map(lambda row: judge_one(llm, row), rows))
    tokens = [sum(r["tokens"][i] for r in done) for i in (0, 1)]
    usd = tokens[0] * reask.PRICE["input"] + tokens[1] * reask.PRICE["output"]
    Path(out).write_text(json.dumps({"model": model, "tokens": tokens, "usd": round(usd, 4), "system": SYSTEM,
                                     "rows": done}, indent=1, ensure_ascii=False))
    print(f"{len(done)} replies judged by {model}; failed {sum(r['judged'] is None for r in done)}; US${usd:.4f}")
    summary(out)


def summary(path: str):
    rows = json.loads(Path(path).read_text())["rows"]
    print("reply categories:", dict(Counter(category(r) for r in rows)))
    for gold in ("DECLINE", "DO", "CLARIFY", "ASK"):
        mine = [r for r in rows if r["gold"] == gold]
        if mine:
            print(f"  gold {gold:8} n={len(mine):3} {dict(Counter(category(r) for r in mine))}")
    print("statement verdicts by type:")
    by_type = Counter((line["type"], line["verdict"]) for r in rows for line in r.get("judged") or [])
    for kind in ("R1", "R2", "R3", "R4", "R5", "ALT"):
        found = {verdict: n for (k, verdict), n in by_type.items() if k == kind}
        if found:
            print(f"  {kind:4} {found}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[0] == "run":
        run(args[1], args[2], int(args[args.index("--pilot") + 1]) if "--pilot" in args else None)
    else:
        summary(args[1])
