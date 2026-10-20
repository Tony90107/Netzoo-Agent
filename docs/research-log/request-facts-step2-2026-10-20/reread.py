"""ROUND-04 debug re-read (collab/ROUND-04-PLAN.md section 3): the capability check alone, shape 1 vs shape 2.

Seen items only (items.json, frozen before any shape-2 reading) -- a debugging aid, never an acceptance.
Each item is read once per arm with the check's prompt and schema exactly as the live call builds them
(`build_capability_check_messages`, `proposal_model(count, version=...)`); no session, no re-read, no second opinion.
Spending stops at the cap (input $0.15/M, output $0.60/M -- gpt-4o-mini's list price on OpenRouter).

Usage:
  python3 -I reread.py run ARM OUT.json [--model M] [--cap USD] [--spent USD]   ARM: 1 (shape 1) or 2 (shape 2)
  python3 -I reread.py score OUT1.json OUT2.json                                  per item and per gate
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREE = HERE.parents[2]
sys.path.insert(0, str(WORKTREE / "scripts"))
DOTENV = WORKTREE.parents[1] / "netzoo_agent" / ".env"  # the main checkout's; worktrees carry none

PRICE = {"openai/gpt-4o-mini": (0.15, 0.60)}  # USD per million tokens (input, output)


def _items():
    return json.loads((HERE / "items.json").read_text())["items"]


def run(arm: int, out: str, model: str, cap: float, spent: float):
    from dotenv import dotenv_values

    for key, value in dotenv_values(DOTENV, interpolate=False).items():
        if value is not None:
            os.environ.setdefault(key, value)
    from netzoo_agent_core.contracts.capability_check import proposal_model
    from netzoo_agent_core.graph.capability_check_call import build_capability_check_messages
    from netzoo_agent_core.interpretation.semantic_repair import semantic_payload
    from netzoo_agent_core.llm import build_llm, validate_router_model

    llm = build_llm(validate_router_model(model), 0.0, max_output_tokens=4000, timeout_seconds=180)
    price_in, price_out = PRICE[model]
    path = Path(out)
    found = json.loads(path.read_text()) if path.exists() else {}
    for item in _items():
        if item["id"] in found and found[item["id"]].get("status") == "success":
            continue
        for attempt in (1, 2):
            if spent >= cap:
                print(f"cap reached at US${spent:.4f}; stopping")
                path.write_text(json.dumps(found, indent=1))
                return
            messages, count = build_capability_check_messages(item["task"])
            schema = proposal_model(count, version=arm)
            started = time.time()
            row = {"arm": arm, "model": model, "attempt": attempt}
            try:
                adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
                payload, raw = semantic_payload(adapter.invoke(messages))
                usage = getattr(raw, "usage_metadata", None) or {}
                row.update(input_tokens=usage.get("input_tokens", 0), output_tokens=usage.get("output_tokens", 0))
                payload = payload.model_dump() if hasattr(payload, "model_dump") else payload
                schema.model_validate(payload)
                row.update(status="success", proposal=payload)
            except Exception as error:  # noqa: BLE001 -- recorded; a second attempt counts toward the cap
                row.update(status="failed", error=f"{type(error).__name__}: {str(error)[:500]}")
            row["seconds"] = round(time.time() - started, 1)
            cost = (row.get("input_tokens", 0) * price_in + row.get("output_tokens", 0) * price_out) / 1e6
            if row["status"] != "success" and not row.get("input_tokens"):
                cost = (15000 * price_in + 900 * price_out) / 1e6  # a failed call is charged as a p90 call
            row["usd"] = round(cost, 6)
            spent += cost
            found[item["id"]] = row
            print(f"{item['id']:6} arm {arm} {row['status']:7} in {row.get('input_tokens', 0):6} "
                  f"out {row.get('output_tokens', 0):5} {row['seconds']:5}s  total US${spent:.4f}", flush=True)
            path.write_text(json.dumps(found, indent=1))
            if row["status"] == "success":
                break
    print(f"done; spent US${spent:.4f}")


# -- scoring --------------------------------------------------------------------------------------------------------

def _check(item, row):
    from netzoo_agent_core.contracts.capability_check import proposal_model
    from netzoo_agent_core.interpretation.capability_check import build_capability_check

    count = sum(1 for name in row["proposal"] if name[1:].isdigit())
    proposal = proposal_model(count, version=row["arm"]).model_validate(row["proposal"])
    return build_capability_check(item["task"], proposal)[0]


def _fold(text) -> str:
    return re.sub(r"[^0-9a-z]+", "", str(text).casefold())


def _rows(check, item, scope):
    from netzoo_agent_core.interpretation.request_spans import _span

    rows = [row for row in check.results() if row.status != "not_checked"]
    if scope == "all":
        return rows, []
    spans = [found for words in scope if (found := _span(item["task"], words)) is not None]
    inside = lambda row: (s := _span(item["task"], row.quote)) is not None and any(  # noqa: E731
        s[0] < b and a < s[1] for a, b in spans)
    return [row for row in rows if inside(row)], [row for row in rows if not inside(row)]


def _carries(row, fact) -> bool:
    method = row.method
    if fact["property"] == "sample_count":
        return method.get("samples") == fact["value"]
    if fact["property"] == "feature_count":
        return any(count == fact["value"] for *_span, count in method.get("feature_items", []))
    return any(setting["name"] == fact["name"] and _fold(fact["value"]) in _fold(setting.get("value", "") + " "
                                                                               + setting.get("quote", ""))
               for setting in method.get("settings", []))


def _read(check, fact) -> bool:
    if fact["property"] == "candidates":
        prop = {"samples": "sample_count", "features": "feature_count"}[fact["of"]]
        return any(f.property == prop and f.state == "unsure" and sorted(map(float, f.values)) ==
                   sorted(map(float, fact["values"])) for f in check.facts)
    for f in check.facts:
        if f.origin != "user_stated" or f.state != "stated":
            continue
        if fact["property"] in ("sample_count", "feature_count") and f.property == fact["property"] \
                and float(f.value) == fact["value"]:
            return True
        if fact["property"] == "setting" and f.property == "setting" and f.name == fact["name"] \
                and _fold(fact["value"]) in _fold(f.value + " " + f.quote):
            return True
    return False


def score_item(item, row) -> dict:
    check = _check(item, row)
    found = {"read": 0, "expected": 0, "placed": 0, "placements": 0, "misapplied": 0, "notes": []}
    for fact in item["expected"]:
        found["expected"] += 1
        if _read(check, fact):
            found["read"] += 1
        else:
            found["notes"].append(f"not read: {fact}")
        if fact["property"] == "candidates":
            continue
        inside, outside = _rows(check, item, fact["scope"])
        for result in inside:
            found["placements"] += 1
            if _carries(result, fact):
                found["placed"] += 1
        for result in outside:
            if _carries(result, fact):
                found["misapplied"] += 1
                found["notes"].append(f"misapplied {fact} -> {result.quote[:50]}")
    found["calls"] = [(r.quote[:60], r.status, sorted({k.split('.')[0] for k in r.delivered_by})) for r in check.results()
                      if r.status != "not_checked"]
    found["conflicts"] = [c.reason for c in check.fact_conflicts]
    found["owners"] = {f.quote: f.belongs_to for f in check.facts if f.property == "feature_count" and f.belongs_to}
    return found


def _leaves(value) -> int:
    if isinstance(value, dict):
        return sum(_leaves(v) for v in value.values())
    if isinstance(value, list):
        return sum(_leaves(v) for v in value) if value else 1
    return 1


def score(path1: str, path2: str):
    one, two = json.loads(Path(path1).read_text()), json.loads(Path(path2).read_text())
    totals = {arm: {"read": 0, "expected": 0, "placed": 0, "placements": 0, "misapplied": 0, "out": 0, "in": 0,
                    "leaves": 0, "usd": 0.0, "items": 0} for arm in (1, 2)}
    report = {}
    for item in _items():
        rows = {1: one.get(item["id"]), 2: two.get(item["id"])}
        if not all(row and row.get("status") == "success" for row in rows.values()):
            report[item["id"]] = {"skipped": {arm: (row or {}).get("status") for arm, row in rows.items()}}
            continue
        report[item["id"]] = {"gold": item["gold_class"], "category": item["category"]}
        for arm, row in rows.items():
            found = score_item(item, row)
            report[item["id"]][arm] = found
            for key in ("read", "expected", "placed", "placements", "misapplied"):
                totals[arm][key] += found[key]
            totals[arm]["out"] += row["output_tokens"]
            totals[arm]["in"] += row["input_tokens"]
            totals[arm]["leaves"] += _leaves(row["proposal"])
            totals[arm]["usd"] += row["usd"]
            totals[arm]["items"] += 1
    print(json.dumps(totals, indent=1))
    for iid, found in report.items():
        if "skipped" in found:
            print(iid, "skipped", found["skipped"])
            continue
        a, b = found[1], found[2]
        print(f"{iid:6} [{found['gold'] or '-':4}] read {a['read']}/{a['expected']} -> {b['read']}/{b['expected']}  "
              f"placed {a['placed']}/{a['placements']} -> {b['placed']}/{b['placements']}  "
              f"misapplied {a['misapplied']} -> {b['misapplied']}")
        if a["calls"] != b["calls"]:
            print("        calls 1:", a["calls"])
            print("        calls 2:", b["calls"])
        for note in b["notes"]:
            print("        B", note)
        if b["conflicts"] or b["owners"]:
            print("        B conflicts", b["conflicts"], "owners", b["owners"])
    Path(HERE / "score.json").write_text(json.dumps({"totals": totals, "items": report}, indent=1, default=str))


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[0] == "run":
        option = lambda name, default: args[args.index(name) + 1] if name in args else default  # noqa: E731
        run(int(args[1]), args[2], option("--model", "openai/gpt-4o-mini"), float(option("--cap", "0.32")),
            float(option("--spent", "0")))
    elif args[0] == "score":
        score(args[1], args[2])
