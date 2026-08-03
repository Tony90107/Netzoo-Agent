from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from netzoo_agent_core.trace_contracts import ZERO_HASH, TraceEvent
from netzoo_observer.contracts import EventBatch, RunCreate, ShareGrant
from netzoo_observer.database import Base
from netzoo_observer.repository import (
    DigestConflictError,
    ObserverRepository,
    SequenceGapError,
    ShareAccessError,
)


@pytest.fixture
def repository() -> ObserverRepository:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return ObserverRepository(sessionmaker(engine, expire_on_commit=False))


@pytest.fixture
def two_events() -> list[TraceEvent]:
    run_id = uuid4()
    occurred_at = datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc)
    first = TraceEvent.create(
        run_id=run_id,
        sequence=1,
        event_type="run.started",
        node="agent",
        payload={"session_id": "session-1", "profile_id": "panda"},
        previous_hash=ZERO_HASH,
        occurred_at=occurred_at,
        recorded_at=occurred_at,
    )
    second = TraceEvent.create(
        run_id=run_id,
        sequence=2,
        event_type="tool.completed",
        node="tool",
        payload={"tool": "netzoo.panda", "input_tokens": 120},
        previous_hash=first.event_hash,
        occurred_at=occurred_at + timedelta(seconds=1),
        recorded_at=occurred_at + timedelta(seconds=1),
    )
    return [first, second]


def test_batch_append_is_contiguous_idempotent_and_atomic(
    repository: ObserverRepository,
    two_events: list[TraceEvent],
) -> None:
    run_id = two_events[0].run_id
    repository.create_run(RunCreate.from_event(two_events[0]))

    first = repository.append_batch(EventBatch(run_id=run_id, events=two_events))
    retried = repository.append_batch(EventBatch(run_id=run_id, events=two_events))

    assert first.accepted_count == 2
    assert first.next_required_sequence == 3
    assert retried.accepted_count == 0
    assert retried.next_required_sequence == 3

    conflicting = TraceEvent.create(
        run_id=run_id,
        sequence=2,
        event_type="tool.completed",
        node="tool",
        payload={"tool": "netzoo.puma"},
        previous_hash=two_events[0].event_hash,
        occurred_at=two_events[1].occurred_at,
        recorded_at=two_events[1].recorded_at,
    )
    with pytest.raises(DigestConflictError):
        repository.append_batch(EventBatch(run_id=run_id, events=[conflicting]))

    third = TraceEvent.create(
        run_id=run_id,
        sequence=3,
        event_type="decision.recorded",
        node="decision",
        payload={"choice": "continue"},
        previous_hash=two_events[1].event_hash,
    )
    fifth = TraceEvent.create(
        run_id=run_id,
        sequence=5,
        event_type="run.failed",
        node="agent",
        payload={"reason": "gap"},
        previous_hash=third.event_hash,
    )
    with pytest.raises(SequenceGapError) as gap:
        repository.append_batch(run_id, [third, fifth])

    assert gap.value.next_required_sequence == 3
    assert repository.sync_status(run_id).next_required_sequence == 3


def test_share_reads_exclude_restricted_and_local_events(
    repository: ObserverRepository,
    two_events: list[TraceEvent],
) -> None:
    run_id = two_events[0].run_id
    restricted = TraceEvent.create(
        run_id=run_id,
        sequence=3,
        event_type="memory.read",
        node="memory",
        payload={"private": "redacted upstream"},
        previous_hash=two_events[1].event_hash,
        visibility="restricted",
    )
    local_only = TraceEvent.create(
        run_id=run_id,
        sequence=4,
        event_type="debug.snapshot",
        node="agent",
        payload={"debug": True},
        previous_hash=restricted.event_hash,
        visibility="local_only",
    )
    repository.create_run(RunCreate.from_event(two_events[0]))
    repository.append_batch(run_id, [*two_events, restricted, local_only])

    visible = repository.read_shareable_events(run_id)

    assert [event.sequence for event in visible] == [1, 2]


def test_share_exchange_fails_after_expiry_or_revocation(
    repository: ObserverRepository,
    two_events: list[TraceEvent],
) -> None:
    repository.create_run(RunCreate.from_event(two_events[0]))
    now = datetime.now(timezone.utc)
    pepper = "observer-pepper-with-at-least-32-bytes"

    expired = ShareGrant(
        run_id=two_events[0].run_id,
        token="expired-share-token-with-enough-entropy",
        expires_at=now + timedelta(minutes=1),
    )
    repository.create_share(expired, pepper=pepper)
    with pytest.raises(ShareAccessError, match="expired"):
        repository.exchange_share(
            expired.share_id,
            expired.token.get_secret_value(),
            pepper=pepper,
            now=now + timedelta(minutes=2),
        )

    active = ShareGrant(
        run_id=two_events[0].run_id,
        token="active-share-token-with-enough-entropy",
        expires_at=now + timedelta(days=1),
    )
    repository.create_share(active, pepper=pepper)
    repository.revoke_share(active.share_id, now=now)
    with pytest.raises(ShareAccessError, match="revoked"):
        repository.exchange_share(
            active.share_id,
            active.token.get_secret_value(),
            pepper=pepper,
            now=now,
        )
