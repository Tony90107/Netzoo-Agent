from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent_core.contracts as contracts  # noqa: E402
from netzoo_agent_core.contracts import WorkspaceResourceInventory  # noqa: E402
from workflow_registry import (  # noqa: E402
    ACTION_DEFINITIONS,
    DISCOVERABLE_ACTIONS,
    READ_ONLY_ACTIONS,
)


HISTORICAL_EXPORTS = [
    "EXECUTE_TOOLS",
    "TRACE_ENABLED",
    "VERBOSE_OUTPUT",
    "TRANSIENT_TRACE",
    "TOOL_TIMEOUT_SECONDS",
    "_TRANSIENT_TRACE_ACTIVE",
    "_TRANSIENT_TRACE_UPDATED_AT",
    "TRANSIENT_TRACE_MIN_SECONDS",
    "USER_VISIBLE_OUTPUT_LANGUAGE",
    "LIONESS_MODE_QUESTION",
    "PROJECT_ROOT",
    "SESSION_ROOT",
    "TOOL_LOG_ROOT",
    "TRACE_ROOT",
    "MEMORY_ROOT",
    "PROFILE_ROOT",
    "EPISODE_ROOT",
    "TOOL_RAW_MAX_CHARS",
    "DEFAULT_RETENTION_DAYS",
    "DEFAULT_SESSION_HARD_RETENTION_DAYS",
    "DEFAULT_ROUTER_MODEL",
    "DEFAULT_ROUTER_MAX_TOKENS",
    "DEFAULT_RESPONSE_MAX_TOKENS",
    "DEFAULT_TASK_TOKEN_BUDGET",
    "DEFAULT_LLM_TIMEOUT_SECONDS",
    "DEFAULT_LLM_MAX_RETRIES",
    "DEFAULT_TOOL_TIMEOUT_SECONDS",
    "MAX_RECOVERY_ATTEMPTS",
    "ROUTER_CONTEXT_MAX_CHARS",
    "DEFAULT_EPISODE_RETENTION_DAYS",
    "DEFAULT_EPISODE_DRY_RUN_RETENTION_DAYS",
    "DEFAULT_EPISODE_FAILED_RETENTION_DAYS",
    "DEFAULT_EPISODE_MAX_COUNT",
    "DEFAULT_EPISODE_MAX_BYTES",
    "_ui_text",
    "output_language_policy",
    "_clear_transient_trace",
    "_trace_line",
    "_trace",
    "AgentState",
    "AgentTurnInterrupted",
    "ClarificationInputError",
    "PreferenceProposal",
    "RouterDecision",
    "TaskDecision",
    "LLMUsage",
    "InputEvidence",
    "WorkspaceDiscoveryScope",
    "ValidatedResourceBundle",
    "PartialResourceCandidate",
    "WorkspaceResourceInventory",
    "RequestedOutcome",
    "OutcomeEvidence",
    "OutcomeHypothesis",
    "EvidenceDimension",
    "CapabilityMatch",
    "CapabilityMatchStatus",
    "WorkflowStep",
    "WorkflowPlan",
    "EvaluationResult",
    "PlanRubricItem",
    "PlanEvaluationResult",
    "NextTurnPrompt",
    "CLI_FOLLOW_UP_STARTERS",
    "strip_cli_owned_follow_up_question",
    "ArtifactValidationResult",
    "ToolExecutionResult",
    "AgentsPolicyHeader",
    "WorkflowPolicySpec",
    "WorkflowOutputCapabilitySpec",
    "ProjectPolicySnapshot",
    "UserProfile",
    "Episode",
    "INPUT_ROLE_FIELDS",
    "OUTPUT_ROLE_FIELDS",
    "PARAMETER_FIELDS",
    "_display_path",
    "_is_demo_request",
]

SCHEMA_DIGESTS = {
    "TaskDecision": "b8b73f8bb43bee01610aee99692e3840d1691da044e543b5ea21635a0f0145e0",
    "RouterDecision": "86f8adf02a15c752cb7e6b3b346e6fcd803384476746523a1779da79b4fcb191",
    "RequestedOutcome": "9958b10da7ee3c95fbec8af78da4d7d2e30f6d7df6c0191ffefba8d080287d36",
    "OutcomeEvidence": "d6415b130ca1a6e4a02c5369f34b03e75ffdb87bf3aa7af1787a6491e12b5362",
    "OutcomeHypothesis": "68d87cd2290862732e753dec11b7e5c7e7bed8c3c3f83af9b93317421e71fe9b",
    "CapabilityMatch": "c5952a563a94fa5b5e9cfc9d1298bfc130e603f283afb61c7b89472b2ef121dd",
    "WorkflowPlan": "9a57762cf8ffc4cd8e611b1d9907ef89c9d5ee1b82280ef5c2e76133b9ecfc4b",
    "InputEvidence": "0582cce8d5b06debc2e6af06b2f2c2fff9fc0d062b00ac41863442a3a11f0a8a",
    "ToolExecutionResult": "0416c4d5b2844e7ad40b4a50b832af51a99b4cd45ac4fff245fb22f337d6e02a",
    "ProjectPolicySnapshot": "a8502c6d87e9108ae033d26584b2d7d2ca58724c3fbfd0771a6ff6149686457b",
    "UserProfile": "f1a5487412da7e287b7d64e0e37cc6e8d46af0940711af25294624e3f51bf72b",
    "Episode": "12ea309e79b9fcfc32cd4030ad5aed570eecac04a5414fdfe061dc569a82e70e",
}


def test_contracts_is_a_package_with_final_owners():
    assert hasattr(contracts, "__path__")
    for name in (
        "decisions",
        "outcomes",
        "planning",
        "results",
        "policy",
        "memory",
        "resources",
        "state",
    ):
        importlib.import_module(f"netzoo_agent_core.contracts.{name}")


def test_workspace_discovery_is_a_registered_read_only_action():
    definition = ACTION_DEFINITIONS["discover_workspace_resources"]
    assert definition.read_only is True
    assert definition.required_inputs == ("workspace_root",)
    assert definition.executor_fields == (
        "workspace_root", "resource_subpath", "resource_actions"
    )
    assert "discover_workspace_resources" in READ_ONLY_ACTIONS


def test_discoverable_workflows_declare_complete_specs():
    assert DISCOVERABLE_ACTIONS
    for action in DISCOVERABLE_ACTIONS:
        spec = ACTION_DEFINITIONS[action].discovery
        assert spec is not None
        assert spec.input_roles
        assert set(spec.input_roles) == set(spec.filename_hints)
        assert spec.validator_ids


def test_inventory_contract_orders_typed_result_groups():
    inventory = WorkspaceResourceInventory(
        scope_root=".",
        visited_file_count=2,
        validated_bundles=[],
        partial_candidates=[],
    )
    assert inventory.truncated is False
    assert inventory.rejected_summary == {}


def test_contract_facade_exports_exact_historical_surface():
    assert contracts.__all__ == HISTORICAL_EXPORTS
    for name in HISTORICAL_EXPORTS:
        assert hasattr(contracts, name), name


def test_models_have_one_owner_and_preserve_identity():
    owners = {
        "decisions": ("PreferenceProposal", "RouterDecision", "TaskDecision"),
        "outcomes": (
            "RequestedOutcome",
            "OutcomeEvidence",
            "OutcomeHypothesis",
            "EvidenceDimension",
            "CapabilityMatch",
            "CapabilityMatchStatus",
        ),
        "planning": ("InputEvidence", "WorkflowStep", "WorkflowPlan"),
        "results": (
            "EvaluationResult",
            "PlanRubricItem",
            "PlanEvaluationResult",
            "ArtifactValidationResult",
            "ToolExecutionResult",
        ),
        "policy": (
            "AgentsPolicyHeader",
            "WorkflowPolicySpec",
            "WorkflowOutputCapabilitySpec",
            "ProjectPolicySnapshot",
        ),
        "memory": ("UserProfile", "Episode"),
        "resources": (
            "WorkspaceDiscoveryScope",
            "ValidatedResourceBundle",
            "PartialResourceCandidate",
            "WorkspaceResourceInventory",
        ),
        "state": (
            "AgentState",
            "AgentTurnInterrupted",
            "ClarificationInputError",
            "LLMUsage",
            "NextTurnPrompt",
        ),
    }
    for module_name, names in owners.items():
        owner = importlib.import_module(f"netzoo_agent_core.contracts.{module_name}")
        for name in names:
            assert getattr(contracts, name) is getattr(owner, name)


def test_contract_model_schemas_are_unchanged():
    for name, expected in SCHEMA_DIGESTS.items():
        payload = json.dumps(
            getattr(contracts, name).model_json_schema(),
            sort_keys=True,
            separators=(",", ":"),
        )
        assert hashlib.sha256(payload.encode()).hexdigest() == expected, name


def test_framework_and_presentation_names_have_single_owners():
    framework = importlib.import_module("netzoo_agent_core.framework_compat")
    presentation = importlib.import_module("netzoo_agent_core.presentation")
    settings = importlib.import_module("netzoo_agent_core.settings")
    assert contracts.AIMessage is framework.AIMessage
    assert contracts.tool is framework.tool
    assert contracts._trace is presentation._trace
    assert contracts._ui_text is presentation._ui_text
    assert contracts.PROJECT_ROOT is settings.PROJECT_ROOT


def test_contract_children_do_not_import_langgraph_directly():
    for module_name in (
        "decisions",
        "outcomes",
        "planning",
        "results",
        "policy",
        "memory",
        "resources",
        "state",
    ):
        module = importlib.import_module(f"netzoo_agent_core.contracts.{module_name}")
        tree = ast.parse(inspect.getsource(module))
        imports = [
            node.module or ""
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
        ]
        assert not any(name.startswith("langgraph") for name in imports), module_name
