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
    compatibility,
    contracts,
    evaluation,
    execution,
    framework_compat,
    graph,
    interaction,
    interpretation,
    llm,
    memory,
    outcomes,
    path_safety,
    planning,
    policy,
    presentation,
    pricing,
    preparation,
    routing,
    session,
    settings,
    trace_contracts,
    trace_redaction,
    trace_store,
    tracing,
    validation,
)
from netzoo_agent_core.routing import (
    capability as routing_capability,
    discovery as routing_discovery,
    dispatch as routing_dispatch,
    results as routing_results,
    retrieval as routing_retrieval,
)
from netzoo_agent_core.planning import assembly, builder, context, evidence, rendering
from netzoo_agent_core.cli import _CLI_IMPLEMENTATION_MODULES
from netzoo_agent_core.contracts import _CONTRACT_IMPLEMENTATION_MODULES
from netzoo_agent_core.graph import _GRAPH_IMPLEMENTATION_MODULES
from netzoo_agent_core.interpretation import _INTERPRETATION_IMPLEMENTATION_MODULES
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
    settings,
    framework_compat,
    presentation,
    *_CONTRACT_IMPLEMENTATION_MODULES,
    artifact_validation,
    bundles,
    memory,
    outcomes,
    path_safety,
    command,
    compatibility,
    validation,
    preparation,
    execution,
    routing,
    routing_capability,
    routing_discovery,
    routing_retrieval,
    routing_dispatch,
    routing_results,
    policy,
    pricing,
    interpretation, *_INTERPRETATION_IMPLEMENTATION_MODULES,
    planning, assembly, builder, context, evidence, rendering,
    evaluation,
    llm,
    graph, *_GRAPH_IMPLEMENTATION_MODULES,
    session,
    trace_contracts,
    trace_redaction,
    trace_store,
    tracing,
    interaction,
    cli,
    *_CLI_IMPLEMENTATION_MODULES,
)
_SYMBOL_OWNERS: dict[str, types.ModuleType] = {}
for _module in _IMPLEMENTATION_MODULES:
    for _name in _module.__all__:
        globals()[_name] = getattr(_module, _name)
        _SYMBOL_OWNERS[_name] = _module
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
