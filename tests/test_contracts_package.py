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
    "SemanticDiscriminator",
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


def test_default_task_budget_covers_the_full_semantic_repair_route():
    assert contracts.DEFAULT_TASK_TOKEN_BUDGET == 30_000

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
# 2026-09-10: sample_cluster_assignment now declares its sole canonical
# operation=analyze in the artifact-dependent generation schema. This prevents
# a review patch from carrying the proposed network's infer operation into the
# terminal cohort-clustering result. Embedded schemas change transitively.
# 2026-09-10: tf_activity_matrix is now a first-class artifact so GIRAFFE's TFA
# output can be expressed without overloading optional selection tags. Those tags
# remain optional at both Python and provider boundaries. Contracts embedding
# ArtifactType or RequestedOutcome change transitively.
# The joint GRN/TFA result is now a first-class composite artifact whose support
# is derived from concrete produced-artifact components. This expands the same
# ArtifactType-bearing schemas without changing their transport shape.
# Signed partial regulatory-effect networks are now a first-class subtype, so
# the model can express coefficient direction without relying on optional tags.
# 2026-09-11: WorkflowPolicySpec records conditional required-input groups so
# guidance can state expression_file OR coexpression_file without making both
# sources mandatory.
# 2026-09-14: TaskDecision.matched_actions now uses ActionName rather than the
# narrower RecommendedAction because direct read-only tools (WEB-SEARCH and
# Context7) are valid exact matches but are not scientific workflow
# recommendations.
# 2026-09-22: refresh the six pins that transitively embed already-reviewed
# contract changes: the expanded RequestedOutcome selection-tag description and
# artifact/action vocabulary, WorkflowPlan handoff/recovery fields, and the
# registry-owned WorkflowPolicySpec input_validator. The direct contract tests
# for those fields remain the source of meaning; these hashes detect later drift.
# 2026-09-26: TaskDecision.discovered_inputs records files in a folder routing
# read that validated by content for an input role, reported to the user but
# never used (Log 188). Omitted from dumps while empty; the TaskDecision digest
# is the only schema change.
# 2026-09-30: STRING acquisition adds a direct action to ActionName and a typed
# network kind to TaskDecision. RouterDecision and CapabilityMatch embed ActionName.
SCHEMA_DIGESTS = {
    # 2026-09-27: optional advisory philosophy rationale, quotes, assumptions and capability gap;
    # existing condition recommendations remain valid. Execution fields unchanged.
    # 2026-09-29: optional quoted research hypotheses; no execution authority.
    # 2026-10-05: optional code-owned operation_authorization (requested and
    # forbidden operations read from the request); it can only refuse execution.
    # 2026-10-06 (Log 380): optional code-owned data_facts and applicability; advisory only.
    # 2026-10-06 (Log 383): optional code-owned data_plan (the turn's data-needs plan); reply only.
    "TaskDecision": "21885777b9db5fea1fb3f729cfac9621f04f71da05902a440a3b05089635c333",
    "RouterDecision": "e3d115c92b6ed1ad2adb50bd5a9e2e0fcbb314fead002814b27a2c3badc75ae6",
    "RequestedOutcome": "7ad03175bf93392e5664b574108c104fd569d3c5a8a0d257176bbb9c967bf5aa",
    "OutcomeEvidence": "0b014a1f66f97681cbd4359aa7c00a9e8ed1edaf762b53a9bb70fe40c4662e6f",
    "OutcomeHypothesis": "90cdc308da7a0c3fb3099f7cdd31e8823668e1beb22925d1137df156272dbf9f",
    "CapabilityMatch": "15d1c70f2929d7e220b694d8080934185877dcf21c1ec735c1653029a530638e",
    "WorkflowPlan": "60754a779e0ad46bd409619063be6793cb9c68268fb23fe5bc61d2469777113c",
    "InputEvidence": "a02eac4efb7237a0a54188b6648f36300a35b555574554a2fccd0450bd804cda",
    "ToolExecutionResult": "5dc1715aafa8d1f284c7d7fb42ece1869317ea1af9ee7fd43cf5863360faebbc",
    "ProjectPolicySnapshot": "a9c603b3bad0ef133c74160c7c81a9b9bca96fc35f661fdaac31c13dfc460cd0",
    "UserProfile": "f1a5487412da7e287b7d64e0e37cc6e8d46af0940711af25294624e3f51bf72b",
    # Updated deliberately on 2026-09-10: episodes retain the typed scientific
    # outcome used for semantic memory retrieval.
    "Episode": "90413517536ca2e8fc6c1dfde5d02cc6085d8ccb5179f8fd47524be9e06ac566",
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
            "SemanticDiscriminator",
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
