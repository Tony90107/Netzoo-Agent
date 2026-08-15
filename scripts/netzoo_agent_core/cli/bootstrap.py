"""CLI validation, persistence, tracing, and Graph construction."""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
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
from ..settings import PROJECT_ROOT, TRACE_ROOT
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
) -> CliRuntime:
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
    if min(args.router_max_tokens, args.response_max_tokens, args.max_task_tokens) <= 0:
        raise SystemExit("Token limits must be positive integers.")
    if args.llm_timeout <= 0:
        raise SystemExit("--llm-timeout must be positive.")
    try:
        validate_router_model(args.router_model)
        validate_response_model(args.model)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    session_id = _safe_session_id(args.session or resume_id or uuid.uuid4().hex[:8])
    conversation = []
    pending_plan = None
    active_usage = None
    trace_store = LocalTraceStore(TRACE_ROOT)
    trace_store.preflight()
    recorder = TraceRecorder(trace_store)
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
