"""Core decision spec, phase 4b (section 12.3): inputs the user says they do not have.

Round p0-p3 C18 ("Run CONDOR directly on expr_kidney_fibrosis.tsv ... I don't have any motif or PPI files, just this
expression table") was offered CONDOR through PANDA -> CONDOR in 3 of 4 rounds: CONDOR needs a regulator-gene network,
and every registered route to one needs a motif prior the user ruled out. `route_available` is the one rule: the
check's credits (`without_ruled_out`) and the two-step routes (`hypothesis_routes`) both ask it.

What a workflow needs is the registry's own `required_inputs`; a ruled-out input is fatal only when no registered
tool or workflow can provide it from what the user still has.
"""

from __future__ import annotations

from workflow_registry import ACTION_DEFINITIONS, OUTPUT_CAPABILITIES, workflow_name

from ..capability_sheet import entry

__all__ = ["INPUT_KIND", "route_available", "without_ruled_out"]

INPUT_KIND = {
    "motif_file": "motif_prior", "ppi_file": "ppi", "mirna_file": "mirna_list", "design_file": "covariates",
    "omics_layer_2": "second_omics", "mutation_file": "mutations", "network_file": "network",
    "expression_file": "expression",
}
_LABEL = {
    "motif_prior": "a TF motif prior", "ppi": "a protein-interaction network", "mirna_list": "a miRNA list",
    "covariates": "a covariate table", "second_omics": "a second omics data type", "mutations": "somatic mutations",
    "network": "a regulator-gene network", "expression": "expression data",
}
_TOOLS = {"ppi": "STRING download"}
"""A registered tool that provides the input (`download_string` writes a PPI network)."""


def _producers(kind: str, consumer: str) -> list[str]:
    """Registered workflows that hand this input to the consumer (PANDA, PUMA, OTTER -> CONDOR's network)."""
    if kind != "network":
        return []
    return [action for action, capability in OUTPUT_CAPABILITIES.items() if consumer in capability.handoff_targets]


def route_available(action: str, ruled_out: dict[str, str], lacking: frozenset[str] = frozenset(),
                    depth: int = 0) -> str | None:
    """Why the workflow cannot run on what the user has, or None when it can.

    `ruled_out`: input kind -> the user's words saying they do not have it. `lacking`: kinds the request reads as
    absent without ruling them out (a result computed from no existing network); either must be provided by a
    registered tool, or by a registered workflow that can itself run (one handoff, never a guessed chain).
    """
    definition = ACTION_DEFINITIONS.get(action)
    if definition is None:
        return None
    grouped = {name for group in definition.required_input_groups for name in group}
    needed = [INPUT_KIND[name] for name in definition.required_inputs if name in INPUT_KIND and name not in grouped]
    for kind in dict.fromkeys(needed):
        if kind not in ruled_out and kind not in lacking:
            continue
        if kind in _TOOLS:
            continue
        producers = [producer for producer in _producers(kind, action)
                     if depth == 0 and route_available(producer, ruled_out, frozenset(), depth + 1) is None]
        if producers:
            continue
        name = definition.workflow
        if kind in ruled_out:
            return (f'You said you do not have {_LABEL[kind]} ("{ruled_out[kind]}"); {name} needs it and no registered '
                    "workflow or tool provides it")
        blocked = sorted({workflow_name(producer) for producer in _producers(kind, action)})
        reasons = sorted({route_available(producer, ruled_out, frozenset(), depth + 1) or "" for producer in
                          _producers(kind, action)} - {""})
        return (f"{name} needs {_LABEL[kind]}; every registered route to one ({', '.join(blocked)}) needs an input "
                f"you do not have" + (f": {reasons[0][0].lower()}{reasons[0][1:]}" if reasons else ""))
    return None


_NETWORKS = frozenset({"regulatory_network", "coexpression_network"})


def without_ruled_out(check, stated_inputs: frozenset[str] = frozenset()):
    """The check with every credit the user's ruled-out inputs make impossible taken off, with its reason.

    A network is absent when the row reads no existing network, or when the routing reading's stated inputs are known
    and hold none (smoke S1: "I only have expr_liver.tsv" typed the CONDOR ask's input_network as regulator_gene, the
    kind CONDOR takes, not one the user has).
    """
    if check is None or not check.ruled_out:
        return check
    no_network = bool(stated_inputs) and not stated_inputs & _NETWORKS
    from .capability_check import _full_gap

    rows = []
    for row in check.requirements:
        if row.kind != "result" or row.status not in ("available", "with_step", "partial", "needs_fact"):
            rows.append(row)
            continue
        lacking = (frozenset({"network"}) if no_network or row.attrs.get("input_network") in ("none", None)
                   else frozenset())
        kept, limits = [], []
        for key in row.delivered_by:
            try:
                action = entry(key).action
            except KeyError:
                action = None
            reason = route_available(action, check.ruled_out, lacking) if action else None
            (limits if reason else kept).append(reason or key)
        if limits:
            row = row.model_copy(update={"delivered_by": kept, "limits": [*row.limits, *dict.fromkeys(limits)],
                                         "status": row.status if kept else "not_available"})
        rows.append(row)
    results = [row for row in rows if row.kind == "result"]
    return check.model_copy(update={"requirements": rows, "full_gap": _full_gap(results, check.unchecked)})
