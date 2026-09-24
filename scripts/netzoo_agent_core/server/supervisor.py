"""Session lifecycle: spawn, fan out, cancel, reap.

The supervisor owns no agent state.  It starts a process per session, copies
JSON between that process and any number of attached clients, and makes sure a
window that is closed does not leave a Python process holding an LLM budget.
"""

from __future__ import annotations

import asyncio
import multiprocessing as mp
import os
import signal
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Protocol

from .protocol import Envelope

__all__ = [
    "SessionHandle",
    "SessionSupervisor",
    "SupervisorError",
    "UnknownSession",
]

HISTORY_LIMIT = 500
DEFAULT_IDLE_TIMEOUT_SECONDS = 30 * 60
_PROMPT_RESPONSE_TYPES = {"answer", "approve_execution", "decline_execution"}
_PROMPT_VALIDATION_ERRORS = {
    "InvalidMessage",
    "UnexpectedMessage",
    "ExecutionApprovalRequired",
    "NoPreviewedPlan",
    "StalePlanHash",
}


class SupervisorError(RuntimeError):
    """A session could not be started or addressed."""


class UnknownSession(SupervisorError):
    """No such live session."""


class WorkerProcess(Protocol):
    """What the supervisor needs from a worker; a real process satisfies it."""

    def start(self) -> None: ...

    def is_alive(self) -> bool: ...

    def join(self, timeout: float | None = None) -> None: ...

    def terminate(self) -> None: ...


@dataclass
class SessionHandle:
    session_id: str
    process: WorkerProcess
    to_worker: object
    from_worker: object
    history: deque = field(default_factory=lambda: deque(maxlen=HISTORY_LIMIT))
    subscribers: set = field(default_factory=set)
    seq: int = 0
    active_prompt_seq: int | None = None
    pending_prompt_seq: int | None = None
    active_view: Envelope | None = None
    last_activity: float = field(default_factory=time.monotonic)
    stopped: bool = False
    pid: int | None = None

    def snapshot(self, since: int) -> list[Envelope]:
        return [envelope for envelope in self.history if envelope.seq > since]


def _default_process_factory(target, args) -> WorkerProcess:
    # spawn keeps the worker free of whatever threads uvicorn has already
    # started; forking a threaded server is a known source of deadlocks.
    context = mp.get_context("spawn")
    return context.Process(target=target, args=args, daemon=True)


def _default_queue_factory():
    return mp.get_context("spawn").Queue()


class SessionSupervisor:
    """Owns every live session process."""

    def __init__(
        self,
        *,
        worker_target=None,
        process_factory=_default_process_factory,
        queue_factory=_default_queue_factory,
        idle_timeout_seconds: float = DEFAULT_IDLE_TIMEOUT_SECONDS,
    ):
        if worker_target is None:
            from .session_worker import worker_main

            worker_target = worker_main
        self._worker_target = worker_target
        self._process_factory = process_factory
        self._queue_factory = queue_factory
        self._idle_timeout = idle_timeout_seconds
        self._sessions: dict[str, SessionHandle] = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        self._reaper: asyncio.Task | None = None

    # -- lifecycle ---------------------------------------------------------

    async def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._reaper = asyncio.create_task(self._reap_idle_sessions())

    async def shutdown(self) -> None:
        if self._reaper is not None:
            self._reaper.cancel()
            try:
                await self._reaper
            except asyncio.CancelledError:
                pass
            self._reaper = None
        for session_id in list(self._sessions):
            await self.close(session_id)

    # -- sessions ----------------------------------------------------------

    def list_sessions(self) -> list[dict]:
        return [
            {
                "session_id": handle.session_id,
                "alive": handle.process.is_alive(),
                "stopped": handle.stopped,
                "seq": handle.seq,
                "idle_seconds": round(time.monotonic() - handle.last_activity, 1),
            }
            for handle in self._sessions.values()
        ]

    def get(self, session_id: str) -> SessionHandle:
        handle = self._sessions.get(session_id)
        if handle is None:
            raise UnknownSession(f"no live session {session_id!r}")
        return handle

    async def create(self, session_id: str, request: dict) -> SessionHandle:
        if session_id in self._sessions:
            raise SupervisorError(f"session {session_id!r} already exists")
        to_worker = self._queue_factory()
        from_worker = self._queue_factory()
        process = self._process_factory(
            self._worker_target,
            ({**request, "session_id": session_id}, to_worker, from_worker),
        )
        handle = SessionHandle(
            session_id=session_id,
            process=process,
            to_worker=to_worker,
            from_worker=from_worker,
        )
        self._sessions[session_id] = handle
        process.start()
        handle.pid = getattr(process, "pid", None)
        threading.Thread(
            target=self._pump,
            args=(handle,),
            name=f"netzoo-session-{session_id}",
            daemon=True,
        ).start()
        return handle

    async def close(self, session_id: str) -> None:
        handle = self._sessions.pop(session_id, None)
        if handle is None:
            return
        try:
            handle.to_worker.put(
                Envelope(type="cancel", session_id=session_id).to_json()
            )
        except Exception:
            pass
        await asyncio.get_running_loop().run_in_executor(
            None, handle.process.join, 5.0
        )
        if handle.process.is_alive():
            handle.process.terminate()
        for subscriber in list(handle.subscribers):
            subscriber.put_nowait(None)

    # -- messaging ---------------------------------------------------------

    def send(self, session_id: str, envelope: Envelope) -> None:
        handle = self.get(session_id)
        handle.last_activity = time.monotonic()
        if envelope.type in _PROMPT_RESPONSE_TYPES:
            prompt_seq = envelope.payload.get("prompt_seq")
            stale = (
                prompt_seq is not None and prompt_seq != handle.active_prompt_seq
            ) or (
                prompt_seq is None
                and handle.active_prompt_seq is None
                and handle.pending_prompt_seq is not None
            )
            if stale:
                self._publish(
                    handle,
                    Envelope(
                        type="error",
                        session_id=session_id,
                        payload={
                            "error_type": "StalePromptSeq",
                            "message": (
                                "This response belongs to an older prompt. "
                                "Use the current question and try again."
                            ),
                        },
                    ),
                )
                if handle.active_prompt_seq is not None and handle.active_view is not None:
                    # A client with an out-of-date view has just cleared its
                    # input. Replay the current question under a fresh sequence
                    # so it can recover without answering the wrong prompt.
                    self._publish(handle, handle.active_view)
                return
            handle.pending_prompt_seq = handle.active_prompt_seq
            handle.active_prompt_seq = None
        handle.to_worker.put(envelope.to_json())

    def cancel_turn(self, session_id: str) -> bool:
        """Interrupt a running turn.

        A worker inside ``app.invoke()`` is not reading the channel, so the
        only way in is the signal the agent already handles: SIGINT raises
        ``AgentTurnInterrupted`` and the turn is recorded as interrupted rather
        than completed.
        """
        handle = self.get(session_id)
        if handle.pid is None or not handle.process.is_alive():
            return False
        try:
            os.kill(handle.pid, signal.SIGINT)
        except (ProcessLookupError, PermissionError):
            return False
        return True

    def subscribe(self, session_id: str, since: int = 0) -> tuple[asyncio.Queue, list]:
        handle = self.get(session_id)
        subscriber: asyncio.Queue = asyncio.Queue()
        handle.subscribers.add(subscriber)
        return subscriber, handle.snapshot(since)

    def unsubscribe(self, session_id: str, subscriber: asyncio.Queue) -> None:
        handle = self._sessions.get(session_id)
        if handle is not None:
            handle.subscribers.discard(subscriber)

    # -- internals ---------------------------------------------------------

    def _pump(self, handle: SessionHandle) -> None:
        """Move worker output onto the event loop.  Runs on its own thread."""
        while True:
            try:
                raw = handle.from_worker.get()
            except (EOFError, OSError):
                break
            if raw is None:
                break
            loop = self._loop
            if loop is None:
                break
            try:
                envelope = Envelope.from_json(raw)
            except Exception:
                # A worker that cannot speak the protocol is a bug, but it must
                # not take the pump thread down with it.
                continue
            loop.call_soon_threadsafe(self._publish, handle, envelope)
            if envelope.type == "stopped":
                break
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._mark_stopped, handle)

    def _publish(self, handle: SessionHandle, envelope: Envelope) -> None:
        handle.seq += 1
        envelope = envelope.model_copy(update={"seq": handle.seq})
        refresh_prompt = False
        if envelope.type == "view":
            handle.active_prompt_seq = envelope.seq
            handle.pending_prompt_seq = None
            handle.active_view = envelope
        elif envelope.type == "error" and (
            envelope.payload.get("error_type") in _PROMPT_VALIDATION_ERRORS
            and handle.pending_prompt_seq is not None
        ):
            # The worker rejected the action but kept the prompt open. Reissue
            # it below with a fresh sequence so the client can retry safely.
            handle.active_prompt_seq = handle.pending_prompt_seq
            handle.pending_prompt_seq = None
            refresh_prompt = True
        handle.history.append(envelope)
        handle.last_activity = time.monotonic()
        for subscriber in list(handle.subscribers):
            subscriber.put_nowait(envelope)
        if refresh_prompt and handle.active_view is not None:
            self._publish(handle, handle.active_view)

    def _mark_stopped(self, handle: SessionHandle) -> None:
        handle.stopped = True
        for subscriber in list(handle.subscribers):
            subscriber.put_nowait(None)

    async def _reap_idle_sessions(self) -> None:
        while True:
            await asyncio.sleep(60)
            deadline = time.monotonic() - self._idle_timeout
            for session_id, handle in list(self._sessions.items()):
                if handle.last_activity < deadline:
                    await self.close(session_id)
                elif (handle.stopped or not handle.process.is_alive()) and not handle.subscribers:
                    # Finished sessions stay addressable while a client is
                    # still reading their tail, and are reaped once nobody is.
                    await self.close(session_id)
