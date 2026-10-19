"""Slim reading S2 (spec 2026-10-19, 6.1): the 85 dev items, reading only (gpt-4o-mini).

Per item: the core read, the focused read when step 2 chooses B fields (`read_slim`), the requirement contract check
when a thing asked carries a requirement (phase 1b, unchanged), then `decide_menu`. Nothing else of the agent runs.
Recorded: both payloads and the values each writes, the slim reading, the fields step 2 chose, what code dropped,
the call, tokens and cost.

Scored (`score`): the three error proxies (spec 1) on the dev classes -- false accepts (a dont item run, partly
included), false refusals (a do item refused, partly included), missed asks (an ask item run or refused) -- beside
the phase-1 reader's last arm on the same items (d9 final); values written per read; and, when the blind label files
exist, A1 accuracy (`a1-labels.json`) and misfilled fields (`fact-labels.json`).

Usage: python3 s2.py read TAG | python3 s2.py score TAG | python3 s2.py facts TAG (writes the facts to label)
"""

from __future__ import annotations

import json
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
P1 = ROOT / "docs/research-log/closed-menu-phase1-2026-10-18"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(P1))

import p1common  # noqa: E402
from dev import outcome  # noqa: E402

from netzoo_agent_core.graph.menu_reading_call import read_requirements  # noqa: E402
from netzoo_agent_core.graph.slim_reading_call import read_slim  # noqa: E402
from netzoo_agent_core.interpretation.menu_decision import decide_menu  # noqa: E402
from netzoo_agent_core.interpretation.slim_reader import SLIM_SHAPE, to_menu, wire_values  # noqa: E402

ITEMS = json.loads((P1 / "dev_items.json").read_text())["items"]


def one(item: dict, llm, keep_menu: bool = False) -> dict:
    prompt = item["prompt"]
    read = read_slim(prompt, llm)
    menu = to_menu(read.reading)
    calls = [p1common.usage(raw) for raw in read.raws]
    req = {"ran": False}
    if read.reading.status == "read":
        checked, pairs = read_requirements(prompt, menu, llm)
        if checked is not None:
            menu = checked.reading
            req = {"ran": True, "pairs": len(pairs), "error": checked.error, **p1common.usage(checked.raw)}
            calls.append(p1common.usage(checked.raw))
    decision = decide_menu(menu, prompt)
    core_values = wire_values(read.core_payload) if read.core_payload else (0, 0)
    focus_values = wire_values(read.focus_payload) if read.focus_payload else (0, 0)
    return {
        "id": item["id"], "class": item["class"], "status": read.reading.status, "error": read.error,
        "focus_error": read.focus_error, "seconds": read.seconds,
        "input_tokens": sum(c["input_tokens"] for c in calls), "output_tokens": sum(c["output_tokens"] for c in calls),
        "usd": round(sum(c["usd"] for c in calls), 6), "calls": len(calls),
        "kind": decision.kind, "basis": decision.basis, "workflows": decision.workflows, "partial": decision.partial,
        "questions": [q.dimension for q in decision.questions], "settled": decision.settled,
        "reasons": [r for d in decision.declined for r in d.reasons],
        "options": [o.workflow for o in decision.options], "evidence": decision.evidence,
        "needs": {"candidates": list(read.needs.candidates), "cells": [c[0] for c in read.needs.cells()],
                  "counts": list(read.needs.counts)},
        "values": {"core": core_values, "focus": focus_values,
                   "written": core_values[0] + focus_values[0], "content": core_values[1] + focus_values[1]},
        "dropped": read.report.dropped + read.focus_report.dropped,
        "filled": read.report.filled + read.focus_report.filled, "req": req,
        "slim": read.reading.model_dump(mode="json", exclude_defaults=True),
        "core_payload": read.core_payload, "focus_payload": read.focus_payload,
        **({"menu": menu.model_dump(mode="json")} if keep_menu else {}),
    }


def read(tag: str) -> None:
    llm = p1common.build_reader_llm()
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(lambda item: one(item, llm), ITEMS))
    print(f"{len(rows)} items, {sum(r['calls'] for r in rows)} calls, US${sum(r['usd'] for r in rows):.4f}, "
          f"failed {sum(r['status'] == 'failed' for r in rows)}, focus failed {sum(bool(r['focus_error']) for r in rows)}")
    p1common.write(HERE / "live" / tag / "dev.json", {"commit": p1common.git_head(), "shape": SLIM_SHAPE, "rows": rows})


ERRORS = {"false_accept": ("dont", ("accepted", "partial")), "false_refusal": ("do", ("refused",)),
          "missed_ask": ("ask", ("committed", "refused"))}


def proxies(rows: list[dict]) -> dict:
    found = {name: [r["id"] for r in rows if r["class"] == cls and outcome(cls, r) in bad]
             for name, (cls, bad) in ERRORS.items()}
    found["failed"] = [r["id"] for r in rows if r["status"] == "failed"]
    return found


def score(tag: str) -> None:
    rows = json.loads((HERE / "live" / tag / "dev.json").read_text())["rows"]
    old = json.loads((P1 / "live/d9/dev.json").read_text())["rows"]
    old = [{**r, **r["final"]} if "final" in r else r for r in old]
    report: dict = {"tag": tag}
    for name, found in (("slim", rows), ("phase-1 reader d9 final", old)):
        p = proxies(found)
        table: dict = {}
        for r in found:
            table.setdefault(r["class"], {}).setdefault(outcome(r["class"], r), 0)
            table[r["class"]][outcome(r["class"], r)] += 1
        report[name] = {"calls": table, **{k: f"{len(v)} {v}" for k, v in p.items()}}
    written = [r["values"]["written"] for r in rows if r["status"] == "read"]
    content = [r["values"]["content"] for r in rows if r["status"] == "read"]
    core = [r["values"]["core"][0] for r in rows if r["status"] == "read"]
    report["values"] = {"written": f"median {statistics.median(written):g}, max {max(written)}",
                        "content": f"median {statistics.median(content):g}, max {max(content)}",
                        "core only": f"median {statistics.median(core):g}, max {max(core)}",
                        "step 3 ran": f"{sum(bool(r['focus_payload']) for r in rows)}/{len(rows)}"}
    report["dropped by code"] = f"{sum(len(r['dropped']) for r in rows)} in {sum(bool(r['dropped']) for r in rows)} reads"
    report["cost"] = (f"US${sum(r['usd'] for r in rows):.4f}; tokens in/out per item "
                      f"{sum(r['input_tokens'] for r in rows) // len(rows)}/{sum(r['output_tokens'] for r in rows) // len(rows)}")
    labels = HERE / "live" / tag / "a1-labels.json"
    if labels.exists():
        report["A1"] = a1_accuracy(rows, json.loads(labels.read_text()))
    facts = HERE / "live" / tag / "fact-labels.json"
    if facts.exists():
        report["misfills"] = misfills(json.loads(facts.read_text()))
    print(json.dumps(report, indent=1, ensure_ascii=False))
    (HERE / "live" / tag / "score.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")


def facts(tag: str) -> None:
    """Every value the reads wrote, with its words, for the blind fact labeller (written values only: an unwritten
    field cannot be misfilled)."""
    rows = json.loads((HERE / "live" / tag / "dev.json").read_text())["rows"]
    out = []
    for r in rows:
        slim = r["slim"]
        found = [{"what": f"A1 item: {i.get('said', 'workflow_only')}" + (f" = {i['value']}" if i.get("value") else "")
                  + (f" between {i['values']}" if i.get("values") else "")
                  + (f" (outside name: {i['outside_name']})" if i.get("outside_name") else ""),
                  "quote": i["quote"]} for i in slim.get("results") or []]
        found += [{"what": f"A3 data {d['name']}: {d.get('value', 'has')}", "quote": d.get("quote", "")}
                  for d in slim.get("data") or []]
        if slim.get("only_these"):
            found.append({"what": "A3 these are all the data the user has", "quote": slim.get("only_quote", "")})
        if slim.get("run") == "run":
            found.append({"what": "A4 the user asks to run it now", "quote": slim.get("run_quote", "")})
        found += [{"what": f"{f['field']} {f.get('name', '')} = "
                   + (f"unsure between {f['values']}" if f.get("values") else f.get("value", ""))
                   + (f" (workflow {f['workflow']})" if f.get("workflow") else ""), "quote": f.get("quote", "")}
                  for f in slim.get("stated") or []]
        found += [{"what": f"C5 unregistered method: {m}", "quote": m} for m in slim.get("unregistered_methods") or []]
        out.append({"id": r["id"], "prompt": next(i["prompt"] for i in ITEMS if i["id"] == r["id"]),
                    "facts": [{"n": n, **f} for n, f in enumerate(found, 1)]})
    (HERE / "live" / tag / "facts-to-label.json").write_text(json.dumps(out, indent=1, ensure_ascii=False),
                                                             encoding="utf-8")
    print(f"{sum(len(o['facts']) for o in out)} facts in {len(out)} items")


def a1_accuracy(rows: list[dict], labels: dict) -> dict:
    """A1 right: the results the reading's things asked name, as the decision table expands them, equal the
    labeller's (a kind of result counts as its results; purpose, method choice and questions as no result named)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from netzoo_agent_core.judgment_defaults import judgment_defaults
    table = judgment_defaults()
    right, wrong = 0, []
    for r in rows:
        gold = labels.get(r["id"])
        if gold is None or r["status"] != "read":
            continue
        said = set()
        open_ = False
        for item in r["slim"].get("results") or []:
            kind = item.get("said", "workflow_only")
            if kind in ("menu_result", "kind_of_result"):
                said |= set(table.expand(item["value"])) if kind == "kind_of_result" else {item["value"]}
                open_ |= kind == "kind_of_result"
            elif kind == "unsure_between_results":
                said |= {v for value in item.get("values") or [] for v in table.expand(value)}
                open_ = True
            elif kind == "off_menu_result":
                said.add("off_menu")
            elif kind in ("purpose_or_topic", "method_choice", "question_to_us"):
                open_ = True
        expected = set(gold.get("results") or [])
        ok = said == expected and open_ == bool(gold.get("open"))
        right += ok
        if not ok:
            wrong.append({"id": r["id"], "read": sorted(said), "read_open": open_, "label": sorted(expected),
                          "label_open": bool(gold.get("open"))})
    return {"right": f"{right}/{right + len(wrong)}", "wrong": wrong}


def misfills(labels: list[dict]) -> dict:
    total = sum(len(item["labels"]) for item in labels)
    bad = [{"id": item["id"], **entry} for item in labels for entry in item["labels"] if entry["label"] != "supported"]
    by_field: dict[str, int] = {}
    for entry in bad:
        field = entry["what"].split(" ")[0]
        by_field[field] = by_field.get(field, 0) + 1
    return {"values labelled": total, "not supported": len(bad), "by field": by_field, "items": bad}


if __name__ == "__main__":
    command, tag = sys.argv[1], sys.argv[2]
    {"read": read, "score": score, "facts": facts}[command](tag)
