"""CLI application lifecycle and interactive task loop."""

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

from ..contracts import (
    AgentTurnInterrupted,
    ClarificationInputError,
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
from ..graph import build_graph, invoke_graph_turn
from ..llm import validate_response_model, validate_router_model
from ..memory import EpisodeStore, UserProfileStore, _safe_memory_id, compact_episode_payload
from ..policy import ProjectPolicyError, ProjectPolicyLoader
from ..routing import query_web_search_first_url
from ..runtime import configure_runtime
from ..session import (
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
from ..trace_store import LocalTraceStore
from ..trace_sync import TraceSyncWorker
from ..tracing import TraceRecorder
from .clarification import (
    clarification_continuation,
    clarification_prompt,
    parse_clarification_assignments,
    preference_confirmation_prompt,
    preference_continuation,
    resolve_clarification,
)
from .follow_up import (
    build_next_turn_prompt,
    follow_up_declined,
    follow_up_returns_to_main,
    initial_next_turn_prompt,
    render_next_turn_prompt,
    resolve_next_turn_input,
)
from .trace_commands import export_local_trace, local_trace_status

__all__: list[str] = []

def run_cli(args) -> int:
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
            ensure_trace_sync(str(run_id))
        else:
            run_id = str(
                recorder.start_run(session_id=session_id, profile_id=profile_id)
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
            ensure_trace_sync(run_id)
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
