"""The worker/daemon boundary.

Only JSON strings cross it.  That is deliberate: the worker holds live graph
objects, open trace files, and a mutable process-wide runtime, and none of
that may leak into the daemon by being accidentally picklable.
"""

from __future__ import annotations

import queue
from typing import Protocol

from .protocol import Envelope

__all__ = ["Channel", "ClosedChannel", "QueueChannel", "local_channel_pair"]


class ClosedChannel(RuntimeError):
    """Raised when the peer has gone away."""


class Channel(Protocol):
    """Bidirectional, line-oriented transport for envelopes."""

    def send(self, envelope: Envelope) -> None: ...

    def receive(self, timeout: float | None = None) -> Envelope | None:
        """Return the next envelope, or None if ``timeout`` elapsed first."""


class QueueChannel:
    """A channel over two queues, one per direction.

    Works unchanged with ``queue.Queue`` (tests, in-process drivers) and
    ``multiprocessing.Queue`` (the real worker), because the payload is always
    a plain JSON string.
    """

    def __init__(self, inbox, outbox):
        self._inbox = inbox
        self._outbox = outbox
        self._closed = False

    def send(self, envelope: Envelope) -> None:
        if self._closed:
            raise ClosedChannel("channel is closed")
        self._outbox.put(envelope.to_json())

    def receive(self, timeout: float | None = None) -> Envelope | None:
        try:
            raw = self._inbox.get(timeout=timeout) if timeout else self._inbox.get()
        except queue.Empty:
            return None
        if raw is None:
            raise ClosedChannel("peer closed the channel")
        return Envelope.from_json(raw)

    def close(self) -> None:
        self._closed = True
        try:
            self._outbox.put(None)
        except Exception:
            # A closed or broken peer queue is the normal shutdown race; the
            # supervisor reaps the process either way.
            return


def local_channel_pair() -> tuple[QueueChannel, QueueChannel]:
    """Two connected in-process channels, for driving a worker under test."""
    to_worker: queue.Queue = queue.Queue()
    from_worker: queue.Queue = queue.Queue()
    worker_side = QueueChannel(to_worker, from_worker)
    client_side = QueueChannel(from_worker, to_worker)
    return client_side, worker_side
