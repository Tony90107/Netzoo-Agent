"""Shared typed contracts, runtime policy constants, and CLI tracing."""

from __future__ import annotations


import re
import sys
import time
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import NotRequired, TypedDict

from workflow_registry import (
    ActionName,
    IntentType,
    PreferenceKey,
    RecommendedAction,
)

from .trace_contracts import LLMCallUsage

try:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    from langchain_core.tools import tool
    from langgraph.graph import END, START, StateGraph
    from langgraph.graph.message import add_messages
except ImportError:
    END = START = StateGraph = None

    class _LocalMessage:
        type = "message"

        def __init__(self, content: str):
            self.content = content

    class AIMessage(_LocalMessage):
        type = "ai"

    class HumanMessage(_LocalMessage):
        type = "human"

    class SystemMessage(_LocalMessage):
        type = "system"

    def add_messages(messages):
        return messages

    class _LocalTool:
        def __init__(self, func):
            self.func = func
            self.name = func.__name__
            self.description = func.__doc__ or ""

        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)

        def invoke(self, arguments):
            if isinstance(arguments, dict):
                return self.func(**arguments)
            return self.func(arguments)

    def tool(func):
        return _LocalTool(func)


__all__ = [
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
    "ProjectPolicySnapshot",
    "UserProfile",
    "Episode",
    "INPUT_ROLE_FIELDS",
    "OUTPUT_ROLE_FIELDS",
    "PARAMETER_FIELDS",
    "_display_path",
    "_is_demo_request",
]


EXECUTE_TOOLS = False


TRACE_ENABLED = False


VERBOSE_OUTPUT = False


TRANSIENT_TRACE = False


DEFAULT_TOOL_TIMEOUT_SECONDS = 86_400.0


TOOL_TIMEOUT_SECONDS = DEFAULT_TOOL_TIMEOUT_SECONDS


MAX_RECOVERY_ATTEMPTS = 1


_TRANSIENT_TRACE_ACTIVE = False


_TRANSIENT_TRACE_UPDATED_AT = 0.0


TRANSIENT_TRACE_MIN_SECONDS = 0.6


USER_VISIBLE_OUTPUT_LANGUAGE = "English"


LIONESS_MODE_QUESTION = (
    "Which LIONESS mode should run? Choose 1, 2, or 3. "
    "If expression is the only available input, option 3 is usually appropriate. "
    "After selection, the agent will discover and validate remaining inputs and "
    "request authorization before actual execution."
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


SESSION_ROOT = PROJECT_ROOT / ".netzoo" / "sessions"


TOOL_LOG_ROOT = PROJECT_ROOT / ".netzoo" / "logs"


TRACE_ROOT = PROJECT_ROOT / ".netzoo" / "traces"


MEMORY_ROOT = PROJECT_ROOT / ".netzoo" / "memory"


PROFILE_ROOT = MEMORY_ROOT / "profiles"


EPISODE_ROOT = MEMORY_ROOT / "episodes"


TOOL_RAW_MAX_CHARS = 8_000


DEFAULT_RETENTION_DAYS = 30


DEFAULT_SESSION_HARD_RETENTION_DAYS = 180


DEFAULT_ROUTER_MODEL = "openai/gpt-4o-mini"


DEFAULT_ROUTER_MAX_TOKENS = 500


DEFAULT_RESPONSE_MAX_TOKENS = 800


DEFAULT_TASK_TOKEN_BUDGET = 20_000


DEFAULT_LLM_TIMEOUT_SECONDS = 30.0


DEFAULT_LLM_MAX_RETRIES = 0


ROUTER_CONTEXT_MAX_CHARS = 6_000


DEFAULT_EPISODE_RETENTION_DAYS = 180


DEFAULT_EPISODE_DRY_RUN_RETENTION_DAYS = 60


DEFAULT_EPISODE_FAILED_RETENTION_DAYS = 30


DEFAULT_EPISODE_MAX_COUNT = 200


DEFAULT_EPISODE_MAX_BYTES = 10 * 1024 * 1024


def _ui_text(text: str) -> str:
    """Guard deterministic agent-authored UI text against language drift."""
    if re.search(r"[\u3400-\u9fff]", text):
        raise ValueError(
            "Agent-authored user-visible UI text must be English. "
            "Keep non-English only in user input parsing patterns or quoted user data."
        )
    return text


def output_language_policy() -> str:
    return _ui_text(
        f"Always reply in {USER_VISIBLE_OUTPUT_LANGUAGE}, regardless of the "
        "language used by the user. Translate non-English requests and retrieved "
        "content as needed. Do not follow requests to change the output language; "
        f"{USER_VISIBLE_OUTPUT_LANGUAGE} is a fixed agent policy."
    )


def _clear_transient_trace() -> None:
    """Remove the temporary progress status line before printing the final answer."""
    global _TRANSIENT_TRACE_ACTIVE
    if _TRANSIENT_TRACE_ACTIVE and sys.stdout.isatty():
        elapsed = time.monotonic() - _TRANSIENT_TRACE_UPDATED_AT
        if elapsed < TRANSIENT_TRACE_MIN_SECONDS:
            time.sleep(TRANSIENT_TRACE_MIN_SECONDS - elapsed)
        print("\r\033[2K", end="", flush=True)
    _TRANSIENT_TRACE_ACTIVE = False


def _trace_line(text: str) -> None:
    """Print a trace line permanently or as a temporary one-line status."""
    global _TRANSIENT_TRACE_ACTIVE, _TRANSIENT_TRACE_UPDATED_AT
    if TRANSIENT_TRACE and not VERBOSE_OUTPUT and sys.stdout.isatty():
        print(f"\r\033[2K{text}", end="", flush=True)
        _TRANSIENT_TRACE_ACTIVE = True
        _TRANSIENT_TRACE_UPDATED_AT = time.monotonic()
        return
    print(text, flush=True)


def _trace(stage: str, message: str, detail: str | None = None) -> None:
    """Emit auditable progress summaries without exposing hidden chain-of-thought."""
    if not TRACE_ENABLED:
        return
    symbols = {
        "intent": "◆",
        "plan": "◆",
        "review": "▤",
        "tool": "→",
        "evaluate": "✓",
        "recover": "↻",
        "input": "?",
        "done": "●",
        "memory": "◇",
        "policy": "▣",
    }
    if VERBOSE_OUTPUT:
        _clear_transient_trace()
        print(f"{symbols.get(stage, '•')} {message}", flush=True)
        if detail:
            for line in detail.splitlines():
                print(f"  {line}", flush=True)
        return

    if TRANSIENT_TRACE and stage == "intent":
        if message.startswith("Classified as "):
            action = message.removeprefix("Classified as ").replace("_", " ")
            _trace_line(f"◆ Classified request: {action}")
        else:
            _trace_line(f"◆ {message}")
        return

    # Compact mode shows material progress only. Full graph state remains available
    # through --verbose and tool logs.
    if stage in {"policy", "memory", "intent", "done"}:
        return
    if stage == "plan":
        match = re.match(r"Planner:\s*(.+?)\s*/\s*(\w+)", message)
        if match:
            workflow, status = match.groups()
            if status == "ready":
                mode = "execution" if EXECUTE_TOOLS else "dry run"
                _trace_line(f"◆ {workflow} · {mode}")
            elif status == "needs_input":
                _trace_line(f"◆ {workflow} · additional input required")
            elif status == "needs_confirmation":
                _trace_line("◆ Preference confirmation required")
            elif status == "respond_only":
                _trace_line("◆ Preparing answer without tools")
        return
    if stage == "review":
        if "approved" in message.casefold():
            _trace_line("✓ Plan evaluation approved")
        elif "rejected" in message.casefold():
            _trace_line("✗ Plan evaluation rejected")
        return
    if stage == "tool":
        executor = re.match(r"Executor \[\d+/\d+\]:\s*(\w+)", message)
        if executor:
            action = executor.group(1)
            if action.startswith("inspect_"):
                label = "Validating inputs"
            elif action.startswith("run_"):
                workflow = action.removeprefix("run_").replace("_", "-").upper()
                label = (
                    f"Running {workflow}"
                    if EXECUTE_TOOLS
                    else f"Preparing {workflow} command"
                )
            else:
                label = action.replace("_", " ").capitalize()
            _trace_line(f"→ {label}")
            return
        result = re.match(r"(\w+)\s*→\s*(success|dry_run|failed)", message)
        if result:
            action, status = result.groups()
            if action.startswith("inspect_"):
                label = (
                    "Input validation passed"
                    if status != "failed"
                    else "Input validation failed"
                )
            else:
                workflow = action.removeprefix("run_").replace("_", "-").upper()
                label = (
                    f"{workflow} completed"
                    if status == "success"
                    else (
                        "Command preview ready"
                        if status == "dry_run"
                        else f"{workflow} failed"
                    )
                )
            marker = "✓" if status == "success" else "○" if status == "dry_run" else "✗"
            _trace_line(f"{marker} {label}")
        return
    if stage == "evaluate":
        if re.search(r"Evaluator:\s*(replan|failed)", message):
            _trace_line(f"{symbols[stage]} {message}")
            if detail:
                _clear_transient_trace()
                print(f"  {detail}", flush=True)
        return
    if stage == "recover":
        _trace_line(f"{symbols[stage]} Recovery plan selected")
        return
    if stage == "input":
        _trace_line(f"{symbols[stage]} {message}")
        # The full question is rendered by the interactive prompt; printing it here
        # makes mode-selection prompts appear duplicated.
        return


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    decision: NotRequired[dict]
    plan: NotRequired[dict]
    plan_evaluation: NotRequired[dict]
    current_step: NotRequired[int]
    tool_result: NotRequired[dict]
    tool_results: NotRequired[list[dict]]
    evaluation: NotRequired[dict]
    replan_count: NotRequired[int]
    profile: NotRequired[dict]
    retrieved_episodes: NotRequired[list[dict]]
    project_policy: NotRequired[dict]
    token_usage: NotRequired[dict]
    run_id: NotRequired[str]


class AgentTurnInterrupted(Exception):
    """Raised when the user interrupts an in-flight graph turn."""


class ClarificationInputError(ValueError):
    """Raised when one reply cannot unambiguously resolve every displayed field."""


class PreferenceProposal(BaseModel):
    key: PreferenceKey
    value: str
    reason: str


class RouterDecision(BaseModel):
    """Small LLM-facing interface; deterministic code hydrates execution details."""

    action: ActionName
    in_scope: bool = True
    intent_type: IntentType = "unknown"
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=300)
    recommended_actions: list[RecommendedAction] = Field(
        default_factory=list, max_length=4
    )


class TaskDecision(BaseModel):
    """A capability-aware routing decision for the allow-listed NetZoo agent."""

    action: ActionName
    in_scope: bool = Field(
        description="True only when the requested operation is supported by this agent."
    )
    should_execute: bool = Field(
        description="True only when a tool call is necessary to fulfil the request now."
    )
    intent_type: IntentType = Field(
        default="unknown",
        description=(
            "High-level user intent. answer_question means explain concepts, "
            "formats, inputs, or usage without running local tools."
        ),
    )
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    recommended_actions: list[RecommendedAction] = Field(
        default_factory=list,
        description=(
            "Allow-listed local capabilities that fit the user's goal, ordered as a "
            "useful workflow. Populate this even when action=no_tool because the user "
            "asked for advice rather than immediate execution."
        ),
    )
    missing_inputs: list[str] = Field(default_factory=list)
    expression_file: str | None = None
    motif_file: str | None = None
    ppi_file: str | None = None
    mirna_file: str | None = None
    output_file: str | None = None
    lioness_output: str | None = None
    network_file: str | None = None
    output_dir: str | None = None
    prefix: str | None = None
    with_header: bool = False
    genes_axis: Literal["auto", "rows", "columns"] = "auto"
    library_name: str | None = None
    library_id: str | None = None
    docs_query: str | None = None
    web_query: str | None = None
    preference_updates: list[PreferenceProposal] = Field(default_factory=list)


class LLMUsage(BaseModel):
    """Per-task token telemetry with explicit estimated/actual provenance."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    calls: list[LLMCallUsage] = Field(default_factory=list)
    budget_tokens: int = DEFAULT_TASK_TOKEN_BUDGET
    budget_exhausted: bool = False


class InputEvidence(BaseModel):
    """Where a workflow input came from and why it is (or is not) usable."""

    field: str
    status: Literal[
        "provided",
        "selected",
        "discovered",
        "demo_bundle",
        "defaulted",
        "missing",
    ]
    value: str | None = None
    reason: str
    candidates: list[str] = Field(default_factory=list)
    bundle_id: str | None = None


class WorkflowStep(BaseModel):
    action: str
    purpose: str
    arguments: dict = Field(default_factory=dict)


class WorkflowPlan(BaseModel):
    workflow: str
    objective: str
    decision: dict
    evidence: list[InputEvidence] = Field(default_factory=list)
    steps: list[WorkflowStep] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    status: Literal["ready", "needs_input", "needs_confirmation", "respond_only"]
    question: str | None = None
    preference_proposals: list[PreferenceProposal] = Field(default_factory=list)
    memory_notes: list[str] = Field(default_factory=list)
    policy_hash: str | None = None
    policy_notes: list[str] = Field(default_factory=list)
    recovery_action: Literal["format_expression_headerless"] | None = None
    recovery_step_index: int | None = Field(default=None, ge=0)
    recovery_attempt: int = Field(default=0, ge=0, le=MAX_RECOVERY_ATTEMPTS)


class EvaluationResult(BaseModel):
    status: Literal["continue", "completed", "needs_input", "replan", "failed"]
    reason: str
    recovery_action: str | None = None


class PlanRubricItem(BaseModel):
    """One machine-readable pre-execution planning criterion."""

    criterion: str
    required: bool = True
    result: Literal["pass", "fail", "not_applicable"]
    detail: str


class PlanEvaluationResult(BaseModel):
    """Code-enforced verdict produced before any workflow tool may execute."""

    status: Literal["approved", "deferred", "rejected"]
    score: int = Field(ge=0, le=100)
    summary: str
    rubric: list[PlanRubricItem] = Field(default_factory=list)


class NextTurnPrompt(BaseModel):
    """Outcome-aware CLI prompt plus optional workflow continuation context."""

    kind: Literal[
        "initial",
        "recommended_workflow",
        "dry_run",
        "completed",
        "failed",
        "plan_rejected",
        "unsupported",
        "retrieval",
    ]
    question: str
    continuation_action: str | None = None
    expected_field: str | None = None


CLI_FOLLOW_UP_STARTERS = (
    "would you like",
    "do you want",
    "shall i",
    "shall we",
    "would you prefer",
    "should i",
)


def strip_cli_owned_follow_up_question(text: str) -> str:
    """Remove only a trailing conversational CTA that duplicates the CLI prompt."""
    rendered = text.rstrip()
    if "\n" not in rendered:
        return rendered
    boundaries = list(re.finditer(r"\n\s*\n", rendered))
    starts = [boundaries[-1].end()] if boundaries else []
    starts.append(rendered.rfind("\n") + 1)
    for start in starts:
        tail = re.sub(r"\s+", " ", rendered[start:]).strip()
        lowered = tail.casefold()
        if tail.endswith("?") and lowered.startswith(CLI_FOLLOW_UP_STARTERS):
            cleaned = rendered[:start].rstrip()
            return cleaned or rendered
    return rendered


class ArtifactValidationResult(BaseModel):
    """Structural verification outcome for files produced by one workflow."""

    ok: bool
    artifacts: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metrics: dict[str, int | float | str | bool] = Field(default_factory=dict)


class ToolExecutionResult(BaseModel):
    """Stable contract between Executor and Evaluator."""

    action: str
    status: Literal["success", "dry_run", "failed"]
    summary: str
    attempt_id: int = Field(default=0, ge=0)
    superseded: bool = False
    superseded_reason: str | None = None
    artifacts: list[str] = Field(default_factory=list)
    metrics: dict[str, int | float | str | bool] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    retryable: bool = False
    recovery_hint: str | None = None
    log_file: str | None = None
    raw_output: str = ""


class AgentsPolicyHeader(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: Literal[1]
    project: str = Field(min_length=1, max_length=120)
    workflow_spec_dir: str = Field(min_length=1, max_length=200)
    conventions: list[str] = Field(default_factory=list, max_length=20)


class WorkflowPolicySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: Literal[1]
    workflow: str = Field(min_length=1, max_length=80)
    action: Literal[
        "run_panda",
        "run_puma",
        "run_lioness_panda",
        "run_lioness_puma",
        "run_lioness_coexpression",
        "run_condor",
    ]
    description: str = Field(min_length=1, max_length=500)
    required_inputs: list[str] = Field(max_length=12)
    optional_inputs: list[str] = Field(default_factory=list, max_length=12)
    validation_steps: list[Literal["inspect_inputs", "inspect_condor_inputs"]] = Field(
        default_factory=list, max_length=4
    )
    execution_step: Literal[
        "run_panda",
        "run_puma",
        "run_lioness_panda",
        "run_lioness_puma",
        "run_lioness_coexpression",
        "run_condor",
    ]
    conventions: list[str] = Field(default_factory=list, max_length=20)


class ProjectPolicySnapshot(BaseModel):
    policy_version: Literal[1]
    project: str
    agents_path: str
    workflow_spec_dir: str
    policy_hash: str
    conventions: list[str] = Field(default_factory=list)
    workflows: dict[str, WorkflowPolicySpec]

    def router_capability_summary(self) -> str:
        """Generate the run-workflow catalog from the validated policy registry."""
        lines = []
        for action, spec in sorted(self.workflows.items()):
            lines.append(
                f"- {action}: {spec.description} "
                f"Required inputs: {', '.join(spec.required_inputs)}."
            )
        return "\n".join(lines)


class UserProfile(BaseModel):
    profile_id: str
    version: int = 1
    preferences: dict[str, str | bool | list[str]] = Field(default_factory=dict)
    sources: dict[str, str] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class Episode(BaseModel):
    episode_id: str
    profile_id: str
    created_at: float = Field(default_factory=time.time)
    task_summary: str
    raw_task_excerpt: str | None = None
    workflow: str
    action: str | None = None
    intent_type: str | None = None
    status: Literal["completed", "dry_run", "failed"]
    inputs: dict[str, str] = Field(default_factory=dict)
    input_roles: list[str] = Field(default_factory=list)
    output_roles: list[str] = Field(default_factory=list)
    parameters: list[str] = Field(default_factory=list)
    validation_steps: list[str] = Field(default_factory=list)
    execution_steps: list[str] = Field(default_factory=list)
    validation_status: Literal["passed", "failed", "not_applicable"] = "not_applicable"
    execution_mode: Literal["executed", "dry_run"] = "executed"
    memory_tags: list[str] = Field(default_factory=list)
    domain_metadata: dict[str, str] = Field(default_factory=dict)
    artifacts: list[str] = Field(default_factory=list)
    metrics: dict[str, int | float | str | bool] = Field(default_factory=dict)
    error_signature: str | None = None
    recovery_actions: list[str] = Field(default_factory=list)
    log_files: list[str] = Field(default_factory=list)
    policy_hash: str | None = None


INPUT_ROLE_FIELDS = {
    "expression_file",
    "motif_file",
    "ppi_file",
    "mirna_file",
    "network_file",
}


OUTPUT_ROLE_FIELDS = {"output_file", "lioness_output", "output_dir"}


PARAMETER_FIELDS = {"prefix", "with_header", "genes_axis"}


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _is_demo_request(task: str) -> bool:
    return bool(
        re.search(
            r"(試跑|試試看|試一下|測一下|跑\s*一次|run\s*一次|測試|示範"
            r"|demo|trial|toy|test run|run(?:\s+(?:it|this|the))?\s+once)",
            task,
            flags=re.IGNORECASE,
        )
    )
