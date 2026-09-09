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

# Updated deliberately on 2026-09-05: input_artifacts now names the closed
# artifact_type vocabulary and declares that its items are plain strings, after a
# live run recorded an object at input_artifacts[0]. Field meaning is unchanged.
# 2026-09-05: MatchBasis gained assumed_outcome, so a hypothesis kept advisory by
# its assumptions can be reported as registry guidance instead of a question.
# 2026-09-06: CapabilityMatch.hypothesis_actions maxItems 6 -> 12. That field is
# built by the matcher from the registry, never from model output, and a live run
# aborted because a wholly unresolved outcome ties across all twelve registered
# capabilities. Only that one bound changed. See Log 42.
# 2026-09-06: TaskDecision.hypothesis_actions maxItems 6 -> 12, the same
# registry-derived bound, now imported from one place. `assembly` copies
# CapabilityMatch.hypothesis_actions straight into this field, so widening only
# the producer left the abort intact one contract downstream and cost a second
# full-corpus round. Router output must not populate this field. See Log 53.
# 2026-09-06: community_assignment declares granularities={aggregate}, so its
# anyOf branch narrows from {aggregate, sample_specific, not_applicable, unknown}
# to {aggregate, unknown}. Only that one branch changed; no field was added,
# removed or renamed. See docs/research-log/sambar-agent-routing.md Log 31.
# 2026-09-08: OutcomeEvidence gained an anyOf pair -- an `explicit` entry must
# carry text_span, an `inferred` one need not. The rule existed only in prompt
# prose while the schema said the field was optional and defaulted to null, so
# the contract kept inviting the one shape `_grounded_span` was certain to
# reject: 185 of 188 entries in the largest issue family, 79% of them costing
# the whole interpretation. OutcomeHypothesis, TaskDecision and RouterDecision
# change only because they embed it; RequestedOutcome and CapabilityMatch are
# untouched, which is what confines the change to the evidence entry. See Log 92.
# 2026-09-08: MatchBasis gained unverified_evidence, the basis carried by a
# reading kept although one of its quotes could not be located in the request.
# It is the only basis that describes trust in the reading rather than fit to a
# capability, and invoke_router holds anything carrying it below exact and away
# from execution. Nothing else in these contracts changed. See Log 94.
# Changed deliberately on 2026-09-09 for `named_methods` (Log 128/129): the six
# below all carry the new outcome field, its `named_method` evidence dimension,
# or the `named_method` match basis. The pin exists so a schema the provider sees
# cannot move by accident; moving it is a decision, and this is the record of one.
SCHEMA_DIGESTS = {
    "TaskDecision": "44248ddce6ecb6c8bc9af0feb8ec7a068c4dd12be77f6a80878288d40229f75f",
    "RouterDecision": "877624117b7401dbd58347026b27b867802f5b1c897096eee1f39a2633489bae",
    "RequestedOutcome": "49e3f0998191a19dc427101a9d065542deddf8acc7a4cf68a43332957fc82efd",
    "OutcomeEvidence": "c6ee1732f03bfbe5ee381c20ae9be7f490ce07e288cd3af8b83ac82864a73c16",
    "OutcomeHypothesis": "a97e4047f229671d466dab184dbe65d62ade05d37d4ba6aa3289dc4945a0f055",
    "CapabilityMatch": "931318bcb26b92199d20472a91ce1222ec6068b4139aebac43ebecd7d0231087",
    "WorkflowPlan": "29287f95a1dde44319d645a86e89d3992c0d5cb53ddfa95d70d30167d5ae1263",
    "InputEvidence": "a02eac4efb7237a0a54188b6648f36300a35b555574554a2fccd0450bd804cda",
    "ToolExecutionResult": "5dc1715aafa8d1f284c7d7fb42ece1869317ea1af9ee7fd43cf5863360faebbc",
    "ProjectPolicySnapshot": "7874d426766e6f00bc969f1a53e810e3a112b8317dc58fb2f68979a9cdc6b6e7",
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
