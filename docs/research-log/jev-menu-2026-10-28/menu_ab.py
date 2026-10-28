"""Gates K1-K3 (ROUND.md): Jev's `result` pick with the old and the new menu on the 175 recorded calls of
jev-guard-2026-10-27/links-offline.json, plus j5 W23 / W45 (reported). Jev calls only.

Usage (env with OPENROUTER_API_KEY): python3 menu_ab.py run -> menu-ab.json ; python3 menu_ab.py score
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from netzoo_agent_core.graph import jev_guard_call as g  # noqa: E402

NEW_MENU = g.result_menu


def old_menu() -> dict[str, str]:
    """The menu before this round (main 7763381d): no produced artifacts."""
    menu = {}
    for path in sorted(g.WORKFLOWS.glob("*.yaml")):
        spec = yaml.safe_load(path.read_text())
        cap = spec.get("output_capability") or {}
        regulators = f"; regulators {', '.join(cap['regulator_types'])}" if cap.get("regulator_types") else ""
        menu[spec["workflow"]] = (f"{spec['description'].strip()} Result: {cap.get('artifact_type')} "
                                  f"({', '.join(cap.get('granularities') or [])}{regulators}).")
    return menu | g.RESULT_NONE


def rows():
    found = json.loads((HERE.parent / "jev-guard-2026-10-27/links-offline.json").read_text())
    items = {i["id"]: i for i in json.loads((HERE.parent / "jev-j5-2026-10-28/j5/items.json").read_text())["single"]}
    extra = [{"set": "j5", "id": key, "request": items[key]["prompt"], "gold": "DO", "workflows": ["GIRAFFE"],
              "kind": kind, "basis": basis} for key, kind, basis in (("W23", "DECLINE", "full_gap"),
                                                                       ("W45", "CLARIFY", "goal_open"))]
    return [{k: v for k, v in row.items() if k != "jev"} for row in found] + extra


def run():
    out = []
    for row in rows():
        for name, menu in (("old", old_menu), ("new", NEW_MENU)):
            g.result_menu = menu
            try:
                row[name] = g.check_result(row["request"])
            except Exception as exc:  # noqa: BLE001 -- recorded
                row[name] = {"error": repr(exc)}
        g.result_menu = NEW_MENU
        out.append(row)
    (HERE / "menu-ab.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    cost = sum(r[n].get("cost", 0) for r in out for n in ("old", "new"))
    print(f"{len(out)} rows, errors {sum('error' in r[n] for r in out for n in ('old', 'new'))}, US${cost:.4f}")


MISREAD = HERE.parents[3] / "netzoo-misread/docs/research-log/misread-detection-2026-10-25"


def gold_workflows() -> dict[tuple[str, str], list[str]]:
    """(set, id) -> the gold's workflows. The rows' own `workflows` are the recorded call's (conditions_data.py), not the
    gold's; the replay set has no per-item gold workflows (kind only)."""
    files = {"j1": HERE.parent / "jev-guard-2026-10-27/j1/items.json", "h9": MISREAD / "h9/items.json",
             "h10": MISREAD / "h10/items.json"}
    return {(name, item["id"]): item.get("workflows") or [] for name, path in files.items()
            for item in json.loads(path.read_text())["single"]}


def pick(found: dict) -> str | None:
    name = found.get("result")
    return name if name not in (None, *g.RESULT_NONE) and found.get("confidence", 0) >= g.THRESHOLD else None


def score():
    out = json.loads((HERE / "menu-ab.json").read_text())
    base = [r for r in out if r["set"] != "j5"]
    clar = [r for r in base if r["kind"] == "CLARIFY"]
    counts = {n: {"gold_clarify": sum(bool(pick(r[n])) for r in clar if r["gold"] == "CLARIFY"),
                  "other": sum(bool(pick(r[n])) for r in clar if r["gold"] != "CLARIFY")} for n in ("old", "new")}
    print(f"CLARIFY calls {len(clar)} (gold CLARIFY {sum(r['gold'] == 'CLARIFY' for r in clar)})")
    print(f"K1 picks on gold CLARIFY: old {counts['old']['gold_clarify']} new {counts['new']['gold_clarify']} -> "
          f"{'PASS' if counts['new']['gold_clarify'] <= counts['old']['gold_clarify'] else 'fail'}")
    print(f"K2 picks on other CLARIFY calls: old {counts['old']['other']} new {counts['new']['other']} -> "
          f"{'PASS' if counts['new']['other'] >= counts['old']['other'] else 'fail'}")
    golds = gold_workflows()
    for r in out:
        r["gold_workflows"] = golds.get((r["set"], r["id"]), r["workflows"] if r["set"] == "j5" else None)
    changed = [r for r in clar if pick(r["old"]) != pick(r["new"])]
    right = [r for r in changed if pick(r["new"]) and pick(r["new"]) in (r["gold_workflows"] or [])]
    wrong = [r for r in changed if pick(r["new"]) and pick(r["new"]) not in (r["gold_workflows"] or [])]
    print(f"K3 CLARIFY picks changed {len(changed)}: new right {len(right)}, new not the gold's {len(wrong)} -> "
          f"{'PASS' if len(wrong) <= len(right) else 'fail'}")
    for r in changed:
        print(f"   {r['set']} {r['id']} gold {r['gold']} {r['gold_workflows']}: {pick(r['old'])} ({r['old'].get('result')} "
              f"{r['old'].get('confidence', 0):.2f}) -> {pick(r['new'])} ({r['new'].get('result')} "
              f"{r['new'].get('confidence', 0):.2f})")
    moves = Counter((r["old"].get("result"), r["new"].get("result")) for r in base
                    if r["old"].get("result") != r["new"].get("result"))
    print("all 175 calls, result moves (old -> new):", dict(moves.most_common()))
    print("all 175 calls, same result:", sum(r["old"].get("result") == r["new"].get("result") for r in base))
    for r in out:
        if r["set"] == "j5":
            print(f"j5 {r['id']} ({r['kind']}): old {r['old'].get('result')} {r['old'].get('confidence', 0):.2f} -> "
                  f"new {r['new'].get('result')} {r['new'].get('confidence', 0):.2f}")


if __name__ == "__main__":
    {"run": run, "score": score}[sys.argv[1]]()
