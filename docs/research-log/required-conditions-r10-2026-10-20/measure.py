"""ROUND-10 step 0 (collab/ROUND-10-PLAN.md): where the unconfirmed quantity cells of DO calls would go. No model calls.

For every recorded reading (rebuilt by request-facts-round03 `replay.py checks` with this checkout) whose core call
(count-scope-r09 `replay_core.py cores`, this checkout) is DO: each credited result row, each credited workflow, each
quantity condition `workflow_conditions` holds -- the sample minimum (samples), the output size cap and COBRA's
genes > samples relation (samples and features), SAMBAR's kmax <= samples (samples). A cell is unconfirmed when a
quantity it needs was neither read for the row (`method`) nor given as candidates (count alternatives, unknown
sample counts with choices, unread side-by-side candidates in context). Each DO turn with unconfirmed cells falls in
one case of plan section 2.3: `file` (a run is asked for, an input file is named, every unconfirmed cell is one the
workflow's input_checks settle from files), `ask` (a run is asked for otherwise) or `state` (no run asked for).

`--revised` (after reviewing the 18 `ask` turns): a count read for the result anywhere in the shared record counts as
read, and a run sends every unconfirmed quantity cell to the input preflight, which enforces each minimum and cap
from the files (data/dragon.py, giraffe.py, cobra.py too, though their YAML input_checks omit the line).

Usage: python3 measure.py CHECKS.json CORES.json OUT.json [--revised]
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parents[2]
MAIN = WT.parents[1] / "netzoo_agent"
sys.path.insert(0, str(WT / "scripts"))

from netzoo_agent_core.capability_sheet import entry  # noqa: E402
from netzoo_agent_core.contract_text import check_limit, file_checkable  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck  # noqa: E402
from netzoo_agent_core.interpretation.input_bindings import request_input_bindings  # noqa: E402
from netzoo_agent_core.interpretation.needed_facts import check_unknowns  # noqa: E402
from netzoo_agent_core.interpretation.request_spans import _locate, scope_applies  # noqa: E402
from netzoo_agent_core.interpretation.sample_coverage import _candidate_runs  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.settings import PROJECT_ROOT  # noqa: E402
from netzoo_agent_core.workflow_conditions import conditions_for  # noqa: E402

sys.path.insert(0, str(WT / "docs/research-log/count-scope-r09-2026-10-20"))
from replay_core import _gold  # noqa: E402

POLICY = ProjectPolicyLoader(PROJECT_ROOT).load()
REVISED = "--revised" in sys.argv
LIMIT = {"min_samples": "min_samples", "max_values": "max_values", "relation": "relation:", "kmax": "setting:kmax"}


def _file_limits(action: str) -> set[str]:
    spec = POLICY.workflows.get(action)
    return {check_limit(item) for item in (spec.input_checks if spec else ()) if file_checkable(item)}


def _cells(workflow_action: str):
    """(cell, needs) for each quantity condition of the workflow."""
    limits = conditions_for(workflow_action)
    if limits is None:
        return []
    cells = []
    if limits.min_samples is not None:
        cells.append(("min_samples", {"samples"}))
    if limits.max_values is not None:
        cells.append(("max_values", {"samples", "features"}))
    if limits.relation is not None:
        cells.append(("relation", {"samples", "features"}))
    if "kmax" in limits.settings and limits.workflow == "SAMBAR":
        cells.append(("kmax", {"samples"}))
    return cells


def _context_candidates(check, task) -> bool:
    for row in check.requirements:
        if row.kind == "context" and (where := _locate(task, row.quote)) and _candidate_runs(task[where[0]:where[1]]):
            return True
    return False


def main(checks_path, cores_path, out):
    checks, cores = json.loads(Path(checks_path).read_text()), json.loads(Path(cores_path).read_text())
    gold, core_items = _gold()
    rows, tally = [], Counter()
    for key, core in cores.items():
        if core["kind"] != "DO":
            continue
        tally["DO turns"] += 1
        row = checks[key]
        folder = next((p for root in (WT, MAIN) if (p := root / row["where"]).joinpath("session.json").exists()), None)
        decision = TaskDecision.model_validate(json.loads((folder / "session.json").read_text())["plan"]["decision"])
        check = CapabilityCheck.model_validate({k: v for k, v in row["check"].items() if k in CapabilityCheck.model_fields})
        task = row["task"]
        run = decision.execution_requested or decision.action.startswith("run_")
        bindings = request_input_bindings(task)
        files = bool(bindings.values or bindings.named_paths)
        alternatives = {item["of"] for item in check.count_alternatives}
        side = _context_candidates(check, task)
        unconfirmed, credited = [], False
        for result in check.results():
            if result.status not in ("available", "with_step", "partial"):
                continue
            method = result.method
            have = set()
            if method.get("samples") is not None or "samples" in alternatives or side or any(
                    about == "sample_count" for about, _said, _domain in check_unknowns(check, result.quote)):
                have.add("samples")
            if method.get("features") is not None or "features" in alternatives:
                have.add("features")
            if REVISED:  # a count read anywhere for this result (the shared record), not only on its method
                for fact in check.facts:
                    if fact.state == "stated" and not fact.scope_unverified and scope_applies(result.quote,
                                                                                              fact.applies_to):
                        have.add({"sample_count": "samples", "feature_count": "features"}.get(fact.property, ""))
            for key_ in result.delivered_by:
                found = entry(key_)
                if not found or not found.action:
                    continue
                credited = True
                for cell, needs in _cells(found.action):
                    if needs - have:
                        unconfirmed.append({"workflow": found.workflow, "action": found.action, "cell": cell,
                                            "missing": sorted(needs - have),
                                            "file_checkable": any(limit.startswith(LIMIT[cell])
                                                                  for limit in _file_limits(found.action))})
        if not credited:
            tally["DO turns with no credited result (routed only; not measured)"] += 1
            continue
        if not unconfirmed:
            tally["DO turns with every quantity cell confirmed"] += 1
            continue
        unique = list({(u["workflow"], u["cell"]): u for u in unconfirmed}.values())
        if not run:
            case = "state"
        elif REVISED:  # every quantity minimum and cap is enforced by the input preflight (data/*.py)
            case = "file"
        elif files and all(u["file_checkable"] for u in unique):
            case = "file"
        else:
            case = "ask"
        tally[f"case {case}"] += 1
        label = gold.get(core["session"])
        if label is None and (m := re.match(r"cj-[^-]+-(C\d+)-1", core["session"])):
            label = core_items.get(m.group(1))
        rows.append({"key": key, "where": row["where"], "case": case, "gold": label, "run": run, "files": files,
                     "cells": unique, "task": task})
    Path(out).write_text(json.dumps({"tally": tally, "rows": rows}, indent=1, ensure_ascii=False))
    print(json.dumps(tally, indent=1))
    by = Counter((r["case"], r["gold"]) for r in rows)
    print("case x gold:", dict(sorted(by.items(), key=str)))


if __name__ == "__main__":
    main(*sys.argv[1:4])
