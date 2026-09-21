"""Publishing every event the hash chain accepts.

Order matters and is not negotiable: the event is written to the chain first,
and only an event that is already durable is published. A UI timeline that
could show entries the trace file does not contain would be worse than no
timeline, because it would look like evidence.

The wrapping is at the store, not at the recorder. ``pause_run`` and
``finish_run`` append ``run.paused`` and ``run.finished`` through the store
directly, so a recorder-level wrapper silently dropped them -- a paused run
reached the window one event short of its own trace file.
"""

from __future__ import annotations

from collections.abc import Callable

from ..trace_store import LocalTraceStore
from ..tracing import TraceRecorder

__all__ = ["BroadcastTraceStore", "broadcast_recorder_factory"]


class BroadcastTraceStore(LocalTraceStore):
    """``LocalTraceStore`` that publishes each event it has persisted."""

    def __init__(self, root, sink: Callable[[dict], None]):
        super().__init__(root)
        self._sink = sink

    def append(self, *args, **kwargs):
        event = super().append(*args, **kwargs)
        try:
            self._sink(event.model_dump(mode="json"))
        except Exception:
            # Publishing is observability. A broken or slow UI connection must
            # never change the outcome of a planning or execute turn.
            pass
        return event


def broadcast_recorder_factory(
    sink: Callable[[dict], None],
) -> Callable[[LocalTraceStore], TraceRecorder]:
    """Build the ``recorder_factory`` ``bootstrap_runtime`` expects."""

    def factory(store: LocalTraceStore) -> TraceRecorder:
        return TraceRecorder(BroadcastTraceStore(store.root, sink))

    return factory
