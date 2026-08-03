"""FastAPI collector for Agent uploads and read-only browser sharing."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, AsyncIterator, Literal
from urllib.parse import quote
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from .blob_store import BlobStore
from .contracts import EventBatch, RunCreate, ShareGrant
from .repository import (
    BlobRecord,
    DigestConflictError,
    ObserverRepository,
    RunConflictError,
    RunNotFoundError,
    SequenceGapError,
    ShareAccessError,
)
from .settings import CollectorSettings


SHARE_COOKIE = "netzoo_share_session"


class ShareCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expires_in_seconds: int = Field(default=604_800, ge=60, le=2_592_000)


class ShareExchangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    share_id: UUID
    token: str = Field(min_length=32, max_length=256)


def _bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def _matches(candidate: str, expected: str) -> bool:
    return hmac.compare_digest(candidate.encode("utf-8"), expected.encode("utf-8"))


def create_app(
    settings: CollectorSettings,
    repository: ObserverRepository,
    blob_store: BlobStore,
) -> FastAPI:
    app = FastAPI(title="NetZoo Trace Observer", version="1.0.0", docs_url=None)
    pepper = settings.credential_pepper.get_secret_value()
    agent_key = settings.agent_key.get_secret_value()
    admin_key = settings.admin_key.get_secret_value()

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_blob_bytes:
            return JSONResponse(status_code=413, content={"detail": "request too large"})
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'none'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    def require_agent(request: Request) -> None:
        token = _bearer_token(request)
        if token is None:
            raise HTTPException(status_code=401, detail="agent credential required")
        if _matches(token, admin_key):
            raise HTTPException(status_code=403, detail="admin credential has no agent scope")
        if not _matches(token, agent_key):
            raise HTTPException(status_code=401, detail="invalid agent credential")

    def require_admin(request: Request) -> None:
        token = _bearer_token(request)
        if token is None:
            raise HTTPException(status_code=401, detail="admin credential required")
        if _matches(token, agent_key):
            raise HTTPException(status_code=403, detail="agent credential has no admin scope")
        if not _matches(token, admin_key):
            raise HTTPException(status_code=401, detail="invalid admin credential")

    def require_share(request: Request, run_id: UUID) -> None:
        if _bearer_token(request) is not None:
            raise HTTPException(status_code=403, detail="service keys cannot read shared runs")
        raw_cookie = request.cookies.get(SHARE_COOKIE, "")
        raw_session_id, separator, token = raw_cookie.partition(".")
        if not separator:
            raise HTTPException(status_code=401, detail="share session required")
        try:
            repository.validate_access_session(
                UUID(raw_session_id), token, pepper=pepper, run_id=run_id
            )
        except (ValueError, ShareAccessError) as error:
            raise HTTPException(status_code=401, detail="share session is invalid") from error

    @app.exception_handler(RunNotFoundError)
    async def run_not_found(_request: Request, error: RunNotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(error)})

    @app.exception_handler(RunConflictError)
    async def run_conflict(_request: Request, error: RunConflictError):
        return JSONResponse(status_code=409, content={"detail": str(error)})

    @app.exception_handler(DigestConflictError)
    async def digest_conflict(_request: Request, error: DigestConflictError):
        return JSONResponse(status_code=409, content={"detail": str(error)})

    @app.exception_handler(SequenceGapError)
    async def sequence_gap(_request: Request, error: SequenceGapError):
        return JSONResponse(
            status_code=409,
            content={
                "detail": str(error),
                "next_required_sequence": error.next_required_sequence,
            },
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/runs", status_code=201)
    def create_run(request: RunCreate, _scope: None = Depends(require_agent)):
        created = repository.create_run(request)
        return {"run_id": str(request.run_id), "created": created}

    @app.post("/v1/runs/{run_id}/events:batch")
    def append_events(
        run_id: UUID,
        batch: EventBatch,
        _scope: None = Depends(require_agent),
    ):
        if batch.run_id != run_id:
            raise HTTPException(status_code=422, detail="path and batch run ids differ")
        return repository.append_batch(batch)

    @app.get("/v1/runs/{run_id}/sync")
    def sync_status(run_id: UUID, _scope: None = Depends(require_agent)):
        return repository.sync_status(run_id)

    @app.post("/v1/admin/runs/{run_id}/shares", status_code=201)
    def create_share(
        run_id: UUID,
        request: ShareCreateRequest,
        _scope: None = Depends(require_admin),
    ):
        token = secrets.token_urlsafe(32)
        grant = ShareGrant(
            run_id=run_id,
            token=token,
            expires_at=datetime.now(timezone.utc)
            + timedelta(seconds=request.expires_in_seconds),
        )
        repository.create_share(grant, pepper=pepper)
        return {
            "share_id": str(grant.share_id),
            "token": token,
            "expires_at": grant.expires_at,
            "share_path": f"/share/{grant.share_id}#token={quote(token)}",
        }

    @app.delete("/v1/admin/shares/{share_id}", status_code=204)
    def revoke_share(
        share_id: UUID,
        _scope: None = Depends(require_admin),
    ) -> Response:
        repository.revoke_share(share_id)
        return Response(status_code=204)

    @app.post("/v1/share/exchange", status_code=204)
    def exchange_share(request: ShareExchangeRequest) -> Response:
        try:
            access = repository.exchange_share(
                request.share_id,
                request.token,
                pepper=pepper,
            )
        except ShareAccessError as error:
            raise HTTPException(status_code=401, detail="share link is invalid") from error
        response = Response(status_code=204)
        response.set_cookie(
            SHARE_COOKIE,
            f"{access.session_id}.{access.token}",
            expires=access.expires_at,
            secure=True,
            httponly=True,
            samesite="strict",
            path="/v1/share",
        )
        return response

    @app.get("/v1/share/runs/{run_id}")
    def shared_run(run_id: UUID, request: Request):
        require_share(request, run_id)
        events = repository.read_shareable_events(run_id)
        return {
            "run_id": str(run_id),
            "event_count": len(events),
            "events": [event.model_dump(mode="json") for event in events],
        }

    @app.get("/v1/share/runs/{run_id}/events")
    async def shared_events(
        run_id: UUID,
        request: Request,
        once: bool = False,
        last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
    ):
        require_share(request, run_id)
        try:
            cursor = max(0, int(last_event_id or "0"))
        except ValueError as error:
            raise HTTPException(status_code=400, detail="invalid Last-Event-ID") from error

        async def event_stream() -> AsyncIterator[str]:
            nonlocal cursor
            while True:
                require_share(request, run_id)
                events = repository.read_shareable_events(
                    run_id, after_sequence=cursor
                )
                for event in events:
                    cursor = event.sequence
                    data = json.dumps(event.model_dump(mode="json"), ensure_ascii=False)
                    yield f"id: {event.sequence}\nevent: trace\ndata: {data}\n\n"
                if once or await request.is_disconnected():
                    return
                if not events:
                    yield ": keep-alive\n\n"
                await asyncio.sleep(1)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no"},
        )

    @app.post("/v1/runs/{run_id}/blobs", status_code=201)
    async def upload_blob(
        run_id: UUID,
        request: Request,
        visibility: Literal["shareable", "restricted", "local_only"] = "restricted",
        content_type: Annotated[str | None, Header(alias="Content-Type")] = None,
        _scope: None = Depends(require_agent),
    ):
        content = await request.body()
        if not content or len(content) > settings.max_blob_bytes:
            raise HTTPException(status_code=413, detail="invalid blob size")
        blob_id = uuid4()
        object_key = f"{run_id}/{blob_id}"
        digest = hashlib.sha256(content).hexdigest()
        media_type = (content_type or "application/octet-stream")[:120]
        blob_store.put(object_key, content, media_type)
        try:
            repository.register_blob(
                BlobRecord(
                    blob_id=blob_id,
                    run_id=run_id,
                    object_key=object_key,
                    content_type=media_type,
                    size_bytes=len(content),
                    sha256=digest,
                    visibility=visibility,
                )
            )
        except Exception:
            blob_store.delete(object_key)
            raise
        return {
            "blob_id": str(blob_id),
            "size_bytes": len(content),
            "sha256": digest,
            "visibility": visibility,
        }

    @app.get("/v1/share/runs/{run_id}/blobs/{blob_id}")
    def download_blob(run_id: UUID, blob_id: UUID, request: Request):
        require_share(request, run_id)
        record = repository.read_blob(run_id, blob_id, shareable_only=True)
        return Response(
            content=blob_store.get(record.object_key),
            media_type=record.content_type,
            headers={"Content-Length": str(record.size_bytes)},
        )

    return app


__all__ = ["create_app"]
