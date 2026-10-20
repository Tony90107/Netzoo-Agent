"""ROUND-02 offline replay (collab/ROUND-02-PLAN.md, section 7): the saved veto readings judged by the code before
ROUND-02 (`c32ba444`, unpacked by `git archive` into a temporary folder) and by this worktree's code. $0: no model is
called -- each reading is used exactly as it was recorded.

Readings: h4 (`closed-menu-hybrid-2026-10-19/h4/live/h4/veto.json`, 19 live DOs, H2) and the h1-h3 debug read
(`closed-menu-hybrid-2026-10-19/h1-debug.json`, 44 live DOs, H1). All four sets are seen: this is debug and regression,
never acceptance. Readings from before ROUND-02 carry no evidence (legacy): ownership is unknown and is not filled in.
The contract check's payloads were not saved, so clauses it copied (C1, C4, C6, D4) are not replayed; a veto that
came only from one is listed as not replayable.

    python3 -I replay.py      # writes manifest.json, replay.json; prints the summary
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = HERE.parent
ROOT = LOG.parents[1]
BEFORE = "c32ba444"
SOURCES = {
    "h4": ("closed-menu-hybrid-2026-10-19/h4/live/h4/veto.json", "closed-menu-hybrid-2026-10-19/h4/items.json"),
    "h1-h3": ("closed-menu-hybrid-2026-10-19/h1-debug.json", {
        "h1": "closed-menu-phase1b-2026-10-18/heldout/items.json",
        "h2": "closed-menu-options-first-2026-10-18/h2/items.json",
        "h3": "closed-menu-slim-2026-10-19/h3/items.json"}),
}
REPLAYABLE = {"B5", "B6", "C2", "C3", "C5", "C7", "C8", "B4"}  # code-verified sources; the rest needed the check payload

RUNNER = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
from netzoo_agent_core.contracts.slim_reading import SlimReading
from netzoo_agent_core.contracts.core_decision import CoreDecision
from netzoo_agent_core.interpretation import contract_veto as cv
rows = json.load(sys.stdin)
out = {}
for row in rows:
    slim = SlimReading.model_validate(row["slim"])
    verdict = cv.contract_veto(slim, row["workflows"], row["prompt"])
    core = cv.vetoed_core(CoreDecision(kind="DO", basis="results_given", workflows=row["workflows"]), verdict)
    entry = {"kind": core.kind,
             "violations": [[v.workflow, v.kind, v.reason, v.user_quote] for vs in verdict.violations.values() for v in vs],
             "questions": [[q.dimension, list(q.values), q.quote, getattr(q, "evidence", "")] for q in verdict.questions],
             "question_lines": [f.question for f in core.facts],
             "set_aside": getattr(verdict, "set_aside", []), "dropped_questions": getattr(verdict, "dropped_questions", [])}
    if hasattr(sys.modules.get("netzoo_agent_core.interpretation.veto_evidence") or object, "veto_ledger"):
        from netzoo_agent_core.interpretation.veto_evidence import veto_ledger
        entry["ledger"] = veto_ledger(row["workflows"], "checked", slim, (), verdict, verdict.set_aside)
    out[row["key"]] = entry
print(json.dumps(out))
'''


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def rows() -> list[dict]:
    found = []
    path, items_path = SOURCES["h4"]
    items = {x["id"]: x for x in json.loads((LOG / items_path).read_text())["items"]}
    for row in json.loads((LOG / path).read_text())["rows"]:
        found.append({"key": f"h4:{row['id']}", "set": "h4", "id": row["id"], "class": row["class"],
                      "workflows": row["core_before"]["workflows"], "prompt": items[row["id"]]["prompt"],
                      "slim": row["slim"], "recorded": {"vetoes": row["vetoes"], "questions": row["questions"]}})
    path, sets = SOURCES["h1-h3"]
    items = {name: {x["id"]: x for x in json.loads((LOG / p).read_text())["items"]} for name, p in sets.items()}
    for row in json.loads((LOG / path).read_text())["rows"]:
        if row.get("status") != "checked" or not row.get("slim"):
            continue
        found.append({"key": f"{row['set']}:{row['id']}", "set": row["set"], "id": row["id"], "class": row["class"],
                      "workflows": row["live"]["workflows"] if isinstance(row.get("live"), dict) else row["workflows_after"],
                      "prompt": items[row["set"]][row["id"]]["prompt"], "slim": row["slim"],
                      "recorded": {"vetoes": row["vetoes"], "questions": row["questions"]}})
    return found


def judge(scripts: Path, batch: list[dict]) -> dict:
    payload = json.dumps([{k: r[k] for k in ("key", "workflows", "prompt", "slim")} for r in batch])
    done = subprocess.run([sys.executable, "-I", "-c", RUNNER, str(scripts)], input=payload, capture_output=True,
                          text=True, check=True, cwd=str(scripts.parent))
    return json.loads(done.stdout)


def _cell_read(ledger: dict, cell: str) -> list:
    for row in ledger.get("cells", []):
        if row["cell"] == cell or (cell.startswith("data:") and row["cell"].startswith("data:")
                                   and cell.split(":", 1)[1] in row["cell"].split(":", 1)[1].split("|")):
            return row["values"]
    return []


def score(gold: dict, entry: dict, slim: dict) -> dict:
    """Per item: value recall, doubt recall, ownership (legacy: unknown), violations and questions vs gold."""
    stated = {f["name"]: f for f in slim.get("stated", [])}
    data = {d["name"]: d for d in slim.get("data", [])}
    values = doubts = doubts_read = values_read = 0
    for cell in gold["cells"]:
        name = cell["cell"]
        if name.startswith("setting:"):
            control = name.split(".", 1)[1]
            got = [f for f in slim.get("stated", []) if f.get("name") in (control, f"setting:{control}")]
            read = [str(f.get("value", "")) for f in got]
        elif name.startswith("data:"):
            d = data.get(name.split(":", 1)[1])
            read = [d["value"]] if d else []
        else:
            f = stated.get(name) or ({"values": slim_condition(slim, name)} if slim_condition(slim, name) else None)
            read = (f.get("values") or [f.get("value")]) if f else []
        if cell.get("doubt"):
            doubts += 1
            doubts_read += sorted(map(str, read)) == sorted(cell["values"])
        else:
            values += 1
            values_read += str(cell["value"]) in [str(v) for v in read]
    kinds = sorted(v[1] for v in entry["violations"])
    asked = sorted({q[0] for q in entry["questions"]})
    return {"values": [values_read, values], "doubts": [doubts_read, doubts],
            "ownership": "legacy_unknown" if not any(f.get("evidence") for f in slim.get("stated", [])) else "read",
            "violations_right": kinds == sorted(gold["violations"]),
            "unsupported_vetoes": [k for k in kinds if k not in gold["violations"]],
            "missed_vetoes": [k for k in gold["violations"] if k not in kinds],
            "unsupported_questions": [d for d in asked if d not in gold["questions"]],
            "missed_questions": [d for d in gold["questions"] if d not in asked]}


def slim_condition(slim: dict, name: str) -> list:
    found = [f for f in slim.get("stated", []) if f.get("name") == name]
    return (found[0].get("values") or [found[0].get("value")]) if found else []


def main() -> None:
    batch = rows()
    with tempfile.TemporaryDirectory() as tmp:
        archive = subprocess.run(["git", "archive", BEFORE, "scripts", "workflows", "AGENTS.md"], cwd=ROOT,
                                 capture_output=True, check=True).stdout
        subprocess.run(["tar", "-x", "-C", tmp], input=archive, check=True)
        before = judge(Path(tmp) / "scripts", batch)
    after = judge(ROOT / "scripts", batch)
    gold = json.loads((HERE / "gold-cells.json").read_text())["items"]
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "scripts", "workflows", "tests"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    results, changed = [], []
    for row in batch:
        b, a = before[row["key"]], after[row["key"]]
        record = {"key": row["key"], "class": row["class"], "workflows": row["workflows"], "before": b, "after": a,
                  "not_replayable": [v for v in row["recorded"]["vetoes"] if v.get("kind") not in REPLAYABLE]}
        if row["set"] == "h4" and row["id"] in gold:
            record["score_before"] = score(gold[row["id"]], b, row["slim"])
            record["score_after"] = score(gold[row["id"]], a, row["slim"])
        if (b["kind"], b["violations"], b["questions"]) != (a["kind"], a["violations"], a["questions"]):
            changed.append(row["key"])
        results.append(record)
    summary = {"rows": len(results), "changed": changed,
               "kind_changes": {r["key"]: [r["before"]["kind"], r["after"]["kind"]] for r in results
                                if r["before"]["kind"] != r["after"]["kind"]},
               "set_aside": {r["key"]: r["after"]["set_aside"] for r in results if r["after"]["set_aside"]},
               "dropped_questions": {r["key"]: r["after"]["dropped_questions"] for r in results
                                     if r["after"]["dropped_questions"]},
               "not_replayable": {r["key"]: r["not_replayable"] for r in results if r["not_replayable"]}}
    scored = [r for r in results if "score_after" in r]
    for when in ("before", "after"):
        s = [r[f"score_{when}"] for r in scored]
        summary[f"h4_{when}"] = {
            "value_recall": [sum(x["values"][0] for x in s), sum(x["values"][1] for x in s)],
            "doubt_recall": [sum(x["doubts"][0] for x in s), sum(x["doubts"][1] for x in s)],
            "violations_right": sum(x["violations_right"] for x in s),
            "unsupported_vetoes": {r["key"]: r[f"score_{when}"]["unsupported_vetoes"] for r in scored
                                   if r[f"score_{when}"]["unsupported_vetoes"]},
            "missed_vetoes": {r["key"]: r[f"score_{when}"]["missed_vetoes"] for r in scored
                              if r[f"score_{when}"]["missed_vetoes"]},
            "unsupported_questions": {r["key"]: r[f"score_{when}"]["unsupported_questions"] for r in scored
                                      if r[f"score_{when}"]["unsupported_questions"]},
            "missed_questions": {r["key"]: r[f"score_{when}"]["missed_questions"] for r in scored
                                 if r[f"score_{when}"]["missed_questions"]}}
    manifest = {"before": BEFORE, "after_head": head, "after_uncommitted": bool(dirty),
                "inputs": {str(p): _sha(LOG / p) for p in (SOURCES["h4"][0], SOURCES["h4"][1], SOURCES["h1-h3"][0],
                                                          *SOURCES["h1-h3"][1].values())},
                "gold": _sha(HERE / "gold-cells.json"), "model_calls": 0}
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    (HERE / "replay.json").write_text(json.dumps({"summary": summary, "rows": results}, indent=1, sort_keys=True,
                                                 ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
