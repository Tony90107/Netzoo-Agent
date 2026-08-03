"""Command-line parsing and the interactive application loop."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path


from .contracts import (
    AgentTurnInterrupted,
    ClarificationInputError,
    DEFAULT_EPISODE_MAX_BYTES,
    DEFAULT_EPISODE_MAX_COUNT,
    DEFAULT_EPISODE_RETENTION_DAYS,
    DEFAULT_LLM_TIMEOUT_SECONDS,
    DEFAULT_RESPONSE_MAX_TOKENS,
    DEFAULT_RETENTION_DAYS,
    DEFAULT_ROUTER_MAX_TOKENS,
    DEFAULT_ROUTER_MODEL,
    DEFAULT_SESSION_HARD_RETENTION_DAYS,
    DEFAULT_TASK_TOKEN_BUDGET,
    DEFAULT_TOOL_TIMEOUT_SECONDS,
    HumanMessage,
    LLMUsage,
    NextTurnPrompt,
    PROJECT_ROOT,
    TRACE_ROOT,
    WorkflowPlan,
    _clear_transient_trace,
    _trace,
    _ui_text,
)

from .memory import (
    EpisodeStore,
    UserProfileStore,
    _safe_memory_id,
    compact_episode_payload,
)

from .routing import (
    query_web_search_first_url,
)

from .policy import (
    ProjectPolicyError,
    ProjectPolicyLoader,
)

from .llm import (
    validate_response_model,
    validate_router_model,
)

from .graph import (
    build_graph,
    invoke_graph_turn,
)

from .session import (
    _is_auto_session_id,
    _safe_session_id,
    cleanup_runtime_storage,
    cleanup_trace_storage,
    compact_conversation,
    delete_session,
    load_session,
    load_session_payload,
    resolve_resume_id,
    save_session,
)

from .interaction import (
    build_next_turn_prompt,
    clarification_continuation,
    clarification_prompt,
    follow_up_declined,
    follow_up_returns_to_main,
    initial_next_turn_prompt,
    parse_clarification_assignments,
    preference_confirmation_prompt,
    preference_continuation,
    render_next_turn_prompt,
    resolve_clarification,
    resolve_next_turn_input,
)
from .runtime import configure_runtime
from .trace_store import LocalTraceStore
from .tracing import TraceRecorder

__all__ = [
    "parse_args",
    "main",
    "export_local_trace",
    "local_trace_status",
]


def local_trace_status(run_id: str, *, trace_root: Path = TRACE_ROOT) -> dict:
    """Verify and summarize one local trace without an LLM or provider key."""
    verification = LocalTraceStore(trace_root).verify_run(run_id)
    return {"run_id": run_id, **verification.model_dump(mode="json")}


def export_local_trace(
    run_id: str,
    destination: Path,
    *,
    trace_root: Path = TRACE_ROOT,
) -> Path:
    """Export one verified local audit package without overwriting a file."""
    return LocalTraceStore(trace_root).export_run(run_id, Path(destination))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "LangGraph Planner/Executor/Evaluator agent for PANDA, PUMA, "
            "LIONESS, and CONDOR workflows."
        )
    )
    parser.add_argument(
        "--task",
        help="Task written in natural language. If omitted, ask interactively.",
    )
    parser.add_argument(
        "--web-url",
        metavar="QUERY",
        help="Search through Websearch MCP and print only the first result URL; no LLM call.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually run NetZooPy/CONDOR commands after validation.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        help=(
            "OpenRouter response model name; it must be listed in "
            "NETZOO_RESPONSE_MODEL_ALLOWLIST."
        ),
    )
    parser.add_argument(
        "--router-model",
        default=os.environ.get("OPENROUTER_ROUTER_MODEL", DEFAULT_ROUTER_MODEL),
        help=(
            "Cheap allow-listed OpenRouter model used only for routing. "
            "Configure NETZOO_ROUTER_MODEL_ALLOWLIST to permit alternatives."
        ),
    )
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument(
        "--router-max-tokens",
        type=int,
        default=int(
            os.environ.get(
                "NETZOO_ROUTER_MAX_TOKENS",
                DEFAULT_ROUTER_MAX_TOKENS,
            )
        ),
        help="Maximum Router output tokens.",
    )
    parser.add_argument(
        "--response-max-tokens",
        type=int,
        default=int(
            os.environ.get(
                "NETZOO_RESPONSE_MAX_TOKENS",
                DEFAULT_RESPONSE_MAX_TOKENS,
            )
        ),
        help="Maximum response-model output tokens.",
    )
    parser.add_argument(
        "--max-task-tokens",
        type=int,
        default=int(
            os.environ.get(
                "NETZOO_MAX_TASK_TOKENS",
                DEFAULT_TASK_TOKEN_BUDGET,
            )
        ),
        help="Combined input/output token budget for one task, including clarifications.",
    )
    parser.add_argument(
        "--llm-timeout",
        type=float,
        default=float(
            os.environ.get(
                "NETZOO_LLM_TIMEOUT_SECONDS",
                DEFAULT_LLM_TIMEOUT_SECONDS,
            )
        ),
        help="Timeout in seconds for each Router or response-model call.",
    )
    parser.add_argument(
        "--tool-timeout",
        type=float,
        default=float(
            os.environ.get(
                "NETZOO_TOOL_TIMEOUT_SECONDS",
                DEFAULT_TOOL_TIMEOUT_SECONDS,
            )
        ),
        help=(
            "Timeout in seconds for one local NetZoo command; use 0 to disable "
            "the command timeout."
        ),
    )
    parser.add_argument(
        "--session",
        help="Session id used for a resumable checkpoint (generated when omitted).",
    )
    parser.add_argument(
        "--profile",
        default=os.environ.get("NETZOO_PROFILE", "default"),
        help="Long-term user profile id used for confirmed preferences and episodes.",
    )
    parser.add_argument(
        "--memory-status",
        action="store_true",
        help="Show the confirmed profile and compact episode count without calling an LLM.",
    )
    parser.add_argument(
        "--memory-cleanup",
        action="store_true",
        help="Migrate, secure and prune all episode memory without calling an LLM.",
    )
    parser.add_argument(
        "--forget-memory",
        action="store_true",
        help="Delete the selected profile and all of its compact episodes without calling an LLM.",
    )
    parser.add_argument(
        "--policy-status",
        action="store_true",
        help="Validate AGENTS.md and workflow YAML files, then show the effective policy without calling an LLM.",
    )
    parser.add_argument(
        "--resume",
        metavar="SESSION_ID",
        help="Resume a previous CLI session; use 'latest' for the newest pending session.",
    )
    parser.add_argument(
        "--keep-session",
        action="store_true",
        help="Keep an auto-generated checkpoint after a successful one-shot task.",
    )
    parser.add_argument(
        "--trace-status",
        metavar="RUN_ID",
        help="Verify and summarize one local trace without calling an LLM.",
    )
    parser.add_argument(
        "--trace-export",
        nargs=2,
        metavar=("RUN_ID", "ARCHIVE"),
        help="Export one verified local trace package without calling an LLM.",
    )
    parser.add_argument(
        "--trace-retention-days",
        type=int,
        default=int(os.environ.get("NETZOO_TRACE_RETENTION_DAYS", "90")),
        help="Retention period for sealed local traces.",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=int(os.environ.get("NETZOO_RETENTION_DAYS", DEFAULT_RETENTION_DAYS)),
        help="Retention period for old auto-generated completed sessions and tool logs.",
    )
    parser.add_argument(
        "--session-hard-retention-days",
        type=int,
        default=int(
            os.environ.get(
                "NETZOO_SESSION_HARD_RETENTION_DAYS",
                DEFAULT_SESSION_HARD_RETENTION_DAYS,
            )
        ),
        help="Hard expiry for named and pending sessions.",
    )
    parser.add_argument(
        "--episode-retention-days",
        type=int,
        default=int(
            os.environ.get(
                "NETZOO_EPISODE_RETENTION_DAYS",
                DEFAULT_EPISODE_RETENTION_DAYS,
            )
        ),
        help="Retention period for successful episodes.",
    )
    parser.add_argument(
        "--episode-max-count",
        type=int,
        default=int(
            os.environ.get(
                "NETZOO_EPISODE_MAX_COUNT",
                DEFAULT_EPISODE_MAX_COUNT,
            )
        ),
        help="Maximum retained episodes per profile.",
    )
    parser.add_argument(
        "--episode-max-mb",
        type=float,
        default=float(
            os.environ.get(
                "NETZOO_EPISODE_MAX_MB",
                DEFAULT_EPISODE_MAX_BYTES / (1024 * 1024),
            )
        ),
        help="Approximate episode storage ceiling per profile in MiB.",
    )
    parser.add_argument(
        "--transient-trace",
        action="store_true",
        help=(
            "Show compact progress summaries on a temporary status line and clear "
            "them before the final answer. This is not raw model chain-of-thought."
        ),
    )
    display_group = parser.add_mutually_exclusive_group()
    display_group.add_argument(
        "--verbose",
        action="store_true",
        help="Show the full evidence ledger, graph events, evaluator details, and log paths.",
    )
    display_group.add_argument(
        "--quiet",
        action="store_true",
        help="Hide progress events and print only the compact final answer.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_runtime(
        EXECUTE_TOOLS=args.execute,
        TRACE_ENABLED=not args.quiet,
        VERBOSE_OUTPUT=args.verbose,
        TRANSIENT_TRACE=(args.transient_trace and not args.verbose and not args.quiet),
        TOOL_TIMEOUT_SECONDS=args.tool_timeout,
    )

    if args.web_url:
        print(query_web_search_first_url(args.web_url))
        return 0

    if args.trace_status:
        print(json.dumps(local_trace_status(args.trace_status), indent=2))
        return 0
    if args.trace_export:
        run_id, archive = args.trace_export
        exported = export_local_trace(run_id, Path(archive))
        print(str(exported))
        return 0

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
    episode_store = EpisodeStore(
        max_episodes=args.episode_max_count,
        retention_days=args.episode_retention_days,
        max_bytes=int(args.episode_max_mb * 1024 * 1024),
    )
    if args.memory_cleanup:
        report = episode_store.maintain()
        runtime_cleanup = cleanup_runtime_storage(
            args.retention_days,
            args.session_hard_retention_days,
        )
        expired_traces = cleanup_trace_storage(args.trace_retention_days)
        print(
            json.dumps(
                {
                    **report.model_dump(),
                    "deleted": report.deleted,
                    "retention_days": episode_store.retention_days,
                    "failed_retention_days": episode_store.failed_retention_days,
                    "dry_run_retention_days": episode_store.dry_run_retention_days,
                    "max_count_per_profile": episode_store.max_episodes,
                    "max_mib_per_profile": round(
                        episode_store.max_bytes / (1024 * 1024),
                        2,
                    ),
                    "expired_sessions": runtime_cleanup["sessions"],
                    "expired_logs": runtime_cleanup["logs"],
                    "expired_traces": expired_traces,
                },
                indent=2,
            )
        )
        return 0
    if args.memory_status:
        profile = profile_store.load(profile_id)
        episodes = episode_store.list_for_profile(profile_id)
        print(
            json.dumps(
                {
                    "profile_id": profile_id,
                    "confirmed_preferences": profile.preferences,
                    "episode_count": len(episodes),
                    "latest_episode": (
                        episodes[0].model_dump()
                        if args.verbose and episodes
                        else compact_episode_payload(episodes[0])
                        if episodes
                        else None
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.forget_memory:
        profile_deleted = profile_store.delete(profile_id)
        episode_count = episode_store.delete_for_profile(profile_id)
        print(
            f"Deleted memory for profile '{profile_id}': "
            f"profile={'yes' if profile_deleted else 'no'}, episodes={episode_count}."
        )
        return 0

    try:
        project_policy = ProjectPolicyLoader(PROJECT_ROOT).load()
    except ProjectPolicyError as error:
        raise SystemExit(f"Project policy validation failed: {error}") from error
    if args.policy_status:
        print(
            json.dumps(
                {
                    "project": project_policy.project,
                    "policy_version": project_policy.policy_version,
                    "policy_hash": project_policy.policy_hash,
                    "agents_path": project_policy.agents_path,
                    "workflow_spec_dir": project_policy.workflow_spec_dir,
                    "workflows": sorted(project_policy.workflows),
                    "code_enforced": True,
                },
                indent=2,
            )
        )
        return 0

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

    resume_id = resolve_resume_id(args.resume, profile_id)

    if (
        min(
            args.router_max_tokens,
            args.response_max_tokens,
            args.max_task_tokens,
        )
        <= 0
    ):
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
    clarification_selections: dict[str, str] = {}
    active_usage = None
    trace_store = LocalTraceStore(TRACE_ROOT)
    trace_store.preflight()
    recorder = TraceRecorder(trace_store)
    run_id = None
    run_paused = False
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
        else:
            run_id = str(
                recorder.start_run(session_id=session_id, profile_id=profile_id)
            )
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
        profile_id=profile_id,
        profile_store=profile_store,
        episode_store=episode_store,
        project_policy=project_policy,
        router_model_name=args.router_model,
        router_max_tokens=args.router_max_tokens,
        response_max_tokens=args.response_max_tokens,
        task_token_budget=args.max_task_tokens,
        timeout_seconds=args.llm_timeout,
        trace_recorder=recorder,
    )

    queued_task = args.task
    one_shot = bool(args.task) and not resume_id
    next_prompt = initial_next_turn_prompt()
    if not args.task:
        print(_ui_text("NetZoo agent started. Enter exit or quit to stop."))

    while True:
        if queued_task is not None:
            task = queued_task.strip()
            queued_task = None
        elif pending_plan is not None:
            if not sys.stdin.isatty():
                _clear_transient_trace()
                if pending_plan.status == "needs_confirmation":
                    print("\n" + preference_confirmation_prompt(pending_plan))
                else:
                    print("\n" + clarification_prompt(pending_plan, batch=True))
                print(
                    _ui_text("Run the command again with --resume ")
                    + f"{session_id}"
                    + _ui_text(" after preparing the answer.")
                )
                return 2
            if pending_plan.status == "needs_confirmation":
                try:
                    answer = input(
                        "\n" + preference_confirmation_prompt(pending_plan)
                    ).strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if answer.casefold() in {"exit", "quit", "q", "離開", "結束"}:
                    break
                approved = answer.casefold() in {"y", "yes"}
                if approved:
                    profile_store.confirm(profile_id, pending_plan.preference_proposals)
                    print(
                        _ui_text("Saved confirmed preferences to profile ")
                        + f"'{profile_id}'."
                    )
                else:
                    print(_ui_text("Preference changes were not saved."))
                task = preference_continuation(pending_plan, approved)
            else:
                try:
                    answer = input(
                        "\n"
                        + clarification_prompt(
                            pending_plan,
                            clarification_selections,
                        )
                    ).strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if answer.casefold() in {"exit", "quit", "q", "離開", "結束"}:
                    break
                if not answer:
                    continue
                try:
                    mode_pending = "lioness_mode" in pending_plan.missing_inputs
                    if mode_pending:
                        task = resolve_clarification(pending_plan, answer)
                    else:
                        unresolved_fields = [
                            item.field
                            for item in pending_plan.evidence
                            if item.status == "missing"
                            and item.field not in clarification_selections
                        ]
                        target_field = (
                            unresolved_fields[0] if unresolved_fields else None
                        )
                        clarification_selections = parse_clarification_assignments(
                            pending_plan,
                            answer,
                            selected=clarification_selections,
                            target_field=target_field,
                            require_all=False,
                        )
                        still_missing = [
                            field_name
                            for field_name in pending_plan.missing_inputs
                            if field_name not in clarification_selections
                        ]
                        if still_missing:
                            continue
                        task = clarification_continuation(
                            pending_plan,
                            clarification_selections,
                        )
                        clarification_selections = {}
                except ClarificationInputError as error:
                    print("\n" + _ui_text("Selection not accepted: ") + str(error))
                    continue
        else:
            if one_shot:
                break
            try:
                answer = input(f"\n{render_next_turn_prompt(next_prompt)}\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if follow_up_returns_to_main(next_prompt, answer):
                next_prompt = initial_next_turn_prompt()
                continue
            if not answer:
                continue
            if next_prompt.kind == "recommended_workflow" and follow_up_declined(
                answer
            ):
                next_prompt = initial_next_turn_prompt()
                continue
            task = resolve_next_turn_input(next_prompt, answer)
        if task.casefold() in {"exit", "quit", "q", "離開", "結束"}:
            break
        if not task:
            continue
        if run_id is None:
            run_id = str(
                recorder.start_run(session_id=session_id, profile_id=profile_id)
            )
        elif run_paused:
            recorder.append(
                run_id,
                "run.resumed",
                "cli",
                {"session_id": session_id},
            )
            run_paused = False
        try:
            invocation = {
                "messages": [*conversation, HumanMessage(content=task)],
                "session_id": session_id,
                "run_id": run_id,
            }
            if active_usage is not None:
                invocation["token_usage"] = active_usage
            result = invoke_graph_turn(app, invocation)
        except AgentTurnInterrupted:
            recorder.append(
                run_id,
                "run.interrupted",
                "cli",
                {"reason": "keyboard_interrupt"},
            )
            _clear_transient_trace()
            print()
            print(
                _ui_text(
                    "The current request was interrupted. No unfinished local "
                    "analysis command will be reported as completed."
                )
            )
            return 130
        except Exception as error:
            recorder.append(
                run_id,
                "error.recorded",
                "cli",
                {"error_type": type(error).__name__, "message": str(error)},
            )
            _clear_transient_trace()
            print(
                _ui_text(
                    "The agent could not finish this request. No unfinished provider "
                    "or local-tool step will be reported as completed."
                )
            )
            print(_ui_text("Error type: ") + type(error).__name__)
            next_prompt = NextTurnPrompt(
                kind="failed",
                question=_ui_text(
                    "Would you like to retry with a clearer request, describe a "
                    "different NetZoo goal, or enter exit?"
                ),
            )
            continue
        conversation = compact_conversation(result["messages"])
        active_usage = result.get("token_usage")
        save_session(session_id, conversation, result, profile_id=profile_id)
        plan = WorkflowPlan.model_validate(result["plan"])
        pending_plan = (
            plan if plan.status in {"needs_input", "needs_confirmation"} else None
        )
        clarification_selections = {}
        if active_usage:
            usage = LLMUsage.model_validate(active_usage)
            _trace(
                "done",
                (
                    f"LLM tokens: input={usage.input_tokens}, "
                    f"output={usage.output_tokens}, total={usage.total_tokens}, "
                    f"budget={usage.budget_tokens}"
                ),
                "estimated calls are marked in the saved token_usage records",
            )
        _clear_transient_trace()
        if pending_plan is None:
            print(result["messages"][-1].content)
            next_prompt = build_next_turn_prompt(result)
        if pending_plan is not None:
            recorder.pause_run(
                run_id,
                {"reason": pending_plan.status},
            )
            run_paused = True
            continue
        evaluation_status = (result.get("evaluation") or {}).get("status")
        terminal_status = "failed" if evaluation_status == "failed" else "completed"
        recorder.finish_run(
            run_id,
            terminal_status,
            {
                "evaluation_status": evaluation_status,
                "token_usage": active_usage or {},
            },
        )
        run_id = None
        active_usage = None
        if one_shot:
            if (
                _is_auto_session_id(session_id)
                and not args.keep_session
                and evaluation_status != "failed"
            ):
                delete_session(session_id)
                _trace("done", "Removed the successful ephemeral session checkpoint")
            break
    return 0
