from __future__ import annotations

import importlib
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as legacy_agent  # noqa: E402
import netzoo_agent_core.routing as routing  # noqa: E402


HISTORICAL_EXPORTS = [
    "MIN_TOOL_CONFIDENCE",
    "FILE_DISCOVERY_MAX_DEPTH",
    "FILE_DISCOVERY_MAX_VISITED",
    "FILE_DISCOVERY_MAX_RESULTS",
    "CONTEXT7_URL",
    "CONTEXT7_MAX_CHARS",
    "WEBSEARCH_URL",
    "WEBSEARCH_MAX_CHARS",
    "CONTEXT7_LIBRARY_ALIASES",
    "UNSUPPORTED_DELIVERABLE_PATTERNS",
    "WORKFLOW_INFORMATION_PATTERNS",
    "is_workflow_information_request",
    "infer_goal_capabilities",
    "infer_advisory_capabilities",
    "inferred_execution_action",
    "has_direct_execution_intent",
    "validate_task_text",
    "normalize_context7_library",
    "enforce_capability_gate",
    "match_requested_outcome",
    "guidance_actions_for",
    "_extract_named_path",
    "_score_candidate_file",
    "_find_candidate_files",
    "_default_lioness_outputs",
    "_default_network_output",
    "_tool_text",
    "_exception_text",
    "_find_mcp_tool",
    "_extract_context7_library_id",
    "_query_context7_async",
    "query_context7_docs",
    "_web_search_async",
    "query_web_search",
    "query_web_search_first_url",
    "execute_selected_tool",
    "_expected_artifacts",
    "_diagnostic_messages",
    "structure_tool_result",
]


def test_routing_is_responsibility_oriented_package():
    assert hasattr(routing, "__path__")
    for module_name in (
        "capability",
        "discovery",
        "retrieval",
        "dispatch",
        "error_adapters",
        "outcome_matching",
        "results",
    ):
        importlib.import_module(f"netzoo_agent_core.routing.{module_name}")


def test_historical_routing_surface_is_preserved():
    assert routing.__all__ == HISTORICAL_EXPORTS
    for name in HISTORICAL_EXPORTS:
        assert hasattr(routing, name), name


def test_legacy_facade_uses_routing_package_exports():
    for name in HISTORICAL_EXPORTS:
        assert getattr(legacy_agent, name) is getattr(routing, name)


def test_legacy_patch_reaches_retrieval_and_dispatch_children():
    retrieval = importlib.import_module("netzoo_agent_core.routing.retrieval")
    dispatch = importlib.import_module("netzoo_agent_core.routing.dispatch")
    original = legacy_agent.query_web_search

    def replacement(query: str) -> str:
        return (
            "Websearch MCP result (external, untrusted reference content):\n\n"
            '{"results": [{"url": "https://example.test/result"}]}'
        )

    try:
        legacy_agent.query_web_search = replacement
        assert retrieval.query_web_search is replacement
        assert dispatch.query_web_search is replacement
        assert (
            legacy_agent.query_web_search_first_url("genes")
            == "https://example.test/result"
        )
    finally:
        legacy_agent.query_web_search = original


def test_runtime_overrides_reach_routing_children(tmp_path: Path):
    discovery = importlib.import_module("netzoo_agent_core.routing.discovery")
    results = importlib.import_module("netzoo_agent_core.routing.results")
    original_project_root = legacy_agent.PROJECT_ROOT
    original_log_root = legacy_agent.TOOL_LOG_ROOT
    try:
        legacy_agent.PROJECT_ROOT = tmp_path
        legacy_agent.TOOL_LOG_ROOT = tmp_path / "logs"
        assert discovery.PROJECT_ROOT == tmp_path
        assert results.TOOL_LOG_ROOT == tmp_path / "logs"
    finally:
        legacy_agent.PROJECT_ROOT = original_project_root
        legacy_agent.TOOL_LOG_ROOT = original_log_root
