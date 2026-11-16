"""Where the agent runs, as seen from the MCP tools.

The tools need five things from an agent: open a session, send it a message,
read what it publishes, interrupt it, and close it. ``AgentBackend`` is that
list. ``EmbeddedBackend`` meets it with a ``SessionSupervisor`` in this
process, which is the whole deployment today: the MCP server runs inside the
container and owns its workers.

A backend that reaches the desktop daemon over its socket would meet the same
list, and the tools would not change. None is written, because nothing needs
one yet.
"""

from __future__ import annotations

import asyncio
from typing import Callable, Protocol

from ..server import history
from ..server.protocol import Envelope
from ..server.session_open import SessionRequest, open_session
from ..server.supervisor import SessionSupervisor, SupervisorError, UnknownSession

__all__ = ["MCP_TAG", "AgentBackend", "BackendError", "EmbeddedBackend"]

MCP_TAG = "mcp"
"""Marks a session started here, so the desktop history can tell it apart."""


class BackendError(RuntimeError):
    """The agent could not be reached or a session could not be opened."""


class AgentBackend(Protocol):
    async def start(self) -> None: ...

    async def shutdown(self) -> None: ...

    async def open(self, *, session_id: str = "", model: str = "") -> str:
        """Start a session, or continue the saved one named; return its id."""

    def is_live(self, session_id: str) -> bool: ...

    def subscribe(self, session_id: str, since: int = 0) -> tuple[asyncio.Queue, list[Envelope]]: ...

    def unsubscribe(self, session_id: str, subscriber: asyncio.Queue) -> None: ...

    def send(self, session_id: str, envelope: Envelope) -> None: ...

    def cancel_turn(self, session_id: str) -> bool: ...

    async def close(self, session_id: str) -> None: ...


def _environment_problem() -> str | None:
    from ..server.session_worker import worker_environment_error

    return worker_environment_error()


class EmbeddedBackend:
    """The supervisor, in this process."""

    def __init__(
        self,
        supervisor: SessionSupervisor | None = None,
        *,
        preflight: Callable[[], str | None] = _environment_problem,
    ):
        self._supervisor = supervisor or SessionSupervisor()
        self._preflight = preflight

    async def start(self) -> None:
        await self._supervisor.start()

    async def shutdown(self) -> None:
        await self._supervisor.shutdown()

    def is_live(self, session_id: str) -> bool:
        return any(
            item["session_id"] == session_id and item["alive"] and not item["stopped"]
            for item in self._supervisor.list_sessions()
        )

    async def open(self, *, session_id: str = "", model: str = "") -> str:
        if session_id and self.is_live(session_id):
            return session_id
        if session_id and not history.has_checkpoint(session_id):
            # has_checkpoint is also what refuses anything that is not a bare id.
            raise BackendError(
                f"There is no saved session {session_id!r}. Leave session_id out to start a new one."
            )
        if (problem := self._preflight()) is not None:
            raise BackendError(problem)
        request = (
            SessionRequest(resume=session_id, model=model)
            if session_id
            else SessionRequest(model=model, tags=[MCP_TAG])
        )
        try:
            opened = await open_session(self._supervisor, request)
        except SupervisorError as error:
            raise BackendError(str(error)) from error
        return opened["session_id"]

    def subscribe(self, session_id: str, since: int = 0) -> tuple[asyncio.Queue, list[Envelope]]:
        try:
            return self._supervisor.subscribe(session_id, since)
        except UnknownSession as error:
            raise BackendError(str(error)) from error

    def unsubscribe(self, session_id: str, subscriber: asyncio.Queue) -> None:
        self._supervisor.unsubscribe(session_id, subscriber)

    def send(self, session_id: str, envelope: Envelope) -> None:
        try:
            self._supervisor.send(session_id, envelope)
        except UnknownSession as error:
            raise BackendError(str(error)) from error

    def cancel_turn(self, session_id: str) -> bool:
        try:
            return self._supervisor.cancel_turn(session_id)
        except UnknownSession:
            return False

    async def close(self, session_id: str) -> None:
        await self._supervisor.close(session_id)
