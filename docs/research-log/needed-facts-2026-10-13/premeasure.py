"""Verdict layer step 2 pre-measure: does the check call read unknown facts, and does code ask only deciding ones?

Usage (repository root, provider key in the environment, OPENROUTER_CAPABILITY_MODEL set as live):
  python docs/research-log/needed-facts-2026-10-13/premeasure.py <out.json>

One check call per request (the free capability model), then build_capability_check. Requests: heldout416b UNKNOWN_INPUT
items and feasibility eval F41/F46/F49 (expect a waiting result), heldout416b DECIDED items (expect none). All seen.
"""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.graph.capability_check_call import _own_llm, build_capability_check_messages  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402
from netzoo_agent_core.interpretation.semantic_repair import semantic_payload  # noqa: E402

BLIND = {item["id"]: item for item in json.loads(
    (ROOT / "docs/research-log/open-choices-2026-10-12/heldout416b.json").read_text())["items"]}
EVAL = {item["id"]: item for item in json.loads(
    (ROOT.parent / "outputs/feasibility-eval-2026-10-12/prompts.json").read_text())}
JOBS = ([(key, "wait", BLIND[key]["prompt"]) for key in BLIND if BLIND[key]["family"] == "UNKNOWN_INPUT"]
        + [(key, "wait", EVAL[key]["prompt"]) for key in ("F41", "F46", "F49")]
        + [(key, "none", BLIND[key]["prompt"]) for key in BLIND if BLIND[key]["family"] == "DECIDED"])


def run(job):
    name, expect, task = job
    llm = _own_llm(os.environ["OPENROUTER_CAPABILITY_MODEL"], int(os.environ.get("OPENROUTER_CAPABILITY_MAX_TOKENS", "9000")))
    messages, count = build_capability_check_messages(task)
    schema = proposal_model(count)
    row = {"name": name, "expect": expect, "task": task}
    try:
        adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
        payload, _raw = semantic_payload(adapter.invoke(messages))
        proposal = schema.model_validate(payload.model_dump() if hasattr(payload, "model_dump") else payload)
    except Exception as error:  # noqa: BLE001
        return {**row, "error": f"{type(error).__name__}: {str(error)[:150]}"}
    check, _ = build_capability_check(task, proposal)
    row["read"] = [[fact.about, fact.quote] for fact in proposal.conditions.unknown_facts]
    row["waiting"] = [[item.quote, item.depends_on, item.outcomes] for item in check.needed_facts()]
    row["results"] = [[item.quote, item.status, item.delivered_by] for item in check.results()]
    row["full_gap"] = check.full_gap
    return row


def main():
    with ThreadPoolExecutor(4) as pool:
        rows = list(pool.map(run, JOBS))
    Path(sys.argv[1]).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    for row in rows:
        waits = bool(row.get("waiting"))
        mark = "ERR" if "error" in row else "ok " if waits == (row["expect"] == "wait") else "XX "
        print(mark, row["name"], row["expect"], "| read", row.get("read"), "| waits on",
              [w[1] for w in row.get("waiting", [])], "| gap" if row.get("full_gap") else "", row.get("error", ""))


if __name__ == "__main__":
    main()
