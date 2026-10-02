"""CLI validation, persistence, tracing, and Graph construction."""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from typing import Callable

from ..contracts import ReplyIntentDecision
from ..contracts.planning import WorkflowPlan
from ..contracts.policy import ProjectPolicySnapshot
from ..graph import build_graph, invoke_graph_turn
from ..llm import build_llm, validate_response_model, validate_router_model
from ..memory import EpisodeStore, UserProfileStore, _safe_memory_id
from ..policy import ProjectPolicyError, ProjectPolicyLoader
from ..presentation import _trace
from ..pricing import PriceCatalog
from ..session import (
    _safe_session_id,
    cleanup_runtime_storage,
    cleanup_trace_storage,
    load_session,
    load_session_payload,
    resolve_resume_id,
)
from ..settings import DEFAULT_ROUTER_MODEL, PROJECT_ROOT, TRACE_ROOT
from ..trace_store import LocalTraceStore
from ..trace_sync import TraceSyncWorker
from ..tracing import TraceRecorder
from .reply_resolution import ContextualReplyResolver

__all__: list[str] = []


@dataclass(frozen=True, slots=True)
class MemoryRuntime:
    profile_id: str
    profile_store: UserProfileStore
    episode_store: EpisodeStore


@dataclass(slots=True)
class CliRuntime:
    memory: MemoryRuntime
    project_policy: ProjectPolicySnapshot
    session_id: str
    resume_id: str | None
    conversation: list
    pending_plan: WorkflowPlan | None
    active_usage: dict | None
    run_id: str | None
    recorder: TraceRecorder
    trace_store: LocalTraceStore
    ensure_trace_sync: Callable[[str], None]
    app: object
    input_func: Callable[[str], str]
    invoke_graph_turn_func: Callable[[object, dict], dict]
    reply_resolver: ContextualReplyResolver
    # The models this session runs under, recorded in its sidecar (session_meta).
    session_models: dict = field(default_factory=dict)


def _keep_session_models(args, resume_id: str) -> None:
    """A resumed session keeps the models it started with (one session, one model).

    Only defaults are replaced -- a model named on this command line wins --
    and only by models every allowlist still permits; otherwise the session
    runs under today's defaults and its sidecar records that it did.
    """
    from .. import session as session_store
    from ..session_meta import load_meta

    recorded = load_meta(resume_id, sessions_root=session_store.SESSION_ROOT).get("models") or {}
    defaults = {
        "model": os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        "router_model": os.environ.get("OPENROUTER_ROUTER_MODEL", DEFAULT_ROUTER_MODEL),
        "semantic_model": os.environ.get("OPENROUTER_SEMANTIC_MODEL"),
    }
    wanted = {"model": recorded.get("response"), "router_model": recorded.get("router"),
              "semantic_model": recorded.get("semantic")}
    try:
        if wanted["model"]:
            validate_response_model(wanted["model"])
        for name in ("router_model", "semantic_model"):
            if wanted[name]:
                validate_router_model(wanted[name])
    except ValueError:
        return
    for name, value in wanted.items():
        if value and getattr(args, name, None) == defaults[name]:
            setattr(args, name, value)


# OpenRouter's free models (ids ending in ":free") are reasoning models whose
# thinking counts as output: nemotron-3-super spent the whole 1,200-token cap
# thinking and returned no tool call, and its calls take 30-60 s (2026-10-02).
# They are not billed, so the caps that guard spending are raised for them only.
_FREE_MODEL_FLOORS = {
    "router_max_tokens": 6_000,
    "response_max_tokens": 6_000,
    "max_task_tokens": 150_000,
    "llm_timeout": 180.0,
}


def _widen_limits_for_free_models(args) -> None:
    models = (getattr(args, name, None) for name in ("model", "router_model", "semantic_model"))
    if not any(str(model or "").endswith(":free") for model in models):
        return
    for name, floor in _FREE_MODEL_FLOORS.items():
        setattr(args, name, max(getattr(args, name), floor))


def bootstrap_memory(args) -> MemoryRuntime:
    profile_id = _safe_memory_id(args.profile)
    profile_store = UserProfileStore()
    if (
        min(
            args.retention_days,
            args.session_hard_retention_days,
            args.episode_retention_days,
            args.episode_max_count,
            args.episode_max_mb,
            args.trace_retention_days,
        )
        <= 0
    ):
        raise SystemExit("Retention and memory limits must be positive.")
    return MemoryRuntime(
        profile_id=profile_id,
        profile_store=profile_store,
        episode_store=EpisodeStore(
            max_episodes=args.episode_max_count,
            retention_days=args.episode_retention_days,
            max_bytes=int(args.episode_max_mb * 1024 * 1024),
        ),
    )


def load_project_policy() -> ProjectPolicySnapshot:
    try:
        return ProjectPolicyLoader(PROJECT_ROOT).load()
    except ProjectPolicyError as error:
        raise SystemExit(f"Project policy validation failed: {error}") from error


def bootstrap_runtime(
    args,
    memory_runtime: MemoryRuntime,
    policy: ProjectPolicySnapshot,
    *,
    recorder_factory=TraceRecorder,
) -> CliRuntime:
    """Build the runtime one conversation needs.

    ``recorder_factory`` exists so a non-terminal driver can wrap the recorder
    and forward trace events to a UI.  The wrapper must still persist through
    ``LocalTraceStore`` first; a UI may not see an event the hash chain does
    not have.
    """
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise SystemExit(
            "Missing OPENROUTER_API_KEY. Export it first, for example:\n"
            "export OPENROUTER_API_KEY='sk-or-v1-...'"
        )

    cleanup = cleanup_runtime_storage(
        args.retention_days,
        args.session_hard_retention_days,
    )
    cleanup["traces"] = cleanup_trace_storage(args.trace_retention_days)
    if any(cleanup.values()):
        _trace(
            "done",
            "Expired runtime data was pruned",
            (
                f"sessions={cleanup['sessions']}, logs={cleanup['logs']}, "
                f"traces={cleanup['traces']}"
            ),
        )

    resume_id = resolve_resume_id(args.resume, memory_runtime.profile_id)
    if resume_id:
        _keep_session_models(args, resume_id)
    _widen_limits_for_free_models(args)
    if min(args.router_max_tokens, args.response_max_tokens, args.max_task_tokens) <= 0:
        raise SystemExit("Token limits must be positive integers.")
    if args.llm_timeout <= 0:
        raise SystemExit("--llm-timeout must be positive.")
    try:
        validate_router_model(args.router_model)
        if args.semantic_model:
            validate_router_model(args.semantic_model)
        validate_response_model(args.model)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    session_id = _safe_session_id(args.session or resume_id or uuid.uuid4().hex[:8])
    conversation = []
    pending_plan = None
    active_usage = None
    trace_store = LocalTraceStore(TRACE_ROOT)
    trace_store.preflight()
    recorder = recorder_factory(trace_store)
    collector_url = os.environ.get("NETZOO_OBSERVER_URL", "").strip()
    collector_agent_key = os.environ.get("NETZOO_OBSERVER_AGENT_KEY", "").strip()
    allow_insecure_observer = os.environ.get(
        "NETZOO_OBSERVER_ALLOW_INSECURE", ""
    ).casefold() in {"1", "true", "yes"}
    sync_worker = (
        TraceSyncWorker(
            trace_store,
            collector_url,
            collector_agent_key,
            allow_insecure=allow_insecure_observer,
        )
        if collector_url and collector_agent_key
        else None
    )
    synchronizing_runs: set[str] = set()

    def ensure_trace_sync(active_run_id: str) -> None:
        if sync_worker is None or active_run_id in synchronizing_runs:
            return
        sync_worker.start_background(active_run_id)
        synchronizing_runs.add(active_run_id)

    run_id = None
    if resume_id:
        saved_payload = load_session_payload(resume_id)
        conversation, saved_plan, active_usage = load_session(
            resume_id,
            include_usage=True,
        )
        run_id = saved_payload.get("run_id")
        if run_id:
            trace_store.verify_run(run_id)
            recorder.append(
                run_id,
                "run.resumed",
                "cli",
                {"session_id": session_id},
            )
            ensure_trace_sync(str(run_id))
        else:
            run_id = str(
                recorder.start_run(
                    session_id=session_id,
                    profile_id=memory_runtime.profile_id,
                )
            )
            ensure_trace_sync(run_id)
        if saved_plan:
            candidate = WorkflowPlan.model_validate(saved_plan)
            if candidate.status in {"needs_input", "needs_confirmation"}:
                pending_plan = candidate
        _trace("done", f"Resumed session {session_id}")
    else:
        _trace("done", f"Session: {session_id}")

    app = build_graph(
        args.model,
        args.temperature,
        profile_id=memory_runtime.profile_id,
        profile_store=memory_runtime.profile_store,
        episode_store=memory_runtime.episode_store,
        project_policy=policy,
        router_model_name=args.router_model,
        semantic_model_name=args.semantic_model,
        router_max_tokens=args.router_max_tokens,
        response_max_tokens=args.response_max_tokens,
        task_token_budget=args.max_task_tokens,
        timeout_seconds=args.llm_timeout,
        trace_recorder=recorder,
    )
    reply_llm = build_llm(
        args.router_model,
        0.0,
        max_output_tokens=min(args.router_max_tokens, 256),
        timeout_seconds=args.llm_timeout,
    )
    reply_model = reply_llm.with_structured_output(
        ReplyIntentDecision,
        method="function_calling",
        include_raw=True,
    )
    reply_resolver = ContextualReplyResolver(
        reply_model,
        model_name=args.router_model,
        task_token_budget=args.max_task_tokens,
        recorder=recorder,
        price_catalog=PriceCatalog.from_environment(),
        max_output_tokens=min(args.router_max_tokens, 256),
    )
    return CliRuntime(
        session_models={
            "response": args.model,
            "router": args.router_model,
            "semantic": args.semantic_model or args.router_model,
        },
        memory=memory_runtime,
        project_policy=policy,
        session_id=session_id,
        resume_id=resume_id,
        conversation=conversation,
        pending_plan=pending_plan,
        active_usage=active_usage,
        run_id=run_id,
        recorder=recorder,
        trace_store=trace_store,
        ensure_trace_sync=ensure_trace_sync,
        app=app,
        input_func=input,
        invoke_graph_turn_func=invoke_graph_turn,
        reply_resolver=reply_resolver,
    )
