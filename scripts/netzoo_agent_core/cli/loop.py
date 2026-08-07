"""Stable CLI lifecycle coordinator."""

from __future__ import annotations

from ..runtime import configure_runtime
from .bootstrap import bootstrap_memory, bootstrap_runtime, load_project_policy
from .commands import (
    handle_memory_command,
    handle_policy_command,
    handle_preflight_command,
)
from .conversation import run_conversation

__all__: list[str] = []


def run_cli(args) -> int:
    configure_runtime(
        EXECUTE_TOOLS=args.execute,
        TRACE_ENABLED=not args.quiet,
        VERBOSE_OUTPUT=args.verbose,
        TRANSIENT_TRACE=(args.transient_trace and not args.verbose and not args.quiet),
        TOOL_TIMEOUT_SECONDS=args.tool_timeout,
    )
    if (result := handle_preflight_command(args)) is not None:
        return result
    memory_runtime = bootstrap_memory(args)
    if (result := handle_memory_command(args, memory_runtime)) is not None:
        return result
    policy = load_project_policy()
    if (result := handle_policy_command(args, policy)) is not None:
        return result
    runtime = bootstrap_runtime(args, memory_runtime, policy)
    return run_conversation(args, runtime)
