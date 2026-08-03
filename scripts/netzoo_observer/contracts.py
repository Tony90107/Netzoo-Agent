"""Versioned request and response contracts for the observer API."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

from netzoo_agent_core.trace_contracts import TraceEvent


__all__ = [
    "AccessScope",
    "BatchAck",
    "EventBatch",
    "RunCreate",
    "ShareGrant",
]


class AccessScope(str, Enum):
    AGENT = "agent"
    ADMIN = "admin"
    SHARE = "share"


class RunCreate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int = Field(default=1, ge=1)
    run_id: UUID
    agent_id: str = Field(min_length=1, max_length=120)
    session_id: str = Field(min_length=1, max_length=80)
    profile_id: str = Field(min_length=1, max_length=80)
    created_at: datetime

    @classmethod
    def from_event(cls, event: TraceEvent, *, agent_id: str = "default-agent"):
        return cls(
            run_id=event.run_id,
            agent_id=agent_id,
            session_id=str(event.payload.get("session_id") or event.run_id),
            profile_id=str(event.payload.get("profile_id") or "default"),
            created_at=event.occurred_at,
        )


class EventBatch(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: UUID
    events: list[TraceEvent] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_events(self) -> "EventBatch":
        previous_sequence = None
        for event in self.events:
            if event.run_id != self.run_id:
                raise ValueError("every event must belong to the batch run")
            if not event.verify():
                raise ValueError("event hash verification failed")
            if previous_sequence is not None and event.sequence != previous_sequence + 1:
                raise ValueError("events in one batch must be contiguous")
            previous_sequence = event.sequence
        return self


class BatchAck(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: UUID
    accepted_count: int = Field(ge=0)
    next_required_sequence: int = Field(ge=1)
    final_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class ShareGrant(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    share_id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    token: SecretStr
    expires_at: datetime

    @model_validator(mode="after")
    def validate_expiry(self) -> "ShareGrant":
        if self.expires_at.tzinfo is None:
            raise ValueError("share expiry must include a timezone")
        if self.expires_at <= datetime.now(timezone.utc):
            raise ValueError("share expiry must be in the future")
        return self
