"""ROUND-10 step 0, second half (2026-10-21): where the unconfirmed input-data and settings cells of DO calls go.
No model calls, no code changes. Same corpus and method as `required-conditions-r10-2026-10-20/measure.py`.

For every recorded reading (rebuilt with this checkout by request-facts-round03 `replay.py checks`) whose core call
(count-scope-r09 `replay_core.py cores`) is DO, each credited result, each credited workflow:

Input presence -- each required input that is not an output (`ACTION_DEFINITIONS`): `bound` (the request names a file
for that role), `typed` (a typed reading says the user has it: the routing reading's input artifacts, `only_inputs`,
the result's omics layers or existing network), else `unconfirmed`. Unconfirmed: a run asked for -> `planner` (the
Planner requires the file before any run, as today); otherwise -> `state`. `said?` marks, for measurement only, an
unconfirmed motif/PPI/miRNA/design input whose usual words appear in the request (an estimate of "said but untyped").

Data properties -- the typed conditions the sheet applies (`_fitting`): data_unit (every workflow), mutation_origin
(somatic-mutation input), value_type and samples_matched (multi-omic continuous input), mirna_driver (miRNA
regulators), input_network (CONDOR). `stated` (a value is read), `doubt` (the reading wrote an unknown about it), else
`unstated`. Unstated: file-checkable (samples_matched: the DRAGON preflight compares sample IDs) with a run -> `file`;
otherwise the contract's usual case is assumed -> `state`.

Settings -- each wired control: `stated` with a usable value; `unresolved` (named without a usable value, or a value
`setting_unresolved` cannot settle) -> a run is held (ROUND-06), otherwise `state`; `candidates` (the setting's words
hold two or more side-by-side numbers) -> `ask` when the candidates differ under `setting_issue`, else `state`;
`must_declare` (BONOBO log_transformed / centered: no usable default) unstated -> `file` with a run (the preflight
refuses an undeclared run), else `state`; every other unstated control takes its default (`default`), and SAMBAR's
default kmax 4 is checked against a stated sample count below 4 (`default_conflict`).

Gold: the blind gold class of the session (strictness audit h1-h4, core-judgment items) and, for gold ASK items, the
kind of the deciding fact (`GOLD_FACT`, my reading of each item's gold_fact / deciding_fact).

Usage: python3 measure.py CHECKS.json CORES.json OUT.json
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
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck  # noqa: E402
from netzoo_agent_core.interpretation.count_words import candidate_runs  # noqa: E402
from netzoo_agent_core.interpretation.input_bindings import request_input_bindings  # noqa: E402
from netzoo_agent_core.interpretation.request_spans import _locate  # noqa: E402
from netzoo_agent_core.settings import OUTPUT_ROLE_FIELDS  # noqa: E402
from netzoo_agent_core.workflow_conditions import (  # noqa: E402
    StatedSetting, conditions_for, setting_issue, setting_unresolved)
from workflow_registry import ACTION_DEFINITIONS  # noqa: E402

GOLD_FACT = {
    **dict.fromkeys("H15 H29 H36 H38 H47 J07 J14 J22 J27 J48 L11 L18 L39 L40 L43 M01 M03 M09 M38 C45".split(),
                    "quantity"),
    **dict.fromkeys("H13 H23 H25 H30 J34 J36 J39 L05 L07 L14 L22 M06 M22 M26 M36 M39 C06 C20 C21 C39 C42 C43 C44 "
                    "C48 C50 C56".split(), "data_property"),
    **dict.fromkeys("J21 J37 L03 M44".split(), "setting"),
    **dict.fromkeys("H09 H39 H41 J09 J19 L12 L23 M30 M35 C11 C31 C34 C36".split(), "which_result"),
}
KIND = {"do": "DO", "dont": "DECLINE", "ask": "ASK", "vague": "CLARIFY"}
SAID = {"motif_file": r"motif", "ppi_file": r"\bPPI\b|protein[- ]protein|STRING", "mirna_file": r"miRNA",
        "design_file": r"design|covariate"}  # measurement-only estimate, never used by the agent
MUST_DECLARE = {"run_bonobo": ("log_transformed", "centered")}


def _gold():
    audit = json.loads((WT / "docs/research-log/strictness-audit-2026-10-20/audit.json").read_text())["items"]
    by_session = {item["trace"]["session"]: (key, KIND[item["class"]]) for key, item in audit.items()}
    items = json.loads((WT / "docs/research-log/core-judgment-2026-10-15/items.json").read_text())["items"]
    items = {i["id"]: i for i in items} if isinstance(items, list) else items
    return by_session, {key: KIND[item["class"]] for key, item in items.items()}


def _label(session, by_session, core_items):
    if session in by_session:
        return by_session[session]
    if m := re.match(r"cj-[^-]+-(C\d+)-1", session):
        return m.group(1), core_items.get(m.group(1))
    return None, None


def _typed_inputs(decision, check, result) -> set[str]:
    have = set(check.only_inputs or [])
    artifacts = set(decision.guidance_input_artifacts)
    for hypothesis in decision.outcome_hypotheses:
        artifacts.update(hypothesis.outcome.input_artifacts)
    if "expression_matrix" in artifacts:
        have.add("expression_file")
    if "mutation_matrix" in artifacts:
        have.add("mutation_file")
    layers = result.attrs.get("omics_layers") or 0
    if layers >= 1:
        have.update({"omics_layer_1", "expression_file"} if layers == 1 else {"omics_layer_1", "omics_layer_2"})
    if result.attrs.get("input_network") == "regulator_gene":
        have.add("network_file")
    kinds = {"motif_prior": "motif_file", "ppi": "ppi_file", "mirna_list": "mirna_file", "covariates": "design_file",
             "expression": "expression_file", "mutations": "mutation_file", "network": "network_file",
             "second_omics": "omics_layer_2"}
    return have | {kinds[k] for k in check.only_inputs or [] if k in kinds}


def _properties(action, result):
    definition = ACTION_DEFINITIONS.get(action)
    modalities = definition.output_capability.accepted_input_modalities if definition.output_capability else ()
    found = [("data_unit", False)]
    if "somatic_mutation" in modalities:
        found.append(("mutation_origin", False))
    if "multi_omic_continuous" in modalities:
        found += [("value_type", False), ("samples_matched", True)]
    if action in ("run_puma", "run_lioness_puma"):
        found.append(("mirna_driver", False))
    if action == "run_condor":
        found.append(("input_network", False))
    return found


def _doubts(check, quote: str) -> set[str]:
    return {about for about, said in (tuple(item) for item in check.unknowns)
            if not check.unknown_scopes.get(said) or quote in check.unknown_scopes.get(said, [])} | set()


def main(checks_path, cores_path, out):
    checks, cores = json.loads(Path(checks_path).read_text()), json.loads(Path(cores_path).read_text())
    by_session, core_items = _gold()
    tally, cells, rows = Counter(), Counter(), []
    for key, core in cores.items():
        if core["kind"] != "DO":
            continue
        row = checks[key]
        folder = next((p for root in (WT, MAIN) if (p := root / row["where"]).joinpath("session.json").exists()), None)
        decision = TaskDecision.model_validate(json.loads((folder / "session.json").read_text())["plan"]["decision"])
        check = CapabilityCheck.model_validate({k: v for k, v in row["check"].items() if k in CapabilityCheck.model_fields})
        task = row["task"]
        run = decision.execution_requested or decision.action.startswith("run_")
        bindings = request_input_bindings(task)
        bound = set(bindings.values)
        files = bool(bindings.values or bindings.named_paths)
        item_id, gold = _label(core["session"], by_session, core_items)
        tally["DO turns"] += 1
        found, credited = [], False
        for result in check.results():
            if result.status not in ("available", "with_step", "partial"):
                continue
            typed = _typed_inputs(decision, check, result)
            doubts = _doubts(check, result.quote)
            settings = {item["name"]: item for item in result.method.get("settings", [])}
            samples = result.method.get("samples")
            for action in dict.fromkeys(entry(k).action for k in result.delivered_by if entry(k) and entry(k).action):
                definition = ACTION_DEFINITIONS.get(action)
                if definition is None:
                    continue
                credited = True
                workflow = definition.workflow
                for name in definition.required_inputs:
                    if name in OUTPUT_ROLE_FIELDS:
                        continue
                    state = "bound" if name in bound else "typed" if name in typed else "unconfirmed"
                    case = None if state != "unconfirmed" else ("planner" if run else "state")
                    said = bool(state == "unconfirmed" and name in SAID and re.search(SAID[name], task, re.I))
                    found.append({"class": "input", "workflow": workflow, "cell": name, "state": state,
                                  "case": case, "said?": said})
                for name, checkable in _properties(action, result):
                    value = result.attrs.get(name, "not_stated")
                    state = ("doubt" if name in doubts else
                             "stated" if value not in ("not_stated", None, "none") else "unstated")
                    case = None if state == "stated" else "ask" if state == "doubt" else (
                        "file" if checkable and run and files else "state")
                    found.append({"class": "property", "workflow": workflow, "cell": name, "state": state,
                                  "case": case})
                limits = conditions_for(action)
                if limits is None:
                    continue
                for control, limit in limits.settings.items():
                    if not limit.wired:
                        continue
                    given = settings.get(f"{workflow}.{control}")
                    if given is not None:
                        words = given.get("value") or ""
                        runs = candidate_runs(f"{words} {given.get('quote') or ''}")
                        stated = StatedSetting(name=given["name"], quote=given.get("quote") or "", value=words)
                        if runs:
                            values = sorted(runs[0][0])
                            outcomes = {setting_issue(limits, StatedSetting(name=stated.name, quote=stated.quote,
                                                                            value=f"{v:g}")) is None for v in values}
                            state, case = "candidates", "ask" if len(outcomes) > 1 else "state"
                        elif not words.strip() and limit.control_type != "boolean" or setting_unresolved(limits, stated):
                            state, case = "unresolved", "held" if run else "state"
                        else:
                            state, case = "stated", None
                    elif control in MUST_DECLARE.get(action, ()):
                        state, case = "must_declare", "file" if run else "state"
                    elif (action == "run_sambar" and control == "kmax" and samples is not None and samples < 4
                          and "SAMBAR.cluster" not in settings):
                        state, case = "default_conflict", "ask" if run else "state"
                    else:
                        state, case = "default", None
                    found.append({"class": "setting", "workflow": workflow, "cell": control, "state": state,
                                  "case": case})
        if not credited:
            tally["DO turns with no credited result (routed only; not measured)"] += 1
            continue
        unique = list({(c["class"], c["workflow"], c["cell"]): c for c in found}.values())
        for c in unique:
            cells[(c["class"], c["state"], c["case"])] += 1
        turn_cases = {(c["class"], c["case"]) for c in unique if c["case"]}
        for case in turn_cases:
            tally[f"turns with {case[0]} -> {case[1]}"] += 1
        rows.append({"key": key, "where": row["where"], "item": item_id, "gold": gold,
                     "gold_fact": GOLD_FACT.get(item_id or ""), "run": run, "files": files, "task": task,
                     "cases": sorted(f"{a}:{b}" for a, b in turn_cases),
                     "cells": [c for c in unique if c["case"]]})
    gold_do = Counter((r["gold"], r["gold_fact"]) for r in rows if r["gold"])
    Path(out).write_text(json.dumps({"tally": tally, "cells": {" / ".join(map(str, k)): v for k, v in cells.items()},
                                     "rows": rows}, indent=1, ensure_ascii=False))
    print(json.dumps(tally, indent=1))
    print("cells (class / state / case):")
    for k, v in sorted(cells.items(), key=lambda kv: (kv[0][0], -kv[1])):
        print(f"  {k[0]:8} {k[1]:16} {str(k[2]):8} {v}")
    print("DO turns by gold class / gold fact kind:", dict(sorted(gold_do.items(), key=str)))


if __name__ == "__main__":
    main(*sys.argv[1:4])
