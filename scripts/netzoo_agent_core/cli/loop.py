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
    presentation_mode = (
        "verbose"
        if args.verbose
        else "timeline"
        if args.timeline
        else "compact"
        if args.transient_trace
        else "state_machine"
    )
    configure_runtime(
        EXECUTE_TOOLS=False,
        TEST_DATA_MODE=False,
        TRACE_ENABLED=not args.quiet,
        VERBOSE_OUTPUT=args.verbose,
        PRESENTATION_MODE=presentation_mode,
        TRANSIENT_TRACE=(
            args.transient_trace
            and presentation_mode == "compact"
            and not args.quiet
        ),
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
    recorder_factory = None
    if presentation_mode == "state_machine" and not args.quiet:
        # The terminal's step list (step_report.py): each step printed as it finishes, with what it
        # found and on what basis, the way the desktop window shows it.
        from ..presentation import enable_step_report, print_step_lines
        from ..server.broadcast_recorder import broadcast_recorder_factory
        from ..step_report import StepReporter

        enable_step_report()
        recorder_factory = broadcast_recorder_factory(StepReporter(print_step_lines))
    runtime = (bootstrap_runtime(args, memory_runtime, policy, recorder_factory=recorder_factory)
               if recorder_factory else bootstrap_runtime(args, memory_runtime, policy))
    return run_conversation(args, runtime)
