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


def test_interpretation_package_exports_only_the_existing_surface():
    assert hasattr(interpretation, "__path__")
    assert interpretation.__all__ == PUBLIC_EXPORTS


def test_extraction_and_hydration_modules_are_internal():
    extraction = importlib.import_module("netzoo_agent_core.interpretation.extraction")
    hydration = importlib.import_module("netzoo_agent_core.interpretation.hydration")
    assert extraction.__all__ == []
    assert hydration.__all__ == []


def test_legacy_hydration_patch_reaches_child():
    hydration = importlib.import_module("netzoo_agent_core.interpretation.hydration")
    original = legacy_agent.hydrate_router_decision

    def replacement(raw_decision, task):
        raise AssertionError("hydration patch sentinel")

    try:
        legacy_agent.hydrate_router_decision = replacement
        assert hydration.hydrate_router_decision is replacement
    finally:
        legacy_agent.hydrate_router_decision = original


def test_repair_and_provider_fallback_modules_are_internal():
    repair = importlib.import_module("netzoo_agent_core.interpretation.repair")
    fallback = importlib.import_module(
        "netzoo_agent_core.interpretation.provider_fallback"
    )
    assert repair.__all__ == []
    assert fallback.__all__ == []


@pytest.mark.parametrize(
    ("module_name", "symbol"),
    [
        ("repair", "repair_router_decision"),
        ("provider_fallback", "deterministic_router_fallback"),
    ],
)
def test_legacy_decision_patch_reaches_owner(module_name, symbol):
    owner = importlib.import_module(
        f"netzoo_agent_core.interpretation.{module_name}"
    )
    original = getattr(legacy_agent, symbol)

    def replacement(*args, **kwargs):
        raise AssertionError("decision patch sentinel")

    try:
        setattr(legacy_agent, symbol, replacement)
        assert getattr(owner, symbol) is replacement
    finally:
        setattr(legacy_agent, symbol, original)


def test_discovery_module_is_internal_and_patchable():
    discovery = importlib.import_module("netzoo_agent_core.interpretation.discovery")
    assert discovery.__all__ == []
    original = legacy_agent.discover_demo_bundle

    def replacement(action):
        return None

    try:
        legacy_agent.discover_demo_bundle = replacement
        assert discovery.discover_demo_bundle is replacement
    finally:
        legacy_agent.discover_demo_bundle = original


def test_interpretation_children_are_responsibility_sized():
    maximum_lines = {
        "discovery": 320,
        "extraction": 280,
        "hydration": 140,
        "provider_fallback": 230,
        "repair": 340,
    }
    for module_name, maximum in maximum_lines.items():
        module = importlib.import_module(
            f"netzoo_agent_core.interpretation.{module_name}"
        )
        assert len(inspect.getsource(module).splitlines()) <= maximum, module_name


def test_temporary_interpretation_core_is_removed():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("netzoo_agent_core.interpretation.core")


def test_interpretation_package_uses_final_responsibility_owners():
    owners = {
        "discovery": (
            "_candidate_keywords",
            "_choose_unambiguous_candidate",
            "_best_named_file",
            "discover_demo_bundle",
            "reusable_episode_inputs",
        ),
        "extraction": (
            "INPUT_LABELS",
            "_task_path",
            "_mentions_unspecified_data_directory",
            "_needs_lioness_mode_choice",
            "is_versioned_documentation_request",
            "documentation_library_for_task",
            "extract_preference_proposals",
        ),
        "hydration": ("hydrate_router_decision",),
        "provider_fallback": (
            "deterministic_router_fallback",
            "_is_fatal_exception",
        ),
        "repair": ("_lioness_mode_plan", "repair_router_decision"),
    }
    for module_name, names in owners.items():
        owner = importlib.import_module(
            f"netzoo_agent_core.interpretation.{module_name}"
        )
        for name in names:
            assert getattr(interpretation, name) is getattr(owner, name)


def test_interpretation_child_dependencies_are_acyclic_and_scoped():
    child_names = {
        "discovery",
        "extraction",
        "hydration",
        "provider_fallback",
        "repair",
    }
    dependencies = {}
    for child_name in child_names:
        module = importlib.import_module(
            f"netzoo_agent_core.interpretation.{child_name}"
        )
        tree = ast.parse(inspect.getsource(module))
        dependencies[child_name] = {
            node.module
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            and node.level == 1
            and node.module in child_names
        }
    assert dependencies == {
        "discovery": set(),
        "extraction": set(),
        "hydration": {"extraction"},
        "provider_fallback": set(),
        "repair": {"extraction"},
    }


def test_interpretation_package_does_not_leak_new_helpers():
    assert interpretation.__all__ == PUBLIC_EXPORTS
    for name in (
        "discovery",
        "extraction",
        "hydration",
        "provider_fallback",
        "repair",
    ):
        assert name not in interpretation.__all__
