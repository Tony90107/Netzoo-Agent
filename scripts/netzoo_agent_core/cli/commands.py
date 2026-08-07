"""Immediate CLI commands that finish before Graph startup."""

from __future__ import annotations

import json
from pathlib import Path

from ..contracts.policy import ProjectPolicySnapshot
from ..routing import query_web_search_first_url
from ..session import cleanup_runtime_storage, cleanup_trace_storage
from .bootstrap import MemoryRuntime
from .trace_commands import export_local_trace, local_trace_status

__all__: list[str] = []


def handle_preflight_command(args) -> int | None:
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
    return None


def handle_memory_command(args, runtime: MemoryRuntime) -> int | None:
    profile_id = runtime.profile_id
    profile_store = runtime.profile_store
    episode_store = runtime.episode_store

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
        from ..memory import compact_episode_payload

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
    return None


def handle_policy_command(
    args,
    policy: ProjectPolicySnapshot,
) -> int | None:
    if not args.policy_status:
        return None
    print(
        json.dumps(
            {
                "project": policy.project,
                "policy_version": policy.policy_version,
                "policy_hash": policy.policy_hash,
                "agents_path": policy.agents_path,
                "workflow_spec_dir": policy.workflow_spec_dir,
                "workflows": sorted(policy.workflows),
                "code_enforced": True,
            },
            indent=2,
        )
    )
    return 0
