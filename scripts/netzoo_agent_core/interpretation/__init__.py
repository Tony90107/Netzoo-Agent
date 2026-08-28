"""Deterministic task hydration, repair, fallback, and input discovery."""

from . import (
    assembly,
    bonobo_demo,
    concept_answers,
    discovery,
    extraction,
    hydration,
    outcome_validation,
    provider_fallback,
    repair,
)
from .discovery import (
    _best_named_file,
    _candidate_keywords,
    _choose_unambiguous_candidate,
    discover_demo_bundle,
    reusable_episode_inputs,
    _unlabeled_input_bindings,  # noqa: F401 -- internal compatibility facade
)
from .assembly import (  # noqa: F401 -- direct internal import without public widening
    assemble_task_decision,
)
from .extraction import (
    INPUT_LABELS,
    _mentions_unspecified_data_directory,
    _needs_lioness_mode_choice,
    _task_path,
    documentation_library_for_task,
    extract_preference_proposals,
    is_versioned_documentation_request,
)
from .hydration import hydrate_router_decision
from .provider_fallback import deterministic_router_fallback, _is_fatal_exception
from .repair import _lioness_mode_plan, repair_router_decision

_INTERPRETATION_IMPLEMENTATION_MODULES = (
    assembly,
    bonobo_demo,
    discovery,
    extraction,
    hydration,
    outcome_validation,
    provider_fallback,
    repair,
    concept_answers,
)

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
