"""Log 416 pre-measure: does the check call fill open_choices, and only when the user leaves a choice open?

Usage (repository root, provider key in the environment, OPENROUTER_CAPABILITY_MODEL set as live):
  python docs/research-log/open-choices-2026-10-12/premeasure416.py <out.json> [repeats] [name ...]

Per request: one check call with this checkout's schema, then build_capability_check; records each
result's status and its open-choice group. No re-read, no second opinion. Every request here is seen
(feasibility eval 2026-10-12) or designed for this pre-measure -- none is held out.
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

# (name, expect, request): expect "open" -- the user leaves a choice about the result open; "none" -- no open choice.
REQUESTS = [
    ("F37", "open", "I want a network for each sample, but I have not decided whether edges should mean TF regulation "
                    "or gene-gene coexpression. What do you need to clarify before choosing a workflow?"),
    ("F39", "open", "Download the human STRING network for me; I have not decided whether it should be functional "
                    "association, physical interactions, or directed regulation."),
    ("F43", "open", "Some regulators seem different between patients. I cannot tell if I mean their activity or their "
                    "network wiring. Help me choose before planning anything."),
    ("D1", "open", "We have expression from 70 kidney biopsies. We have not decided whether we want one network for the "
                   "whole cohort or one network per patient."),
    ("D2", "open", "For my 50 tumors I am torn between a TF activity score per sample and a TF-gene network per sample."),
    ("D3", "open", "Not sure if we need gene-gene co-expression or TF-gene regulation for our 40 samples. Help us choose."),
    ("C1", "none", "We have bulk RNA-seq from 80 tumors and want a network per sample. Should we use LIONESS-PANDA or "
                   "BONOBO?"),
    ("C2", "none", "I want one TF-gene network for 60 liver samples from expression, motifs and PPI."),
    ("C3", "none", "I am not sure whether my expression is log-transformed. I want per-sample co-expression networks "
                   "for 30 samples."),
    ("C4", "none", "We want communities in our bipartite TF-gene network and the core score of each node."),
    ("C5", "none", "Compare TF activity and TF-gene wiring between responders and non-responders; I want both."),
    ("C6", "none", "We have expression and methylation for the same 90 samples. Is a joint network of the two layers or "
                   "a separate network per layer more appropriate?"),
]


def run(job):
    name, expect, task, rep = job
    llm = _own_llm(os.environ["OPENROUTER_CAPABILITY_MODEL"], int(os.environ.get("OPENROUTER_CAPABILITY_MAX_TOKENS", "9000")))
    messages, count = build_capability_check_messages(task)
    schema = proposal_model(count)
    row = {"name": name, "rep": rep, "expect": expect, "task": task}
    try:
        adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
        payload, _raw = semantic_payload(adapter.invoke(messages))
        proposal = schema.model_validate(payload.model_dump() if hasattr(payload, "model_dump") else payload)
    except Exception as error:  # noqa: BLE001
        return {**row, "error": f"{type(error).__name__}: {str(error)[:150]}"}
    check, rejected = build_capability_check(task, proposal)
    row["proposed_choices"] = [[option.quote for option in choice.options]
                               for sentence in (getattr(proposal, f"s{i}") for i in range(1, count + 1))
                               for choice in sentence.open_choices]
    row["results"] = [(r.quote, r.status, [k for k in r.delivered_by], r.choice) for r in check.results()]
    row["context"] = [r.quote for r in check.requirements if r.kind != "result"]
    row["open_choices"] = [[r.quote for r in group] for group in check.open_choices()]
    row["rejected"], row["full_gap"] = rejected, check.full_gap
    return row


def main():
    out = Path(sys.argv[1])
    repeats = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    only = set(sys.argv[3:])
    jobs = [(n, e, t, r) for r in range(1, repeats + 1) for n, e, t in REQUESTS if not only or n in only]
    with ThreadPoolExecutor(4) as pool:
        rows = list(pool.map(run, jobs))
    out.write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    for row in rows:
        fired = bool(row.get("open_choices"))
        mark = "ERR" if "error" in row else ("ok " if fired == (row["expect"] == "open") else "XX ")
        print(mark, row["name"], row["rep"], row.get("open_choices") or row.get("error", ""), "gap" if row.get("full_gap") else "")


if __name__ == "__main__":
    main()
