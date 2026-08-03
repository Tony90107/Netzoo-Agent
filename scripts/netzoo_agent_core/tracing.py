"""Small recording interface shared by the CLI and LangGraph nodes."""

from __future__ import annotations

import time
from collections.abc import Callable
from uuid import UUID

from .trace_store import LocalTraceStore, TraceStorageError


__all__ = ["NullTraceRecorder", "TraceRecorder"]


class TraceRecorder:
    """Record run lifecycle and safely bounded node events."""

    def __init__(self, store: LocalTraceStore):
        self.store = store

    def start_run(self, *, session_id: str, profile_id: str) -> UUID:
        run_id = self.store.start_run(
            {"session_id": session_id, "profile_id": profile_id}
        )
        self.append(
            run_id,
            "run.started",
            "cli",
            {"session_id": session_id, "profile_id": profile_id},
        )
        return run_id

    def append(
        self,
        run_id: UUID | str,
        event_type: str,
        node: str,
        payload: dict,
        **options,
    ):
        return self.store.append(
            run_id,
            event_type,
            node,
            payload,
            **options,
        )

    def pause_run(self, run_id: UUID | str, summary: dict):
        return self.store.pause_run(run_id, summary)

    def finish_run(self, run_id: UUID | str, status: str, summary: dict):
        return self.store.finish_run(run_id, status, summary)

    def instrument_node(self, node_name: str, function: Callable) -> Callable:
        """Wrap a graph node without serializing its full input or output state."""

        def instrumented(state: dict):
            run_id = state.get("run_id")
            if not run_id:
                raise TraceStorageError(
                    f"instrumented node '{node_name}' requires a trace run id"
                )
            started = self.append(
                run_id,
                "node.started",
                node_name,
                {"current_step": state.get("current_step")},
            )
            start_ns = time.monotonic_ns()
            try:
                update = function(state)
            except BaseException as error:
                duration_ms = max(0, (time.monotonic_ns() - start_ns) // 1_000_000)
                self.append(
                    run_id,
                    "error.recorded",
                    node_name,
                    {
                        "error_type": type(error).__name__,
                        "message": str(error),
                        "duration_ms": duration_ms,
                    },
                    parent_event_id=started.event_id,
                )
                raise
            duration_ms = max(0, (time.monotonic_ns() - start_ns) // 1_000_000)
            update_keys = sorted(update) if isinstance(update, dict) else []
            self.append(
                run_id,
                "node.finished",
                node_name,
                {
                    "current_step": state.get("current_step"),
                    "duration_ms": duration_ms,
                    "update_keys": update_keys,
                },
                parent_event_id=started.event_id,
            )
            return update

        return instrumented


class NullTraceRecorder:
    """Compatibility recorder for non-task commands and direct legacy tests."""

    def start_run(self, *, session_id: str, profile_id: str):
        return None

    def append(self, *args, **kwargs):
        return None

    def pause_run(self, *args, **kwargs):
        return None

    def finish_run(self, *args, **kwargs):
        return None

    def instrument_node(self, _node_name: str, function: Callable) -> Callable:
        return function
