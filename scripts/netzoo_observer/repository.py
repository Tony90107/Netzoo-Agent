"""Transactional persistence and integrity policy for observer traces."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from netzoo_agent_core.trace_contracts import ZERO_HASH, TraceEvent

from .auth import hash_credential, verify_credential
from .contracts import BatchAck, EventBatch, RunCreate, ShareGrant
from .models import (
    ObserverAccessSession,
    ObserverBlob,
    ObserverEvent,
    ObserverRun,
    ObserverShare,
)


class ObserverRepositoryError(RuntimeError):
    pass


class RunNotFoundError(ObserverRepositoryError):
    pass


class RunConflictError(ObserverRepositoryError):
    pass


class DigestConflictError(ObserverRepositoryError):
    pass


class SequenceGapError(ObserverRepositoryError):
    def __init__(self, next_required_sequence: int):
        self.next_required_sequence = next_required_sequence
        super().__init__(f"next required sequence is {next_required_sequence}")


class ShareAccessError(ObserverRepositoryError):
    pass


@dataclass(frozen=True)
class ShareAccessSession:
    session_id: UUID
    run_id: UUID
    token: str
    expires_at: datetime


@dataclass(frozen=True)
class BlobRecord:
    blob_id: UUID
    run_id: UUID
    object_key: str
    content_type: str
    size_bytes: int
    sha256: str
    visibility: str


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class ObserverRepository:
    """Database boundary for immutable events and revocable sharing."""

    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    def create_run(self, request: RunCreate) -> bool:
        run_id = str(request.run_id)
        with self._session_factory.begin() as session:
            existing = session.get(ObserverRun, run_id)
            if existing is not None:
                expected = (
                    request.schema_version,
                    request.agent_id,
                    request.session_id,
                    request.profile_id,
                    _utc(request.created_at),
                )
                actual = (
                    existing.schema_version,
                    existing.agent_id,
                    existing.session_id,
                    existing.profile_id,
                    _utc(existing.created_at),
                )
                if actual != expected:
                    raise RunConflictError("run id already exists with different metadata")
                return False
            created_at = _utc(request.created_at)
            session.add(
                ObserverRun(
                    run_id=run_id,
                    schema_version=request.schema_version,
                    agent_id=request.agent_id,
                    session_id=request.session_id,
                    profile_id=request.profile_id,
                    created_at=created_at,
                    updated_at=created_at,
                    acknowledged_sequence=0,
                    final_hash=ZERO_HASH,
                    status="running",
                )
            )
        return True

    def append_batch(
        self,
        batch_or_run_id: EventBatch | UUID | str,
        events: list[TraceEvent] | None = None,
    ) -> BatchAck:
        if isinstance(batch_or_run_id, EventBatch):
            run_id = batch_or_run_id.run_id
            batch_events = batch_or_run_id.events
        else:
            run_id = UUID(str(batch_or_run_id))
            if not events:
                raise ValueError("event batch cannot be empty")
            batch_events = events

        accepted = 0
        try:
            with self._session_factory.begin() as session:
                run = session.scalar(
                    select(ObserverRun)
                    .where(ObserverRun.run_id == str(run_id))
                    .with_for_update()
                )
                if run is None:
                    raise RunNotFoundError(f"run {run_id} was not found")

                persisted_next_sequence = run.acknowledged_sequence + 1
                next_sequence = persisted_next_sequence
                final_hash = run.final_hash
                for event in batch_events:
                    if event.run_id != run_id:
                        raise ValueError("event belongs to a different run")
                    if not event.verify():
                        raise DigestConflictError("event hash verification failed")

                    if event.sequence < next_sequence:
                        existing = session.scalar(
                            select(ObserverEvent).where(
                                ObserverEvent.run_id == str(run_id),
                                ObserverEvent.sequence == event.sequence,
                            )
                        )
                        if existing is None or existing.event_hash != event.event_hash:
                            raise DigestConflictError(
                                f"event {event.sequence} conflicts with stored digest"
                            )
                        continue

                    if event.sequence != next_sequence:
                        raise SequenceGapError(persisted_next_sequence)
                    if event.previous_hash != final_hash:
                        raise DigestConflictError(
                            f"event {event.sequence} does not extend the stored hash chain"
                        )

                    event_json = event.model_dump(mode="json")
                    session.add(
                        ObserverEvent(
                            event_id=str(event.event_id),
                            run_id=str(run_id),
                            sequence=event.sequence,
                            event_type=event.event_type,
                            occurred_at=_utc(event.occurred_at),
                            recorded_at=_utc(event.recorded_at),
                            node=event.node,
                            visibility=event.visibility,
                            previous_hash=event.previous_hash,
                            event_hash=event.event_hash,
                            payload=event_json["payload"],
                            event_json=event_json,
                        )
                    )
                    accepted += 1
                    next_sequence += 1
                    final_hash = event.event_hash

                run.acknowledged_sequence = next_sequence - 1
                run.final_hash = final_hash
                run.updated_at = datetime.now(timezone.utc)
        except IntegrityError as error:
            raise DigestConflictError("event identity already exists") from error

        return BatchAck(
            run_id=run_id,
            accepted_count=accepted,
            next_required_sequence=next_sequence,
            final_hash=final_hash,
        )

    def sync_status(self, run_id: UUID | str) -> BatchAck:
        run_uuid = UUID(str(run_id))
        with self._session_factory() as session:
            run = session.get(ObserverRun, str(run_uuid))
            if run is None:
                raise RunNotFoundError(f"run {run_uuid} was not found")
            return BatchAck(
                run_id=run_uuid,
                accepted_count=0,
                next_required_sequence=run.acknowledged_sequence + 1,
                final_hash=run.final_hash,
            )

    def read_shareable_events(
        self, run_id: UUID | str, *, after_sequence: int = 0
    ) -> list[TraceEvent]:
        run_uuid = UUID(str(run_id))
        with self._session_factory() as session:
            if session.get(ObserverRun, str(run_uuid)) is None:
                raise RunNotFoundError(f"run {run_uuid} was not found")
            rows = session.scalars(
                select(ObserverEvent)
                .where(
                    ObserverEvent.run_id == str(run_uuid),
                    ObserverEvent.visibility == "shareable",
                    ObserverEvent.sequence > after_sequence,
                )
                .order_by(ObserverEvent.sequence)
            )
            return [TraceEvent.model_validate(row.event_json) for row in rows]

    def register_blob(self, record: BlobRecord) -> None:
        with self._session_factory.begin() as session:
            if session.get(ObserverRun, str(record.run_id)) is None:
                raise RunNotFoundError(f"run {record.run_id} was not found")
            session.add(
                ObserverBlob(
                    blob_id=str(record.blob_id),
                    run_id=str(record.run_id),
                    object_key=record.object_key,
                    content_type=record.content_type,
                    size_bytes=record.size_bytes,
                    sha256=record.sha256,
                    visibility=record.visibility,
                    created_at=datetime.now(timezone.utc),
                )
            )

    def read_blob(
        self,
        run_id: UUID | str,
        blob_id: UUID | str,
        *,
        shareable_only: bool,
    ) -> BlobRecord:
        with self._session_factory() as session:
            row = session.get(ObserverBlob, str(blob_id))
            if row is None or row.run_id != str(run_id):
                raise RunNotFoundError("blob was not found for this run")
            if shareable_only and row.visibility != "shareable":
                raise RunNotFoundError("blob was not found for this run")
            return BlobRecord(
                blob_id=UUID(row.blob_id),
                run_id=UUID(row.run_id),
                object_key=row.object_key,
                content_type=row.content_type,
                size_bytes=row.size_bytes,
                sha256=row.sha256,
                visibility=row.visibility,
            )

    def create_share(self, grant: ShareGrant, *, pepper: str) -> None:
        now = datetime.now(timezone.utc)
        with self._session_factory.begin() as session:
            if session.get(ObserverRun, str(grant.run_id)) is None:
                raise RunNotFoundError(f"run {grant.run_id} was not found")
            session.add(
                ObserverShare(
                    share_id=str(grant.share_id),
                    run_id=str(grant.run_id),
                    token_hash=hash_credential(grant.token.get_secret_value(), pepper),
                    created_at=now,
                    expires_at=_utc(grant.expires_at),
                    revoked_at=None,
                )
            )

    def revoke_share(self, share_id: UUID | str, *, now: datetime | None = None) -> None:
        with self._session_factory.begin() as session:
            share = session.get(ObserverShare, str(share_id))
            if share is None:
                raise ShareAccessError("share was not found")
            revoked_at = _utc(now or datetime.now(timezone.utc))
            share.revoked_at = revoked_at
            sessions = session.scalars(
                select(ObserverAccessSession).where(
                    ObserverAccessSession.share_id == str(share_id),
                    ObserverAccessSession.revoked_at.is_(None),
                )
            )
            for access_session in sessions:
                access_session.revoked_at = revoked_at

    def exchange_share(
        self,
        share_id: UUID | str,
        token: str,
        *,
        pepper: str,
        now: datetime | None = None,
        session_ttl: timedelta = timedelta(hours=8),
    ) -> ShareAccessSession:
        exchanged_at = _utc(now or datetime.now(timezone.utc))
        with self._session_factory.begin() as session:
            share = session.get(ObserverShare, str(share_id))
            if share is None:
                raise ShareAccessError("share was not found")
            if share.revoked_at is not None:
                raise ShareAccessError("share was revoked")
            if _utc(share.expires_at) <= exchanged_at:
                raise ShareAccessError("share expired")
            if not verify_credential(token, pepper, share.token_hash):
                raise ShareAccessError("share credential is invalid")

            expires_at = min(_utc(share.expires_at), exchanged_at + session_ttl)
            session_id = uuid4()
            session_token = secrets.token_urlsafe(32)
            session.add(
                ObserverAccessSession(
                    session_id=str(session_id),
                    share_id=share.share_id,
                    run_id=share.run_id,
                    token_hash=hash_credential(session_token, pepper),
                    created_at=exchanged_at,
                    expires_at=expires_at,
                    revoked_at=None,
                )
            )
            return ShareAccessSession(
                session_id=session_id,
                run_id=UUID(share.run_id),
                token=session_token,
                expires_at=expires_at,
            )

    def validate_access_session(
        self,
        session_id: UUID | str,
        token: str,
        *,
        pepper: str,
        run_id: UUID | str,
        now: datetime | None = None,
    ) -> None:
        checked_at = _utc(now or datetime.now(timezone.utc))
        with self._session_factory() as session:
            access = session.get(ObserverAccessSession, str(session_id))
            if access is None or access.run_id != str(run_id):
                raise ShareAccessError("access session is invalid")
            share = session.get(ObserverShare, access.share_id)
            if share is None or share.revoked_at is not None or access.revoked_at is not None:
                raise ShareAccessError("access session was revoked")
            if _utc(share.expires_at) <= checked_at or _utc(access.expires_at) <= checked_at:
                raise ShareAccessError("access session expired")
            if not verify_credential(token, pepper, access.token_hash):
                raise ShareAccessError("access session is invalid")


__all__ = [
    "BlobRecord",
    "DigestConflictError",
    "ObserverRepository",
    "ObserverRepositoryError",
    "RunConflictError",
    "RunNotFoundError",
    "SequenceGapError",
    "ShareAccessError",
    "ShareAccessSession",
]
