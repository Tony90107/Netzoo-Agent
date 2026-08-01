#!/usr/bin/env python3
"""Backward-compatible CLI and import facade for the modular NetZoo agent.

Implementation lives in ``netzoo_agent_core``.  Existing commands and imports can
continue to use this file while new code imports the smaller module that owns the
needed behaviour.
"""

from __future__ import annotations

# ruff: noqa: F401 -- this facade intentionally re-exports the historical surface.

import json
import os
import re
import sys
import time
import types

import pandas as pd

from workflow_registry import (
    ACTION_DEFINITIONS,
    CODE_VALIDATION_STEPS,
    LOCAL_EXECUTION_ACTIONS,
    LOCAL_WORKFLOW_ACTIONS,
    PROFILE_PREFERENCE_KEYS,
    REQUIRED_INPUTS,
    RUN_ACTIONS,
    WORKFLOW_MEMORY_METADATA,
    executor_arguments,
    workflow_name as _workflow_name,
)

from netzoo_agent_core import (
    artifact_validation,
    bundles,
    cli,
    command,
    contracts,
    evaluation,
    execution,
    graph,
    interaction,
    interpretation,
    llm,
    memory,
    outcomes,
    path_safety,
    planning,
    policy,
    preparation,
    routing,
    session,
    validation,
)
from netzoo_agent_core.contracts import (
    AIMessage,
    END,
    HumanMessage,
    START,
    StateGraph,
    SystemMessage,
    add_messages,
    tool,
)
from netzoo_agent_core.runtime import MUTABLE_RUNTIME_NAMES, set_runtime_value


_IMPLEMENTATION_MODULES = (
    contracts,
    artifact_validation,
    bundles,
    memory,
    outcomes,
    path_safety,
    command,
    validation,
    preparation,
    execution,
    routing,
    policy,
    interpretation,
    planning,
    evaluation,
    llm,
    graph,
    session,
    interaction,
    cli,
)

_SYMBOL_OWNERS: dict[str, types.ModuleType] = {}
for _module in _IMPLEMENTATION_MODULES:
    for _name in _module.__all__:
        globals()[_name] = getattr(_module, _name)
        _SYMBOL_OWNERS[_name] = _module


@tool
def explain_panda_puma_io(topic: str = "overview") -> str:
    """Explain PANDA/PUMA input and output formats without running a workflow."""
    return f"""
PANDA needs:
- expression file: rows are genes, columns are samples, values are processed gene expression.
- motif file: TF, target gene, weight. Example: MYC<TAB>CCND1<TAB>1
- PPI file: TF1, TF2, weight. Example: MYC<TAB>MAX<TAB>1
- output: TF, Gene, Motif, Force. Force is the PANDA edge score.

PUMA needs everything PANDA needs plus:
- miRNA file: miRNA, target gene, weight. Example: hsa-miR-21<TAB>PTEN<TAB>1
- output: regulator-to-gene network. Regulators can be TFs or miRNAs.

Important preprocessing point:
Raw sequencing reads are not expression data yet. In a real RNA-seq workflow, FASTQ reads usually go through QC, trimming, alignment or pseudoalignment, quantification, gene ID mapping, filtering, and normalization before becoming the expression matrix used by PANDA/PUMA.

Requested topic: {topic}
""".strip()


TOOLS = [explain_panda_puma_io, inspect_netzoo_inputs, run_panda, run_puma]


class _CompatibilityFacade(types.ModuleType):
    """Forward legacy process-wide setting overrides to their owning modules."""

    def __setattr__(self, name: str, value: object) -> None:
        if name in MUTABLE_RUNTIME_NAMES:
            set_runtime_value(name, value)
        elif owner := _SYMBOL_OWNERS.get(name):
            previous = globals().get(name)
            for module in _IMPLEMENTATION_MODULES:
                if vars(module).get(name) is previous:
                    types.ModuleType.__setattr__(module, name, value)
            if vars(owner).get(name) is not value:
                types.ModuleType.__setattr__(owner, name, value)
            super().__setattr__(name, value)
        else:
            super().__setattr__(name, value)


sys.modules[__name__].__class__ = _CompatibilityFacade


if __name__ == "__main__":
    raise SystemExit(cli.main())
