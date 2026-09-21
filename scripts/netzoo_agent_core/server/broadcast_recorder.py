"""A trace recorder that also feeds the UI.

Order matters and is not negotiable: the event is written to the hash chain
first, and only an event that is already durable is published.  A UI timeline
that could show entries the trace file does not contain would be worse than no
timeline, because it would look like evidence.
"""

from __future__ import annotations

from collections.abc import Callable

from ..trace_store import LocalTraceStore
from ..tracing import TraceRecorder

__all__ = ["BroadcastTraceRecorder"]


class BroadcastTraceRecorder(TraceRecorder):
    """``TraceRecorder`` plus a best-effort publish of each persisted event."""

    def __init__(self, store: LocalTraceStore, sink: Callable[[dict], None]):
        super().__init__(store)
        self._sink = sink

    def append(self, run_id, event_type, node, payload, **options):
        event = super().append(run_id, event_type, node, payload, **options)
        if event is None:
            return event
        try:
            self._sink(event.model_dump(mode="json"))
        except Exception:
            # Publishing is observability. A broken or slow UI connection must
            # never change the outcome of a planning or execute turn.
            pass
        return event
