"""Stable typed contracts and compatibility exports for the NetZoo harness."""

from . import decisions, interaction, memory, outcomes, planning, policy, results, state
from ..framework_compat import (  # noqa: F401 -- historical facade attributes
    AIMessage, END, HumanMessage, START, StateGraph, SystemMessage, add_messages, tool,
)
from ..presentation import (
    CLI_FOLLOW_UP_STARTERS,
    _TRANSIENT_TRACE_ACTIVE,
    _TRANSIENT_TRACE_UPDATED_AT,
    _clear_transient_trace,
    _display_path,
    _is_demo_request,
    _trace,
    _trace_line,
    _ui_text,
    output_language_policy,
    strip_cli_owned_follow_up_question,
)
from ..settings import (
    DEFAULT_EPISODE_DRY_RUN_RETENTION_DAYS,
    DEFAULT_EPISODE_FAILED_RETENTION_DAYS,
    DEFAULT_EPISODE_MAX_BYTES,
    DEFAULT_EPISODE_MAX_COUNT,
    DEFAULT_EPISODE_RETENTION_DAYS,
    DEFAULT_LLM_MAX_RETRIES,
    DEFAULT_LLM_TIMEOUT_SECONDS,
    DEFAULT_RESPONSE_MAX_TOKENS,
    DEFAULT_RETENTION_DAYS,
    DEFAULT_ROUTER_MAX_TOKENS,
    DEFAULT_ROUTER_MODEL,
    DEFAULT_SESSION_HARD_RETENTION_DAYS,
    DEFAULT_TASK_TOKEN_BUDGET,
    DEFAULT_TOOL_TIMEOUT_SECONDS,
    EPISODE_ROOT,
    EXECUTE_TOOLS,
    INPUT_ROLE_FIELDS,
    LIONESS_MODE_QUESTION,
    MAX_RECOVERY_ATTEMPTS,
    MEMORY_ROOT,
    OUTPUT_ROLE_FIELDS,
    PARAMETER_FIELDS,
    PROFILE_ROOT,
    PROJECT_ROOT,
    ROUTER_CONTEXT_MAX_CHARS,
    SESSION_ROOT,
    TOOL_LOG_ROOT,
    TOOL_RAW_MAX_CHARS,
    TOOL_TIMEOUT_SECONDS,
    TRACE_ENABLED,
    TRACE_ROOT,
    TRANSIENT_TRACE,
    TRANSIENT_TRACE_MIN_SECONDS,
    USER_VISIBLE_OUTPUT_LANGUAGE,
    VERBOSE_OUTPUT,
)
from .decisions import PreferenceProposal, RouterDecision, TaskDecision
from .interaction import (  # noqa: F401 -- direct imports without widening __all__
    ContextualReplyResolution,
    FollowUpContext,
    ReplyIntent,
    ReplyIntentDecision,
    WorkflowConversationFact,
)
from .memory import Episode, UserProfile
from .outcomes import (
    CapabilityMatch,
    CapabilityMatchStatus,
    EvidenceDimension,
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
)
from .planning import InputBundleOption  # noqa: F401 -- typed internal plan detail
from .planning import InputEvidence, WorkflowPlan, WorkflowStep
from .policy import (
    AgentsPolicyHeader,
    ProjectPolicySnapshot,
    WorkflowOutputCapabilitySpec,
    WorkflowPolicySpec,
)
from .results import (
    ArtifactValidationResult,
    EvaluationResult,
    PlanEvaluationResult,
    PlanRubricItem,
    ToolExecutionResult,
)
from .state import (
    AgentState,
    AgentTurnInterrupted,
    ClarificationInputError,
    LLMUsage,
    NextTurnPrompt,
)

_CONTRACT_IMPLEMENTATION_MODULES = (
    decisions,
    interaction,
    outcomes,
    planning,
    results,
    policy,
    memory,
    state,
)

__all__ = [
    "EXECUTE_TOOLS", "TRACE_ENABLED", "VERBOSE_OUTPUT", "TRANSIENT_TRACE",
    "TOOL_TIMEOUT_SECONDS", "_TRANSIENT_TRACE_ACTIVE",
    "_TRANSIENT_TRACE_UPDATED_AT", "TRANSIENT_TRACE_MIN_SECONDS",
    "USER_VISIBLE_OUTPUT_LANGUAGE", "LIONESS_MODE_QUESTION", "PROJECT_ROOT",
    "SESSION_ROOT", "TOOL_LOG_ROOT", "TRACE_ROOT", "MEMORY_ROOT",
    "PROFILE_ROOT", "EPISODE_ROOT", "TOOL_RAW_MAX_CHARS",
    "DEFAULT_RETENTION_DAYS", "DEFAULT_SESSION_HARD_RETENTION_DAYS",
    "DEFAULT_ROUTER_MODEL", "DEFAULT_ROUTER_MAX_TOKENS",
    "DEFAULT_RESPONSE_MAX_TOKENS", "DEFAULT_TASK_TOKEN_BUDGET",
    "DEFAULT_LLM_TIMEOUT_SECONDS", "DEFAULT_LLM_MAX_RETRIES",
    "DEFAULT_TOOL_TIMEOUT_SECONDS", "MAX_RECOVERY_ATTEMPTS",
    "ROUTER_CONTEXT_MAX_CHARS", "DEFAULT_EPISODE_RETENTION_DAYS",
    "DEFAULT_EPISODE_DRY_RUN_RETENTION_DAYS",
    "DEFAULT_EPISODE_FAILED_RETENTION_DAYS", "DEFAULT_EPISODE_MAX_COUNT",
    "DEFAULT_EPISODE_MAX_BYTES", "_ui_text", "output_language_policy",
    "_clear_transient_trace", "_trace_line", "_trace", "AgentState",
    "AgentTurnInterrupted", "ClarificationInputError", "PreferenceProposal",
    "RouterDecision", "TaskDecision", "LLMUsage", "InputEvidence",
    "RequestedOutcome", "OutcomeEvidence", "OutcomeHypothesis",
    "EvidenceDimension", "CapabilityMatch", "CapabilityMatchStatus",
    "WorkflowStep", "WorkflowPlan", "EvaluationResult", "PlanRubricItem",
    "PlanEvaluationResult", "NextTurnPrompt", "CLI_FOLLOW_UP_STARTERS",
    "strip_cli_owned_follow_up_question", "ArtifactValidationResult",
    "ToolExecutionResult", "AgentsPolicyHeader", "WorkflowPolicySpec",
    "WorkflowOutputCapabilitySpec",
    "ProjectPolicySnapshot", "UserProfile", "Episode", "INPUT_ROLE_FIELDS",
    "OUTPUT_ROLE_FIELDS", "PARAMETER_FIELDS", "_display_path", "_is_demo_request",
]
