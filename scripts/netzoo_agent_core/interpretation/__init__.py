"""Deterministic task hydration, repair, fallback, and input discovery."""

from . import core
from .core import (
    INPUT_LABELS,
    _best_named_file,
    _candidate_keywords,
    _choose_unambiguous_candidate,
    _is_fatal_exception,
    _lioness_mode_plan,
    _mentions_unspecified_data_directory,
    _needs_lioness_mode_choice,
    _task_path,
    deterministic_router_fallback,
    discover_demo_bundle,
    documentation_library_for_task,
    extract_preference_proposals,
    hydrate_router_decision,
    is_versioned_documentation_request,
    repair_router_decision,
    reusable_episode_inputs,
)

_INTERPRETATION_IMPLEMENTATION_MODULES = (core,)

__all__ = [
    "INPUT_LABELS",
    "_candidate_keywords",
    "_choose_unambiguous_candidate",
    "_task_path",
    "_mentions_unspecified_data_directory",
    "_needs_lioness_mode_choice",
    "is_versioned_documentation_request",
    "documentation_library_for_task",
    "extract_preference_proposals",
    "hydrate_router_decision",
    "_lioness_mode_plan",
    "repair_router_decision",
    "deterministic_router_fallback",
    "_is_fatal_exception",
    "_best_named_file",
    "discover_demo_bundle",
    "reusable_episode_inputs",
]
