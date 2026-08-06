from __future__ import annotations

import ast
import importlib
import inspect
import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as legacy_agent  # noqa: E402
import netzoo_agent_core.interpretation as interpretation  # noqa: E402


PUBLIC_EXPORTS = [
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

PUBLIC_SIGNATURES = {
    "_candidate_keywords": "(action: 'str', field_name: 'str') -> 'tuple[str, ...]'",
    "_choose_unambiguous_candidate": "(candidates: 'list[str]', keywords: 'tuple[str, ...]', nearby: 'Path') -> 'tuple[str | None, str]'",
    "_task_path": "(task: 'str', field_name: 'str') -> 'str | None'",
    "_mentions_unspecified_data_directory": "(task: 'str') -> 'bool'",
    "_needs_lioness_mode_choice": "(task: 'str') -> 'bool'",
    "is_versioned_documentation_request": "(task: 'str') -> 'bool'",
    "documentation_library_for_task": "(task: 'str') -> 'str | None'",
    "extract_preference_proposals": "(task: 'str') -> 'list[PreferenceProposal]'",
    "hydrate_router_decision": "(raw_decision: 'RouterDecision | TaskDecision | dict', task: 'str') -> 'TaskDecision'",
    "_lioness_mode_plan": "(decision: 'TaskDecision', task: 'str', *, memory_notes: 'list[str]', policy_hash: 'str | None') -> 'WorkflowPlan'",
    "repair_router_decision": "(raw_decision: 'TaskDecision', task: 'str') -> 'TaskDecision'",
    "deterministic_router_fallback": "(task: 'str', error: 'BaseException | None' = None) -> 'TaskDecision'",
    "_is_fatal_exception": "(error: 'BaseException') -> 'bool'",
    "_best_named_file": "(directory: 'Path', keywords: 'tuple[str, ...]') -> 'Path | None'",
    "discover_demo_bundle": "(action: 'str') -> 'tuple[dict[str, str], str] | None'",
    "reusable_episode_inputs": "(action: 'str', episodes: 'list[Episode]') -> 'tuple[dict[str, str], str] | None'",
}


def test_interpretation_public_surface_is_characterized():
    assert interpretation.__all__ == PUBLIC_EXPORTS
    for name, signature in PUBLIC_SIGNATURES.items():
        assert str(inspect.signature(getattr(interpretation, name))) == signature
    for name in PUBLIC_EXPORTS:
        assert getattr(legacy_agent, name) is getattr(interpretation, name)


@pytest.mark.parametrize(
    "error",
    [KeyboardInterrupt(), SystemExit(), GeneratorExit()],
)
def test_fatal_provider_exceptions_are_characterized(error):
    assert interpretation._is_fatal_exception(error) is True


def test_ordinary_provider_error_is_not_fatal():
    assert interpretation._is_fatal_exception(TimeoutError()) is False
