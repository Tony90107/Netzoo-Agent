"""The conversation tools, without MCP.

Each method here is one tool: it sends at most the messages a window would
send for the same act, and returns one ``TurnResult``. The MCP layer above
only names these methods and describes them to a model; keeping them apart
means they can be driven by a test with a fake worker and no MCP client.

Three rules hold for every session:

* One call at a time. A second call while a turn is running is refused and
  told to wait; it is never queued behind the first.
* Nothing a worker says is dropped. A result that could not be returned stays
  with the session until ``wait`` reads it.
* Execution has its own door. ``ask`` refuses slash commands, so the only way
  to run a plan is ``execute`` with the hash of the plan that was previewed.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import Awaitable, Callable

from ..server.path_mapper import PathMapper, PathOutsideProject
from ..server.protocol import Envelope
from .backend import AgentBackend
from .contracts import ErrorView, TurnResult
from .turn import TurnCollector, view_fields

__all__ = ["NetzooService", "ServiceError"]

ProgressSink = Callable[[str], Awaitable[None]]

_TIMEOUT = object()
_CONTROL_SECONDS = 30.0
"""How long a step that calls no model may take: a mode switch, a decline."""

_SLASH_HELP = (
    "netzoo_ask does not take slash commands. Use netzoo_execute to run a previewed "
    "plan and netzoo_set_mode to switch between planning and test mode."
)


class ServiceError(RuntimeError):
    """A call that could not be attempted; the message is for the model to read."""


@dataclass
class _Session:
    session_id: str
    queue: asyncio.Queue
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    view: Envelope | None = None
    """The question the worker has open."""
    turn: TurnCollector | None = None
    """A turn whose result has not been fully returned."""
    getter: asyncio.Future | None = None
    """A read of ``queue`` that timed out; kept so the item it gets is not lost."""
    closed: bool = False
    resumed: bool = False
    """Reopened from a checkpoint, and no result has said so yet."""
    mode: str = ""
    carried_messages: list[str] = field(default_factory=list)
    carried_notices: list[str] = field(default_factory=list)


class NetzooService:
    def __init__(
        self,
        backend: AgentBackend,
        *,
        execute_enabled: bool = False,
        wait_seconds: float = 45.0,
        start_seconds: float = 120.0,
        mapper: PathMapper | None = None,
    ):
        self.backend = backend
        self.execute_enabled = execute_enabled
        self.wait_seconds = wait_seconds
        self.start_seconds = start_seconds
        self.mapper = mapper or PathMapper.from_environment()
        self._sessions: dict[str, _Session] = {}
        self._opening = asyncio.Lock()

    # -- paths -------------------------------------------------------------

    def to_container_text(self, text: str) -> str:
        """Replace the host's project folder with the container's, where it is written out.

        One fixed prefix is replaced; the sentence is not parsed. The paths that
        result are checked by the agent exactly as typed ones are.
        """
        if not self.mapper.can_translate:
            return text
        host, container = str(self.mapper.host_root), str(self.mapper.container_root)
        if host == container:
            return text
        # Followed by a separator or the end of a path, so a sibling folder
        # whose name merely starts the same way is left alone.
        return re.sub(re.escape(host) + r"(?=/|$|[\s'\"`),;:])", container, text)

    def to_host(self, path: str) -> str:
        try:
            return self.mapper.to_host(path)
        except PathOutsideProject:
            return path

    # -- reading the worker -------------------------------------------------

    async def _next(self, session: _Session, timeout: float):
        if session.getter is None:
            session.getter = asyncio.ensure_future(session.queue.get())
        done, _ = await asyncio.wait({session.getter}, timeout=max(timeout, 0.0))
        if not done:
            return _TIMEOUT
        getter, session.getter = session.getter, None
        return getter.result()

    def _collector(self, session: _Session) -> TurnCollector:
        collector = TurnCollector(
            session.session_id,
            execute_enabled=self.execute_enabled,
            to_host=self.to_host,
            mode=session.mode,
        )
        collector.carry(messages=session.carried_messages, notices=session.carried_notices)
        session.carried_messages, session.carried_notices = [], []
        return collector

    async def _pump(
        self,
        session: _Session,
        wait_seconds: float,
        on_progress: ProgressSink | None = None,
    ) -> TurnResult:
        """Read until the turn ends or the wait runs out; return what there is."""
        collector = session.turn
        loop = asyncio.get_running_loop()
        deadline = loop.time() + wait_seconds
        while not collector.done:
            envelope = await self._next(session, deadline - loop.time())
            if envelope is _TIMEOUT:
                break
            if envelope is None:
                session.closed = True
                collector.close()
                break
            if envelope.type == "view":
                session.view = envelope
                session.mode = str(envelope.payload.get("mode") or session.mode)
            elif envelope.type == "stopped":
                session.closed = True
            elif envelope.type == "progress" and on_progress is not None:
                text = str(envelope.payload.get("text") or "").strip()
                if text:
                    await on_progress(text)
            collector.feed(envelope)
        result = collector.result()
        if collector.done:
            session.turn = None
        return result

    async def _settle(self, session: _Session) -> None:
        """Between turns, take in anything the worker published unasked.

        A refused answer makes the supervisor publish the open question again
        under a new sequence number; the next answer has to quote that one.
        Text that arrives here is kept for the next result rather than dropped.
        """
        while True:
            envelope = await self._next(session, 0.01)
            if envelope is _TIMEOUT:
                return
            if envelope is None:
                session.closed = True
                return
            if envelope.type == "view":
                session.view = envelope
                session.mode = str(envelope.payload.get("mode") or session.mode)
            elif envelope.type == "stopped":
                session.closed = True
            elif envelope.type == "message" and envelope.payload.get("text"):
                session.carried_messages.append(str(envelope.payload["text"]))
            elif envelope.type == "notice" and str(envelope.payload.get("text") or "").strip():
                session.carried_notices.append(str(envelope.payload["text"]))

    def _snapshot(self, session: _Session, *, errors: list[ErrorView] | None = None,
                  status: str | None = None) -> TurnResult:
        """The session as it stands, with no new turn."""
        fields = view_fields(
            session.view.payload if session.view is not None else None,
            execute_enabled=self.execute_enabled,
            to_host=self.to_host,
        )
        fields.setdefault("mode", session.mode)
        result = TurnResult(
            session_id=session.session_id,
            status=status or ("stopped" if session.closed else "waiting_for_user"),
            reply="\n\n".join(session.carried_messages),
            notices=list(session.carried_notices),
            errors=list(errors or []),
            **fields,
        )
        session.carried_messages, session.carried_notices = [], []
        return result

    def _busy(self, session: _Session) -> TurnResult:
        return TurnResult(
            session_id=session.session_id,
            status="running",
            mode=session.mode,
            execute_enabled=self.execute_enabled,
            errors=[
                ErrorView(
                    error_type="TurnInProgress",
                    message=(
                        "This session has a turn that is still running, or whose result has "
                        "not been read. Call netzoo_wait to read it, or netzoo_cancel to stop it."
                    ),
                )
            ],
        )

    def _refused(self, session: _Session, error_type: str, message: str) -> TurnResult:
        return self._snapshot(session, errors=[ErrorView(error_type=error_type, message=message)])

    # -- sessions ------------------------------------------------------------

    async def _open(self, session_id: str, model: str) -> _Session:
        async with self._opening:
            session = self._sessions.get(session_id) if session_id else None
            if session is not None and (session.closed or not self.backend.is_live(session_id)):
                self._forget(session)
                session = None
            if session is None:
                opened = await self.backend.open(session_id=session_id, model=model)
                queue, backlog = self.backend.subscribe(opened, 0)
                for envelope in backlog:
                    queue.put_nowait(envelope)
                session = _Session(session_id=opened, queue=queue)
                self._sessions[opened] = session
        async with session.lock:
            if session.view is None and session.turn is None:
                await self._boot(session)
                # A worker started from a checkpoint is a new process: what it kept is the
                # conversation and the plan, not a mode that was switched on earlier.
                session.resumed = bool(session_id)
        return session

    async def _boot(self, session: _Session) -> None:
        """Wait for the worker's first question; keep anything it said before it."""
        session.turn = self._collector(session)
        result = await self._pump(session, self.start_seconds)
        session.carried_messages = [result.reply] if result.reply else []
        session.carried_notices = list(result.notices)
        if result.status == "waiting_for_user":
            return
        if result.status == "running":
            session.turn = None
            raise ServiceError(
                f"Session {session.session_id} did not become ready within "
                f"{self.start_seconds:.0f} seconds. Try the same call again."
            )
        self._forget(session)
        detail = "; ".join(f"{error.error_type}: {error.message}" for error in result.errors)
        raise ServiceError(f"Session {session.session_id} could not start. {detail}".strip())

    @staticmethod
    def _deliver(session: _Session, result: TurnResult) -> TurnResult:
        """The result a tool returns; the first one after a reopening says so."""
        if session.resumed:
            session.resumed = False
            result.resumed = True
        return result

    def _forget(self, session: _Session) -> None:
        self._sessions.pop(session.session_id, None)
        self.backend.unsubscribe(session.session_id, session.queue)
        if session.getter is not None:
            session.getter.cancel()
            session.getter = None

    def _known(self, session_id: str) -> _Session:
        session = self._sessions.get(session_id)
        if session is None:
            raise ServiceError(
                f"Session {session_id!r} is not running here. Send netzoo_ask with this "
                "session_id to continue a saved session, or without one to start anew."
            )
        return session

    def _send(self, session: _Session, message_type: str, payload: dict | None = None) -> None:
        body = dict(payload or {})
        if session.view is not None:
            body["prompt_seq"] = session.view.seq
        self.backend.send(
            session.session_id,
            Envelope(type=message_type, session_id=session.session_id, payload=body),
        )
        session.turn = self._collector(session)

    async def _ready(self, session: _Session) -> TurnResult | None:
        """A result to return instead of sending, or None when sending is possible."""
        if session.turn is not None:
            return self._busy(session)
        await self._settle(session)
        if session.closed or session.view is None:
            return self._snapshot(
                session,
                status="stopped",
                errors=[
                    ErrorView(
                        error_type="SessionStopped",
                        message="This session has ended. Send netzoo_ask with its session_id to continue it.",
                    )
                ],
            )
        return None

    async def _leave_execution_prompt(self, session: _Session) -> None:
        """Decline an approval left open, so an ordinary message can be taken."""
        if session.view is None or session.view.payload.get("prompt_kind") != "execution_confirmation":
            return
        self._send(session, "decline_execution")
        result = await self._pump(session, _CONTROL_SECONDS)
        if result.reply:
            session.carried_messages.append(result.reply)
        session.carried_notices.extend(result.notices)
        session.turn = None

    # -- tools ---------------------------------------------------------------

    async def ask(
        self,
        message: str,
        *,
        session_id: str = "",
        model: str = "",
        wait_seconds: float | None = None,
        on_progress: ProgressSink | None = None,
    ) -> TurnResult:
        text = message.strip()
        if not text:
            raise ServiceError("message is empty.")
        if text.startswith("/"):
            raise ServiceError(_SLASH_HELP)
        session = await self._open(session_id, model)
        async with session.lock:
            if (refusal := await self._ready(session)) is not None:
                return self._deliver(session, refusal)
            await self._leave_execution_prompt(session)
            self._send(session, "answer", {"text": self.to_container_text(text)})
            return self._deliver(session, await self._pump(session, self._wait(wait_seconds), on_progress))

    async def wait(
        self,
        session_id: str,
        *,
        wait_seconds: float | None = None,
        on_progress: ProgressSink | None = None,
    ) -> TurnResult:
        session = self._known(session_id)
        async with session.lock:
            if session.turn is not None:
                return self._deliver(session, await self._pump(session, self._wait(wait_seconds), on_progress))
            await self._settle(session)
            return self._deliver(session, self._snapshot(session))

    async def set_mode(self, mode: str, *, session_id: str = "", model: str = "") -> TurnResult:
        """Switch mode. Without a session this starts one, so a mode can be set before the first message."""
        command = {"planning": "/planning", "test": "/test"}.get(mode.strip().casefold())
        if command is None:
            raise ServiceError("mode must be 'planning' or 'test'.")
        session = await self._open(session_id, model)
        async with session.lock:
            if (refusal := await self._ready(session)) is not None:
                return self._deliver(session, refusal)
            await self._leave_execution_prompt(session)
            self._send(session, "answer", {"text": command})
            return self._deliver(session, await self._pump(session, _CONTROL_SECONDS))

    async def execute(
        self,
        session_id: str,
        plan_hash: str,
        *,
        wait_seconds: float | None = None,
        on_progress: ProgressSink | None = None,
    ) -> TurnResult:
        if not self.execute_enabled:
            raise ServiceError(
                "Execution is turned off for this server. Set NETZOO_MCP_EXECUTE=on in the "
                "project's .env, or continue this session in the NetZoo desktop app."
            )
        session = self._known(session_id)
        async with session.lock:
            if (refusal := await self._ready(session)) is not None:
                return self._deliver(session, refusal)
            await self._leave_execution_prompt(session)
            view = session.view.payload
            if not view_fields(view, execute_enabled=True)["previewed"]:
                return self._refused(
                    session,
                    "NoPreviewedPlan",
                    "There is no previewed plan to run. Ask for the plan first; a plan can be "
                    "run once its command preview has been shown.",
                )
            if plan_hash != view.get("plan_hash"):
                return self._refused(
                    session,
                    "StalePlanHash",
                    "plan_hash does not name the plan this session is holding. Show the user "
                    "the plan in this result and ask again before approving it.",
                )
            self._send(session, "answer", {"text": "/execute"})
            requested = await self._pump(session, _CONTROL_SECONDS)
            if requested.prompt_kind != "execution_confirmation":
                requested.errors.append(
                    ErrorView(
                        error_type="ExecutionNotOffered",
                        message="The agent did not offer this plan for execution; its notices say why.",
                    )
                )
                return self._deliver(session, requested)
            if requested.reply:
                session.carried_messages.append(requested.reply)
            # The notices of this step only ask for the confirmation that the next line gives
            # ("Confirm below to execute it once."). Carried into the run's result, they read as a
            # question still open after the run has finished, so they are not passed on.
            self._send(session, "approve_execution", {"plan_hash": plan_hash})
            return self._deliver(session, await self._pump(session, self._wait(wait_seconds), on_progress))

    async def cancel(self, session_id: str) -> TurnResult:
        session = self._known(session_id)
        if session.turn is None:
            async with session.lock:
                await self._settle(session)
                return self._deliver(session, self._refused(session, "NothingRunning", "No turn is running in this session."))
        if not self.backend.cancel_turn(session_id):
            raise ServiceError(f"Session {session_id!r} could not be interrupted.")
        async with session.lock:
            if session.turn is None:
                return self._deliver(session, self._snapshot(session))
            return self._deliver(session, await self._pump(session, _CONTROL_SECONDS))

    async def shutdown(self) -> None:
        for session in list(self._sessions.values()):
            self._forget(session)
        await self.backend.shutdown()

    def _wait(self, wait_seconds: float | None) -> float:
        if wait_seconds is None:
            return self.wait_seconds
        return min(max(float(wait_seconds), 1.0), 600.0)
