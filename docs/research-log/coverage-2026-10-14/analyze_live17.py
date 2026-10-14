"""Items 4-5 live check: what each live17 session read, re-read and answered. No model is called.

Usage (repository root): python docs/research-log/coverage-2026-10-14/analyze_live17.py <tag> [items.json]

Per session: provider failures (a 402/429 voids it), the first check's results and unchecked sentences, the re-read's
passages and what it found, the final check (on the routed decision), the action, and the reply. Verdicts:
- miss: every gold requirement is read as a result, the unsupported ones not available, the supported ones not;
- control: the re-read adds no result, and no gold-supported requirement ends unavailable;
- chitchat: no sentence is left unchecked and the re-read adds no result;
- file_checked (F41): no result waits on a fact.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TREE = ROOT.parent / ".worktrees" / "netzoo-cov-live" / ".netzoo"
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.interpretation.capability_check import _span  # noqa: E402

ITEMS = json.loads((HERE / (sys.argv[2] if len(sys.argv) > 2 else "live17.json")).read_text())


def overlaps(a, b):
    return a is not None and b is not None and min(a[1], b[1]) > max(a[0], b[0])


def analyse(tag, item):
    path = TREE / "sessions" / f"cv-{tag}-{item['id']}.json"
    if not path.exists():
        return {"id": item["id"], "verdict": "MISSING"}
    data = json.loads(path.read_text())
    events = [json.loads(line) for line in (TREE / "traces" / str(data["run_id"]) / "events.jsonl").read_text().splitlines()]
    kinds = [e["event_type"] for e in events]
    failures = [e["payload"].get("error_message", "")[:120] for e in events
                if e["event_type"].endswith("_failed") and any(code in json.dumps(e["payload"]) for code in ("402", "429"))]
    first = next((e["payload"]["check"] for e in events if e["event_type"] == "routing.capability_checked"), None)
    reread = [e["payload"] for e in events if e["event_type"] == "routing.capability_reread"]
    decision = (data.get("plan") or {}).get("decision") or {}
    final = decision.get("capability_check") or (reread[-1]["check"] if reread else first) or {}
    task = item["prompt"]
    results = [(r["quote"], r["status"], r.get("file_checked")) for r in final.get("requirements", [])
               if r["kind"] == "result"]
    first_results = {r["quote"] for r in (first or {}).get("requirements", []) if r["kind"] == "result"}
    added = [quote for quote, _status, _f in results if quote not in first_results]
    gold = []
    for requirement in item.get("requirements") or []:
        span = _span(task, requirement["words"])
        hit = [status for quote, status, _f in results if overlaps(span, _span(task, quote))]
        gold.append((requirement["words"], requirement["expect"], hit))
    if item["kind"] == "miss":
        ok = all(hit and (all(s == "not_available" for s in hit) if expect == "not_supported"
                          else all(s != "not_available" for s in hit)) for _w, expect, hit in gold)
    elif item["kind"] == "control":
        ok = not added and all(not hit or all(s != "not_available" for s in hit)
                               for _w, expect, hit in gold if expect != "not_supported")
    elif item["kind"] == "chitchat":
        ok = not final.get("unchecked") and not added
    elif item["kind"] == "format":  # c2: a file format or a remark is never a delivery, nor any result unavailable
        deliveries = [r["quote"] for r in final.get("requirements", []) if "delivery" in (r.get("not_by") or [])]
        ok = not deliveries and all(not hit or all(s != "not_available" for s in hit)
                                    for _w, expect, hit in gold if expect != "not_supported")
    else:
        ok = all(status != "needs_fact" for _q, status, _f in results)
    reply = next((m["content"] for m in reversed(data["messages"]) if m["role"] == "assistant"), "")
    return {"id": item["id"], "kind": item["kind"], "verdict": "VOID" if failures else ("PASS" if ok else "FAIL"),
            "failures": failures, "action": decision.get("action"), "first_unchecked": (first or {}).get("unchecked"),
            "passages": [r["passages"] for r in reread], "reread_found": [
                [a["quote"] for s in (r.get("reread") or {}).values() for a in s.get("asks", [])] for r in reread],
            "results": results, "added": added, "unchecked": final.get("unchecked"), "gold": gold,
            "semantic_failed": "routing.semantic_interpreter_failed" in kinds, "reply": reply}


def main():
    tag = sys.argv[1]
    rows = [analyse(tag, item) for item in ITEMS]
    for row in rows:
        print(f"== {row['id']} [{row.get('kind')}] {row['verdict']}  action={row.get('action')}")
        for key in ("failures", "first_unchecked", "passages", "reread_found", "results", "added", "unchecked", "gold"):
            if row.get(key):
                print(f"   {key}: {row[key]}")
    counts = {}
    for row in rows:
        counts.setdefault(row.get("kind"), {}).setdefault(row["verdict"], 0)
        counts[row.get("kind")][row["verdict"]] += 1
    print(json.dumps(counts))
    (HERE / f"{tag}-analysis.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
