"""Hybrid H1 debug pass (hybrid spec 2026-10-19, section 6): the contract veto applied offline to the recorded live
sessions of h1, h2 and h3 whose call was DO -- the live system's own workflows, the veto's three reads
(gpt-4o-mini), then code. For debugging only: all three sets are seen, so nothing here is an acceptance figure.

Usage: python3 h1_debug.py run | python3 h1_debug.py show
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.path.insert(0, str(LOGS / "closed-menu-phase1-2026-10-18"))
sys.path.insert(0, str(LOGS / "closed-menu-slim-2026-10-19" / "h3"))
import p1common  # noqa: E402 -- puts this branch's scripts/ on the path
from score_core import outcome  # noqa: E402

from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.graph.contract_veto_call import veto_reads  # noqa: E402
from netzoo_agent_core.interpretation.contract_veto import contract_veto, vetoed_core  # noqa: E402
from netzoo_agent_core.interpretation.semantic_repair import semantic_payload  # noqa: E402

SETS = {"h1": ("closed-menu-phase1b-2026-10-18/heldout/live/h1/structure.json",
               "closed-menu-phase1b-2026-10-18/heldout/items.json"),
        "h2": ("closed-menu-options-first-2026-10-18/h2/live/h2main/structure.json",
               "closed-menu-options-first-2026-10-18/h2/items.json"),
        "h3": ("closed-menu-slim-2026-10-19/h3/live/h3main/structure.json",
               "closed-menu-slim-2026-10-19/h3/items.json")}


def one(job, llm):
    name, item, core = job
    usages = []

    def call(role, messages, schema):
        try:
            adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
            payload, raw = semantic_payload(adapter.invoke(messages))
            usages.append(p1common.usage(raw))
            data = payload.model_dump(mode="json") if hasattr(payload, "model_dump") else dict(payload)
            schema.model_validate(data)
            return data
        except Exception as error:  # noqa: BLE001 -- a failed read leaves the live call (as on the live path)
            usages.append({"input_tokens": 0, "output_tokens": 0, "usd": 0.0, "error": str(error)[:200]})
            return None

    live = CoreDecision.model_validate(core)
    read = veto_reads(item["prompt"], live.workflows, call)
    row = {"set": name, "id": item["id"], "class": item["class"], "live": live.workflows, "calls": len(usages),
           "usd": round(sum(u["usd"] for u in usages), 6), "errors": [u["error"] for u in usages if u.get("error")]}
    if read is None:
        return {**row, "status": "read_failed"}
    slim, pairs, payload = read
    verdict = contract_veto(slim, live.workflows, item["prompt"], payload, pairs)
    after = vetoed_core(live, verdict)
    return {**row, "status": "checked", "kind_after": after.kind, "workflows_after": after.workflows,
            "outcome_before": outcome(item, core)[0], "outcome_after": outcome(item, after.model_dump(mode="json"))[0],
            "vetoes": [{"workflow": v.workflow, "kind": v.kind, "reason": v.reason, "user": v.user_quote,
                        "contract": v.contract_quote, "source": v.source}
                       for w in verdict.vetoed for v in verdict.violations[w]],
            "questions": [{"workflow": q.workflow, "dimension": q.dimension, "values": q.values, "quote": q.quote}
                          for q in verdict.questions],
            "unverified": verdict.unverified, "unconfirmed": verdict.unconfirmed,
            "disclosures": len(verdict.disclosures), "to_confirm": verdict.to_confirm,
            "pairs": len(pairs), "slim": slim.model_dump(mode="json", exclude_defaults=True)}


def run() -> None:
    jobs = []
    for name, (structure, items_path) in SETS.items():
        items = {x["id"]: x for x in json.loads((LOGS / items_path).read_text())["items"]}
        for row in json.loads((LOGS / structure).read_text()).values():
            if (row.get("core") or {}).get("kind") == "DO":
                jobs.append((name, items[row["item"]], row["core"]))
    llm = p1common.build_reader_llm()
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(lambda job: one(job, llm), jobs))
    out = HERE / "h1-debug.json"
    out.write_text(json.dumps({"commit": p1common.git_head(), "rows": rows}, indent=1, ensure_ascii=False),
                   encoding="utf-8")
    print(f"{len(rows)} DO sessions, {sum(r['calls'] for r in rows)} calls, US${sum(r['usd'] for r in rows):.4f}, "
          f"read failed {sum(r['status'] != 'checked' for r in rows)}")


def show() -> None:
    rows = json.loads((HERE / "h1-debug.json").read_text())["rows"]
    for row in rows:
        if row["status"] != "checked":
            print(row["set"], row["id"], row["status"])
            continue
        if row["vetoes"] or row["questions"] or row["outcome_before"] != row["outcome_after"]:
            print(f"{row['set']} {row['id']:4} {row['class']:5} live={','.join(row['live'])} -> {row['kind_after']} "
                  f"{row['outcome_before']} -> {row['outcome_after']}")
            for v in row["vetoes"]:
                print(f"   veto {v['workflow']} {v['kind']} {v['reason'][:90]} | user: {v['user'][:70]!r} | "
                      f"{v['source']}: {v['contract'][:90]!r}")
            for q in row["questions"]:
                print(f"   ask {q['workflow']} {q['dimension']} {q['values']} | {q['quote'][:70]!r}")
    vetoes = [r for r in rows if r.get("vetoes")]
    print("vetoed sessions:", len(vetoes), "by class:",
          {c: sum(1 for r in vetoes if r["class"] == c and r["kind_after"] == "DECLINE") for c in ("do", "dont", "ask", "vague")})
    print("asked sessions:", sum(1 for r in rows if r.get("kind_after") == "ASK"))
    print("outcome changes:", [(r["set"], r["id"], r["outcome_before"], r["outcome_after"]) for r in rows
                               if r.get("outcome_before") != r.get("outcome_after")])
    print("unverified reasons:", sum(len(r.get("unverified") or []) for r in rows))


if __name__ == "__main__":
    {"run": run, "show": show}[sys.argv[1]]()
