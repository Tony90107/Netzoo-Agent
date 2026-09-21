"""One session, one process.

``EXECUTE_TOOLS``, ``TEST_DATA_MODE`` and the twelve other names in
``runtime.MUTABLE_RUNTIME_NAMES`` are process-wide.  Two sessions sharing a
process would share them, so approving execution in one window would hand
execution authority to every other window for the duration of that turn.
Making them per-invocation would mean touching every graph node; giving each
session its own process costs a few tens of MB and changes no agent semantics.
That is the trade this module encodes.
"""

from __future__ import annotations

import os
import sys
from contextlib import redirect_stdout

from .channel import QueueChannel
from .protocol import Envelope

__all__ = ["worker_environment_error", "worker_main"]


def worker_main(request: dict, inbox, outbox) -> int:
    """Process entry point.  Never raises into multiprocessing."""
    channel = QueueChannel(inbox, outbox)
    try:
        return _run(request, channel)
    except BaseException as error:  # noqa: BLE001 - the boundary must hold
        try:
            channel.send(
                Envelope(
                    type="error",
                    session_id=str(request.get("session_id") or ""),
                    payload={
                        "error_type": type(error).__name__,
                        "message": str(error),
                    },
                )
            )
            channel.send(
                Envelope(
                    type="stopped",
                    session_id=str(request.get("session_id") or ""),
                    payload={"exit_code": 1},
                )
            )
        except Exception:
            pass
        return 1


def _run(request: dict, channel: QueueChannel) -> int:
    # Imported here so an import failure is reported over the channel as a
    # session error rather than killing the process before it can speak.
    from ..cli.arguments import parse_args
    from ..cli.bootstrap import bootstrap_memory, bootstrap_runtime, load_project_policy
    from ..engine import ConversationMachine
    from ..runtime import configure_runtime
    from .broadcast_recorder import broadcast_recorder_factory
    from .driver import ProgressWriter, WorkerDriver

    # A worker takes its settings from the session request, not from the
    # daemon's command line, which it would otherwise inherit.
    sys.argv = sys.argv[:1]
    args = parse_args()
    args.task = None
    if request.get("session_id"):
        args.session = request["session_id"]
    if request.get("resume"):
        args.resume = request["resume"]
    if request.get("profile"):
        args.profile = request["profile"]
    if request.get("model"):
        args.model = request["model"]

    configure_runtime(
        EXECUTE_TOOLS=False,
        TEST_DATA_MODE=False,
        TRACE_ENABLED=True,
        VERBOSE_OUTPUT=False,
        PRESENTATION_MODE="state_machine",
        TRANSIENT_TRACE=False,
        TOOL_TIMEOUT_SECONDS=args.tool_timeout,
    )

    session_id = str(request.get("session_id") or "")

    def publish_trace(event: dict) -> None:
        channel.send(
            Envelope(type="trace", session_id=session_id, payload=event)
        )

    recorder_factory = broadcast_recorder_factory(publish_trace)

    memory_runtime = bootstrap_memory(args)
    policy = load_project_policy()
    runtime = bootstrap_runtime(
        args,
        memory_runtime,
        policy,
        recorder_factory=recorder_factory,
    )
    machine = ConversationMachine(args, runtime)
    writer = ProgressWriter(
        lambda line: channel.send(
            Envelope(
                type="progress",
                session_id=runtime.session_id,
                payload={"text": line},
            )
        )
    )
    driver = WorkerDriver(
        machine,
        channel,
        session_id=runtime.session_id,
        progress=writer,
    )
    # Process-wide, because ``sys.stdout`` is. This process exists to serve one
    # session, so capturing all of its stdout is exactly the intent.
    with redirect_stdout(writer):
        return driver.run()


def worker_environment_error() -> str | None:
    """The one precondition worth reporting before a process is spawned."""
    if not os.environ.get("OPENROUTER_API_KEY"):
        return (
            "Missing OPENROUTER_API_KEY. The daemon container needs it in its "
            "environment before a session can start."
        )
    return None
