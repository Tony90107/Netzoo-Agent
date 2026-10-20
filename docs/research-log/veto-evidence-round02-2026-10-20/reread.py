"""ROUND-02 debug re-read (user decision 2026-10-20): the veto's reads re-run with gpt-4o-mini on six seen sessions,
to see whether the new read shape fills its ownership fields right -- counts' belongs_to and operands, data's
input_for, and the doubts. Debug only: every item is seen (h3 L13, h4 M01 M25 M38 M40 M46); nothing here is an
acceptance figure. One read per item at temperature 0; the raw payloads are kept.

    python3 reread.py run    # paid: about US$0.01; writes reread.json
    python3 reread.py show   # $0: compares reread.json with gold-cells.json
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.path.insert(0, str(LOGS / "closed-menu-phase1-2026-10-18"))
import p1common  # noqa: E402 -- puts this branch's scripts/ on the path

from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.graph.contract_veto_call import veto_reads  # noqa: E402
from netzoo_agent_core.interpretation.contract_veto import contract_veto, vetoed_core  # noqa: E402
from netzoo_agent_core.interpretation.semantic_repair import semantic_payload  # noqa: E402
from netzoo_agent_core.interpretation.veto_evidence import veto_ledger  # noqa: E402

ITEMS = {"h4": ("closed-menu-hybrid-2026-10-19/h4/items.json", ("M01", "M25", "M38", "M40", "M46")),
         "h3": ("closed-menu-slim-2026-10-19/h3/items.json", ("L13",))}


def jobs() -> list:
    found = []
    veto = {r["id"]: r for r in json.loads((LOGS / "closed-menu-hybrid-2026-10-19/h4/live/h4/veto.json").read_text())["rows"]}
    h3 = {r["item"]: r for r in json.loads((LOGS / "closed-menu-slim-2026-10-19/h3/live/h3main/structure.json")
                                          .read_text()).values()}
    for name, (path, ids) in ITEMS.items():
        items = {x["id"]: x for x in json.loads((LOGS / path).read_text())["items"]}
        for item_id in ids:
            core = veto[item_id]["core_before"] if name == "h4" else h3[item_id]["core"]
            found.append((name, items[item_id], core))
    return found


def one(job, llm):
    name, item, core = job
    usages, payloads = [], {}

    def call(role, messages, schema):
        try:
            adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
            payload, raw = semantic_payload(adapter.invoke(messages))
            usages.append(p1common.usage(raw))
            data = payload.model_dump(mode="json") if hasattr(payload, "model_dump") else dict(payload)
            schema.model_validate(data)
            payloads[role] = data
            return data
        except Exception as error:  # noqa: BLE001 -- a failed read leaves the live call, as on the live path
            usages.append({"input_tokens": 0, "output_tokens": 0, "usd": 0.0, "error": str(error)[:300]})
            return None

    live = CoreDecision.model_validate(core)
    reports: list = []
    read = veto_reads(item["prompt"], live.workflows, call, reports)
    row = {"set": name, "id": item["id"], "class": item["class"], "workflows": live.workflows, "calls": len(usages),
           "usd": round(sum(u["usd"] for u in usages), 6), "errors": [u["error"] for u in usages if u.get("error")],
           "payloads": payloads}
    if read is None:
        return {**row, "status": "read_failed"}
    slim, pairs, check = read
    verdict = contract_veto(slim, live.workflows, item["prompt"], check, pairs)
    after = vetoed_core(live, verdict)
    return {**row, "status": "checked", "kind_after": after.kind,
            "vetoes": [[v.workflow, v.kind, v.reason, v.user_quote] for w in verdict.vetoed for v in verdict.violations[w]],
            "questions": [f.question for f in after.facts], "set_aside": verdict.set_aside,
            "dropped_questions": verdict.dropped_questions, "dropped": [line for r in reports for line in r.dropped],
            "slim": slim.model_dump(mode="json", exclude_defaults=True),
            "ledger": veto_ledger(live.workflows, "checked", slim, reports, verdict, verdict.set_aside)}


def run() -> None:
    llm = p1common.build_reader_llm()
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(lambda job: one(job, llm), jobs()))
    (HERE / "reread.json").write_text(json.dumps({"commit": p1common.git_head(), "model": p1common.MODEL, "rows": rows},
                                                 indent=1, ensure_ascii=False) + "\n")
    print(f"{len(rows)} sessions, {sum(r['calls'] for r in rows)} calls, US${sum(r['usd'] for r in rows):.4f}, "
          f"read failed {sum(r['status'] != 'checked' for r in rows)}")


def show() -> None:
    gold = json.loads((HERE / "gold-cells.json").read_text())["items"]
    for row in json.loads((HERE / "reread.json").read_text())["rows"]:
        g = gold.get(row["id"], {})
        print(f"\n== {row['set']} {row['id']} [{row['class']}] {row['status']} -> {row.get('kind_after')} "
              f"(gold vetoes {g.get('violations')}, questions {g.get('questions')})")
        for name, payload in row["payloads"].items():
            if name == "contract_veto_core":
                print("  core data:", [(d["kind"], d["status"], d["quote"][:40], d["input_for"], d["corrects"])
                                       for d in payload.get("data", [])])
            if name == "contract_veto_limits":
                print("  counts:", [(c["what"], c["layer"], c["value"], c["values"], c["quote"][:45], c["belongs_to"],
                                     c["corrects"]) for c in payload.get("counts", [])])
                print("  settings:", [(s["control"], s["value"], s["values"], s["quote"][:40])
                                      for s in payload.get("settings", [])])
        for f in row.get("slim", {}).get("stated", []):
            if f.get("field") == "B6":
                print(f"  B6 {f['name']}: {f.get('value') or f.get('values')} derived={f.get('derived', '')!r} "
                      f"evidence={[(e.get('belongs_to'), e.get('role', 'value'), e.get('values')) for e in f.get('evidence', [])]}")
        print("  vetoes:", row.get("vetoes"), "\n  questions:", row.get("questions"), "\n  set aside:", row.get("set_aside"),
              "\n  dropped questions:", row.get("dropped_questions"), "\n  errors:", row["errors"])


if __name__ == "__main__":
    {"run": run, "show": show}[sys.argv[1]]()
