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
    "TaskDecision": "cd2f00d1ca791c6b69fe945cdc3dc705adc468873c724260fecebfa087d3a534",
    "RouterDecision": "d5fe95d5550882392ab0382e1be6b90d2eee874fe0225f4ef924ac72b1153515",
    "RequestedOutcome": "f6e9cd7e92293b7c5e0e67f71fdf7f339e75325b5b91aab2599b05665d920d72",
    "OutcomeEvidence": "c36e790b7027e674beb4783d87c5288c7127f278243707a21321d1772960f522",
    "OutcomeHypothesis": "4350adbc7c60be4a1acb4c87cc009dead65d713f1337ef9e5a642fcf95e9bde3",
    "CapabilityMatch": "6d5d7ba3a9613641512a6a37c026437fa795db550fc98d4f7fcb73ef2dc2afad",
    "WorkflowPlan": "29287f95a1dde44319d645a86e89d3992c0d5cb53ddfa95d70d30167d5ae1263",
    "InputEvidence": "a02eac4efb7237a0a54188b6648f36300a35b555574554a2fccd0450bd804cda",
    "ToolExecutionResult": "5dc1715aafa8d1f284c7d7fb42ece1869317ea1af9ee7fd43cf5863360faebbc",
    "ProjectPolicySnapshot": "d06252a7558e6f628444af238715a4a878cea73ec65893251caeab279ce35653",
    "UserProfile": "f1a5487412da7e287b7d64e0e37cc6e8d46af0940711af25294624e3f51bf72b",
    "Episode": "12ea309e79b9fcfc32cd4030ad5aed570eecac04a5414fdfe061dc569a82e70e",
}


def test_contracts_is_a_package_with_final_owners():
    assert hasattr(contracts, "__path__")
    for name in ("decisions", "outcomes", "planning", "results", "policy", "memory", "state"):
        importlib.import_module(f"netzoo_agent_core.contracts.{name}")


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
        "planning": (
            "InputBundleOption",
            "InputEvidence",
            "WorkflowStep",
            "WorkflowPlan",
        ),
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
    for module_name in ("decisions", "outcomes", "planning", "results", "policy", "memory", "state"):
        module = importlib.import_module(f"netzoo_agent_core.contracts.{module_name}")
        tree = ast.parse(inspect.getsource(module))
        imports = [
            node.module or ""
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
        ]
        assert not any(name.startswith("langgraph") for name in imports), module_name
