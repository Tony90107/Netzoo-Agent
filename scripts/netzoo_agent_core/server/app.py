"""The local daemon.

Bound to loopback, single user, one bearer token generated per launch by the
desktop shell.  It is not an internet service and must never be exposed as
one: it starts processes that can run analyses and spend an LLM budget.
"""

from __future__ import annotations

import asyncio
import os
import secrets
import uuid
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.websockets import WebSocketDisconnect

from . import activity, files, history
from ..environment import environment_report
from ..session_meta import set_details, set_tags
from .path_mapper import PathMapper, PathOutsideProject
from .protocol import PROTOCOL_VERSION, ClientMessage, Envelope
from .supervisor import SessionSupervisor, SupervisorError, UnknownSession

__all__ = ["DESKTOP_ORIGINS", "WS_TOKEN_SUBPROTOCOL", "create_app", "resolve_token"]

# Browsers cannot set an Authorization header on a WebSocket, and a token in
# the query string is written verbatim into the uvicorn access log, where
# `docker logs` keeps it. The subprotocol header carries it instead: it is
# not logged, and it is the mechanism the WebSocket protocol provides for
# exactly this.
WS_TOKEN_SUBPROTOCOL = "netzoo.bearer"

# The window is a browser, so its requests are cross-origin: a packaged Tauri
# app is `tauri://localhost` (`http://tauri.localhost` on Windows) and the Vite
# dev server is `http://localhost:5173`. Without these the webview can start
# the container over IPC and then never be allowed to talk to it.
#
# This is not a loosening: the daemon is bound to loopback and every route
# except /health still requires the bearer token. Credentials are deliberately
# not allowed, so a stray page cannot ride along on an ambient cookie.
DESKTOP_ORIGINS = (
    "tauri://localhost",
    "http://tauri.localhost",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


class SessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(default="", max_length=64)
    profile: str = Field(default="", max_length=64)
    model: str = Field(default="", max_length=200)
    resume: str = Field(default="", max_length=64)
    tags: list[str] = Field(default_factory=list, max_length=12)
    name: str = Field(default="", max_length=200)


class TagsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tags: list[str] = Field(default_factory=list, max_length=24)


class DetailsRequest(BaseModel):
    """A session's name and notes; a field left out is kept, "" clears it."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=8000)


def resolve_token() -> tuple[str, bool]:
    """Return the daemon token and whether it had to be generated."""
    configured = os.environ.get("NETZOO_DESKTOP_TOKEN", "").strip()
    if configured:
        return configured, False
    return secrets.token_urlsafe(32), True


def create_app(*, token: str, supervisor: SessionSupervisor | None = None) -> FastAPI:
    supervisor = supervisor or SessionSupervisor()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        await supervisor.start()
        try:
            yield
        finally:
            await supervisor.shutdown()

    app = FastAPI(
        title="NetZoo Agent Daemon",
        version="1.0.0",
        docs_url=None,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(DESKTOP_ORIGINS),
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["authorization", "content-type"],
    )
    app.state.supervisor = supervisor
    app.state.token = token

    def _authorized(candidate: str | None) -> bool:
        return bool(candidate) and secrets.compare_digest(candidate, token)

    def require_token(request: Request) -> None:
        header = request.headers.get("authorization", "")
        scheme, _, value = header.partition(" ")
        if scheme.casefold() != "bearer" or not _authorized(value.strip()):
            raise HTTPException(status_code=401, detail="unauthorized")

    @app.exception_handler(UnknownSession)
    async def _unknown_session(_request: Request, error: UnknownSession):
        return JSONResponse({"detail": str(error)}, status_code=404)

    @app.exception_handler(files.OutsideRoot)
    async def _outside_root(_request: Request, error: files.OutsideRoot):
        return JSONResponse({"detail": str(error)}, status_code=403)

    @app.exception_handler(files.FileChanged)
    async def _file_changed(_request: Request, error: files.FileChanged):
        return JSONResponse({"detail": str(error)}, status_code=409)

    @app.exception_handler(files.PreviewInvalid)
    async def _preview_invalid(_request: Request, error: files.PreviewInvalid):
        return JSONResponse({"detail": str(error)}, status_code=400)

    @app.exception_handler(FileNotFoundError)
    async def _file_missing(_request: Request, _error: FileNotFoundError):
        return JSONResponse({"detail": "This output no longer exists. Refresh the directory."}, status_code=404)

    @app.exception_handler(SupervisorError)
    async def _supervisor_error(_request: Request, error: SupervisorError):
        return JSONResponse({"detail": str(error)}, status_code=409)

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "protocol": PROTOCOL_VERSION,
            "sessions": len(supervisor.list_sessions()),
        }

    @app.get("/v1/sessions")
    def list_sessions(_scope: None = Depends(require_token)) -> dict:
        return {"sessions": supervisor.list_sessions()}

    @app.post("/v1/sessions", status_code=201)
    async def create_session(
        request: SessionRequest,
        _scope: None = Depends(require_token),
    ) -> dict:
        # Resuming continues a saved session under its own id, as `--resume`
        # does in the terminal, so its name, notes, tags and output folder stay
        # one experiment. A worker still running it is attached to instead,
        # the way a reconnect is; one that has stopped is replaced.
        resumed = request.resume if not request.session_id and history.has_checkpoint(request.resume) else ""
        if resumed:
            live = next((item for item in supervisor.list_sessions() if item["session_id"] == resumed), None)
            if live and live["alive"] and not live["stopped"]:
                return {"session_id": resumed, "tags": history.session_details(resumed)["tags"], "attached": True}
            if live:
                await supervisor.close(resumed)
        session_id = request.session_id or resumed or uuid.uuid4().hex[:8]
        await supervisor.create(
            session_id,
            {
                key: value
                for key, value in request.model_dump().items()
                if value and key not in {"session_id", "tags", "name"}
            },
        )
        tags = set_tags(session_id, request.tags, sessions_root=history.SESSION_ROOT) if request.tags else []
        name = (set_details(session_id, name=request.name, sessions_root=history.SESSION_ROOT)["name"]
                if request.name.strip() else "")
        return {"session_id": session_id, "tags": tags, "name": name}

    @app.delete("/v1/sessions/{session_id}", status_code=204)
    async def delete_session(
        session_id: str,
        _scope: None = Depends(require_token),
    ) -> None:
        await supervisor.close(session_id)

    mapper = PathMapper.from_environment()

    @app.get("/v1/files")
    def browse(
        path: str = Query(default="", max_length=1024),
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=200),
        _scope: None = Depends(require_token),
    ) -> dict:
        listing = files.list_directory(path, offset=offset, limit=limit)
        return {
            "path": listing.path,
            "host_path": _host(listing.path),
            "total": listing.total,
            "offset": listing.offset,
            "limit": listing.limit,
            "has_more": listing.has_more,
            "entries": [
                {
                    "name": entry.name,
                    "path": entry.path,
                    "kind": entry.kind,
                    "size_bytes": entry.size_bytes,
                    "modified_at": entry.modified_at,
                }
                for entry in listing.entries
            ],
        }

    @app.get("/v1/files/preview")
    def file_preview(
        path: str = Query(max_length=1024),
        offset: int = Query(default=0, ge=0, le=9_007_199_254_740_991),
        version: str = Query(default="", max_length=100),
        _scope: None = Depends(require_token),
    ) -> dict:
        result = files.preview(path, offset=offset, version=version)
        return {
            "path": result.path,
            "host_path": _host(result.path),
            "kind": result.kind,
            "size_bytes": result.size_bytes,
            "truncated": result.truncated,
            "columns": result.columns,
            "rows": result.rows,
            "text": result.text,
            "arrays": result.arrays,
            "note": result.note,
            "offset": result.offset,
            "next_offset": result.next_offset,
            "version": result.version,
            "total_columns": result.total_columns,
        }

    def _host(relative: str) -> str:
        """The path as the user would find it, when the shell said where.

        Falls back to the container path rather than guessing: a wrong host
        path is worse than an honest one the user has to translate.
        """
        try:
            return mapper.to_host(relative)
        except PathOutsideProject:
            return relative

    @app.get("/v1/history")
    def session_history(
        limit: int = Query(default=history.DEFAULT_LIMIT, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
        query: str = Query(default="", max_length=200),
        status: Literal["all", "needs_input", "needs_confirmation", "completed", "failed", "dry_run"] = "all",
        tag: str = Query(default="", max_length=40),
        _scope: None = Depends(require_token),
    ) -> dict:
        page = history.list_sessions(limit=limit + 1, offset=offset, query=query, status=status, tag=tag)
        items = page[:limit]
        return {
            "offset": offset,
            "has_more": len(page) > limit,
            "next_offset": offset + len(items) if len(page) > limit else None,
            "sessions": [
                {
                    "session_id": item.session_id,
                    "profile_id": item.profile_id,
                    "updated_at": item.updated_at,
                    "auto_generated": item.auto_generated,
                    "workflow": item.workflow,
                    "status": item.status,
                    "resumable": item.resumable,
                    "title": item.title,
                    "name": item.name,
                    "notes_preview": item.notes.split("\n", 1)[0][:120],
                    "total_tokens": item.total_tokens,
                    "tags": list(item.tags),
                    "models": item.models or {},
                    "outputs": list(item.outputs)[:20],
                    "output_count": len(item.outputs),
                    "output_dir": item.output_dir,
                }
                for item in items
            ]
        }

    @app.get("/v1/tags")
    def all_tags(_scope: None = Depends(require_token)) -> dict:
        return {"tags": history.tag_counts()}

    @app.post("/v1/history/{session_id}/tags")
    def replace_tags(
        session_id: str,
        request: TagsRequest,
        _scope: None = Depends(require_token),
    ) -> dict:
        live = any(item["session_id"] == session_id for item in supervisor.list_sessions())
        try:
            tags = (set_tags(session_id, request.tags, sessions_root=history.SESSION_ROOT) if live
                    else history.update_tags(session_id, request.tags))
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="no such session") from error
        return {"session_id": session_id, "tags": tags}

    @app.get("/v1/history/{session_id}/details")
    def details(
        session_id: str,
        _scope: None = Depends(require_token),
    ) -> dict:
        try:
            return history.session_details(session_id)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/v1/history/{session_id}/details")
    def replace_details(
        session_id: str,
        request: DetailsRequest,
        _scope: None = Depends(require_token),
    ) -> dict:
        live = any(item["session_id"] == session_id for item in supervisor.list_sessions())
        try:
            saved = (set_details(session_id, name=request.name, notes=request.notes,
                                 sessions_root=history.SESSION_ROOT) if live
                     else history.update_details(session_id, name=request.name, notes=request.notes))
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="no such session") from error
        return {"session_id": session_id, **saved}

    @app.get("/v1/outputs/sessions")
    def outputs_by_session(_scope: None = Depends(require_token)) -> dict:
        return history.outputs_by_session()

    @app.get("/v1/outputs/provenance")
    def provenance(
        path: str = Query(max_length=1024),
        _scope: None = Depends(require_token),
    ) -> dict:
        return {"path": path, "sessions": history.output_provenance(path)}

    @app.get("/v1/compare")
    def compare(
        ids: str = Query(max_length=600),
        _scope: None = Depends(require_token),
    ) -> dict:
        try:
            wanted = [item for item in ids.split(",") if item]
            return {"sessions": history.compare_sessions(wanted)}
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.get("/v1/history/{session_id}")
    def session_transcript(
        session_id: str,
        _scope: None = Depends(require_token),
    ) -> dict:
        try:
            transcript = history.read_transcript(session_id)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        if transcript is None:
            raise HTTPException(status_code=404, detail="no such session")
        return {
            "session_id": transcript.session_id,
            "status": transcript.status,
            "workflow": transcript.workflow,
            "resumable": transcript.resumable,
            "messages": transcript.messages,
            "truncated": transcript.truncated,
            "title": transcript.title,
            "name": transcript.name,
            "notes": transcript.notes,
            "tags": list(transcript.tags),
            "models": transcript.models or {},
            "outputs": list(transcript.outputs),
            "output_dir": transcript.output_dir,
        }

    @app.get("/v1/history/{session_id}/activity")
    def saved_runs(
        session_id: str,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=100),
        _scope: None = Depends(require_token),
    ) -> dict:
        try:
            return activity.list_runs(session_id, offset=offset, limit=limit)
        except ValueError as error:
            raise HTTPException(400, str(error)) from error

    @app.get("/v1/history/{session_id}/activity/{run_id}")
    def saved_events(
        session_id: str, run_id: str,
        after_sequence: int = Query(default=0, ge=0),
        limit: int = Query(default=200, ge=1, le=200),
        version: str = Query(default="", max_length=100),
        _scope: None = Depends(require_token),
    ) -> dict:
        try:
            return activity.read_events(session_id, run_id, after_sequence=after_sequence, limit=limit, version=version)
        except ValueError as error:
            raise HTTPException(400, str(error)) from error

    @app.get("/v1/environment")
    def environment(_scope: None = Depends(require_token)) -> dict:
        return environment_report()

    @app.get("/v1/settings")
    def effective_settings(_scope: None = Depends(require_token)) -> dict:
        # Read-only on purpose: the allowlists and the token budget are what
        # stop a stray request reaching an expensive model.
        return history.describe_settings()

    @app.post("/v1/sessions/{session_id}/cancel")
    def cancel_turn(
        session_id: str,
        _scope: None = Depends(require_token),
    ) -> dict:
        return {"interrupted": supervisor.cancel_turn(session_id)}

    @app.websocket("/ws/session/{session_id}")
    async def session_socket(
        websocket: WebSocket,
        session_id: str,
        since: int = Query(default=0, ge=0),
    ) -> None:
        supplied, subprotocol = _websocket_credentials(websocket)
        if not _authorized(supplied):
            await websocket.close(code=4401)
            return
        try:
            subscriber, backlog = supervisor.subscribe(session_id, since)
        except UnknownSession:
            await websocket.close(code=4404)
            return
        await websocket.accept(subprotocol=subprotocol)
        try:
            for envelope in backlog:
                await websocket.send_text(envelope.to_json())
            await _relay(websocket, supervisor, session_id, subscriber)
        except WebSocketDisconnect:
            pass
        finally:
            supervisor.unsubscribe(session_id, subscriber)

    return app


def _websocket_credentials(websocket: WebSocket) -> tuple[str, str | None]:
    """Read the bearer token from a header, or from the subprotocol.

    Non-browser clients keep using Authorization. A browser offers
    ``[WS_TOKEN_SUBPROTOCOL, <token>]``, and the accepted subprotocol has to be
    echoed back or the handshake fails.
    """
    header = websocket.headers.get("authorization", "")
    scheme, _, value = header.partition(" ")
    if scheme.casefold() == "bearer" and value.strip():
        return value.strip(), None
    offered = list(websocket.scope.get("subprotocols") or [])
    if len(offered) >= 2 and offered[0] == WS_TOKEN_SUBPROTOCOL:
        return offered[1], WS_TOKEN_SUBPROTOCOL
    return "", None


async def _relay(websocket, supervisor, session_id, subscriber) -> None:
    async def outbound() -> None:
        while True:
            envelope = await subscriber.get()
            if envelope is None:
                await websocket.close(code=1000)
                return
            await websocket.send_text(envelope.to_json())

    async def inbound() -> None:
        while True:
            raw = await websocket.receive_text()
            try:
                envelope = Envelope.from_json(raw)
                message = ClientMessage.from_envelope(envelope)
            except Exception as error:
                await websocket.send_text(
                    Envelope(
                        type="error",
                        session_id=session_id,
                        payload={
                            "error_type": "InvalidMessage",
                            "message": str(error),
                        },
                    ).to_json()
                )
                continue
            if message.type == "ping":
                await websocket.send_text(
                    Envelope(type="pong", session_id=session_id).to_json()
                )
                continue
            supervisor.send(session_id, envelope)

    outbound_task = asyncio.create_task(outbound())
    inbound_task = asyncio.create_task(inbound())
    done, pending = await asyncio.wait(
        {outbound_task, inbound_task},
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()
    for task in done:
        if (error := task.exception()) and not isinstance(error, WebSocketDisconnect):
            raise error
