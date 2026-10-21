"""ROUND-22 sizing ($0): two candidate input rules, each replayed alone over every reading.

A  a co-expression network the user supplies (`input_network: gene_gene`) fits only a workflow whose registry inputs
   take one (`coexpression_file`: PANDA, PUMA, OTTER); M46 fed COBRA's adjusted matrix to LIONESS-PANDA.
B  a result the request names a network-consuming workflow for (CONDOR) when no existing network is given
   (`input_network: none`) or the user's words rule one out, and the request names no workflow that builds one: the
   named workflow cannot run as asked (H27, L48 "run CONDOR directly on the counts").

A2 A, on the checked rows and only for the workflow the request names for the result (method.named).

Usage: python3 size.py A|A2|B OUT.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "stability-round13-2026-10-21"))
import harness  # noqa: E402

harness.replay_full.GOAL_READS.update({d["task"]: d["read"] for d in json.loads(
    (HERE.parent / "goal-read-2026-10-21/reads.json").read_text())["reads"] if d["read"]})


def rule_a():
    from workflow_registry import ACTION_DEFINITIONS
    from netzoo_agent_core.capability_sheet import entry
    from netzoo_agent_core.interpretation import capability_check

    takes = {action for action, d in ACTION_DEFINITIONS.items()
             if any("coexpression" in name for name in (*d.required_inputs, *getattr(d, "optional_inputs", ())))}
    original = capability_check._fitting

    def fitting(keys, item):
        kept = original(keys, item)
        if getattr(item, "input_network", None) == "gene_gene":
            kept = [k for k in kept if entry(k).action in takes]
        return kept

    capability_check._fitting = fitting


def rule_b():
    from workflow_registry import OUTPUT_CAPABILITIES, workflow_name
    from netzoo_agent_core.capability_sheet import entry
    from netzoo_agent_core.interpretation import ruled_out
    from netzoo_agent_core.method_names import workflows_in

    consumers = {action for capability in OUTPUT_CAPABILITIES.values() for action in capability.handoff_targets
                 if action == "run_condor"}
    builders = {workflow_name(a) for a, c in OUTPUT_CAPABILITIES.items() if "run_condor" in c.handoff_targets}
    original = ruled_out.without_ruled_out
    task_of = {}

    def without(check, stated_inputs=frozenset()):
        check = original(check, stated_inputs)
        if check is None:
            return check
        task = task_of.get("task", "")
        rows = []
        for row in check.requirements:
            named = row.method.get("named")
            held = [k for k in row.delivered_by if entry(k).action in consumers and entry(k).workflow == named]
            no_network = row.attrs.get("input_network") in ("none", None) or "network" in check.ruled_out
            if (row.kind == "result" and row.status in ("available", "with_step", "partial") and held and no_network
                    and not set(workflows_in(task)) & builders):
                kept = [k for k in row.delivered_by if k not in held]
                row = row.model_copy(update={"delivered_by": kept, "status": row.status if kept else "not_available",
                                             "limits": [*row.limits, f"{named} needs a regulator-gene network"]})
            rows.append(row)
        return check.model_copy(update={"requirements": rows})

    ruled_out.without_ruled_out = without
    original_replay = harness.replay_full.replay

    def replay(folder, task, payload, reread, found):
        task_of["task"] = task
        return original_replay(folder, task, payload, reread, found)

    harness.replay_full.replay = replay


def rule_a2():
    """A on the checked rows: a credit to the named workflow is removed when it takes no co-expression input."""
    from workflow_registry import ACTION_DEFINITIONS
    from netzoo_agent_core.capability_sheet import entry
    from netzoo_agent_core.interpretation import ruled_out

    takes = {action for action, d in ACTION_DEFINITIONS.items()
             if any("coexpression" in name for name in (*d.required_inputs, *getattr(d, "optional_inputs", ())))}
    original = ruled_out.without_ruled_out

    def without(check, stated_inputs=frozenset()):
        check = original(check, stated_inputs)
        if check is None:
            return check
        rows = []
        for row in check.requirements:
            named = row.method.get("named")
            held = [k for k in row.delivered_by if entry(k).workflow == named and entry(k).action not in takes]
            if row.kind == "result" and row.attrs.get("input_network") == "gene_gene" and held:
                kept = [k for k in row.delivered_by if k not in held]
                row = row.model_copy(update={"delivered_by": kept, "status": row.status if kept else "not_available",
                                             "limits": [*row.limits, f"{named} takes no co-expression input"]})
            rows.append(row)
        return check.model_copy(update={"requirements": rows})

    ruled_out.without_ruled_out = without


if __name__ == "__main__":
    {"A": rule_a, "A2": rule_a2, "B": rule_b}[sys.argv[1]]()
    harness.run(sys.argv[2])
