"""Versioned contracts for durable NetZoo agent observability records."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)


__all__ = [
    "ZERO_HASH",
    "BudgetDecision",
    "LLMCallUsage",
    "PriceSnapshot",
    "RunManifest",
    "TraceEvent",
    "Visibility",
    "canonical_json",
]


ZERO_HASH = "0" * 64
Visibility = Literal["shareable", "restricted", "local_only"]
UsageProvenance = Literal["actual", "estimated", "unavailable"]


def canonical_json(value: object) -> str:
    """Serialize JSON deterministically for hashing and JSONL persistence."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("trace timestamps must include a timezone")
    return value.astimezone(timezone.utc)


class TraceEvent(BaseModel):
    """One immutable event in a per-run append-only hash chain."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1] = 1
    event_id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    sequence: int = Field(ge=1)
    event_type: str = Field(
        min_length=3,
        max_length=80,
        pattern=r"^[a-z][a-z0-9_.-]+$",
    )
    occurred_at: datetime
    recorded_at: datetime
    node: str = Field(min_length=1, max_length=80)
    parent_event_id: UUID | None = None
    visibility: Visibility = "shareable"
    payload: dict
    previous_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    event_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    _normalize_occurred_at = field_validator("occurred_at")(_utc_datetime)
    _normalize_recorded_at = field_validator("recorded_at")(_utc_datetime)

    def hash_material(self) -> dict:
        return self.model_dump(mode="json", exclude={"event_hash"})

    def verify(self) -> bool:
        expected = hashlib.sha256(
            canonical_json(self.hash_material()).encode("utf-8")
        ).hexdigest()
        return expected == self.event_hash

    @classmethod
    def create(
        cls,
        *,
        run_id: UUID | str,
        sequence: int,
        event_type: str,
        node: str,
        payload: dict,
        previous_hash: str,
        event_id: UUID | str | None = None,
        occurred_at: datetime | None = None,
        recorded_at: datetime | None = None,
        parent_event_id: UUID | str | None = None,
        visibility: Visibility = "shareable",
    ) -> "TraceEvent":
        now = datetime.now(timezone.utc)
        provisional = cls(
            event_id=event_id or uuid4(),
            run_id=run_id,
            sequence=sequence,
            event_type=event_type,
            occurred_at=occurred_at or now,
            recorded_at=recorded_at or now,
            node=node,
            parent_event_id=parent_event_id,
            visibility=visibility,
            payload=payload,
            previous_hash=previous_hash,
            event_hash=ZERO_HASH,
        )
        digest = hashlib.sha256(
            canonical_json(provisional.hash_material()).encode("utf-8")
        ).hexdigest()
        return provisional.model_copy(update={"event_hash": digest})


class PriceSnapshot(BaseModel):
    """Immutable model rates used for one historical cost estimate."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    snapshot_id: UUID = Field(default_factory=uuid4)
    model: str = Field(min_length=1, max_length=200)
    provenance: Literal["estimated", "unavailable"]
    effective_at: datetime
    input_micro_usd_per_million: int | None = Field(default=None, ge=0)
    output_micro_usd_per_million: int | None = Field(default=None, ge=0)

    _normalize_effective_at = field_validator("effective_at")(_utc_datetime)

    @model_validator(mode="after")
    def validate_rates(self) -> "PriceSnapshot":
        rates = (
            self.input_micro_usd_per_million,
            self.output_micro_usd_per_million,
        )
        if self.provenance == "unavailable" and any(rate is not None for rate in rates):
            raise ValueError("unavailable prices cannot contain numeric rates")
        if self.provenance == "estimated" and any(rate is None for rate in rates):
            raise ValueError("estimated prices require both input and output rates")
        return self


class LLMCallUsage(BaseModel):
    """Token, timing, and cost provenance for one provider call."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    call_id: UUID = Field(default_factory=uuid4)
    role: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=200)
    provider_request_id: str | None = Field(default=None, max_length=300)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    cache_read_tokens: int = Field(default=0, ge=0)
    cache_write_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    usage_provenance: UsageProvenance
    cost_provenance: UsageProvenance = "unavailable"
    cost_micro_usd: int | None = Field(default=None, ge=0)
    price_snapshot: PriceSnapshot | None = None
    duration_ms: int = Field(default=0, ge=0)
    status: Literal["success", "failed", "blocked"]

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_call(cls, value):
        if not isinstance(value, dict) or "estimated" not in value:
            return value
        migrated = dict(value)
        estimated = bool(migrated.pop("estimated"))
        migrated.setdefault(
            "usage_provenance",
            "estimated" if estimated else "actual",
        )
        migrated.setdefault("cost_provenance", "unavailable")
        migrated.setdefault("status", "success")
        return migrated

    @model_validator(mode="after")
    def validate_totals_and_cost(self) -> "LLMCallUsage":
        if self.total_tokens != self.input_tokens + self.output_tokens:
            raise ValueError("total_tokens must equal input_tokens plus output_tokens")
        if self.cost_provenance == "unavailable" and self.cost_micro_usd is not None:
            raise ValueError("unavailable cost cannot contain a numeric value")
        if self.cost_provenance != "unavailable" and self.cost_micro_usd is None:
            raise ValueError("actual or estimated cost requires a numeric value")
        if self.cost_provenance == "estimated" and self.price_snapshot is None:
            raise ValueError("estimated cost requires a price snapshot")
        return self

    @computed_field
    @property
    def estimated(self) -> bool:
        """Backward-compatible view used by historical callers and sessions."""
        return self.usage_provenance != "actual"

    def __getitem__(self, key: str):
        if key == "estimated":
            return self.estimated
        return getattr(self, key)


class BudgetDecision(BaseModel):
    """Predictive preflight decision for one possible LLM call."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: Literal["allowed", "warning_70", "warning_85", "blocked"]
    consumed_tokens: int = Field(ge=0)
    estimated_input_tokens: int = Field(ge=0)
    reserved_output_tokens: int = Field(ge=0)
    projected_tokens: int = Field(ge=0)
    hard_limit_tokens: int = Field(gt=0)
    reserve_tokens: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_projection(self) -> "BudgetDecision":
        expected = (
            self.consumed_tokens
            + self.estimated_input_tokens
            + self.reserved_output_tokens
        )
        if self.projected_tokens != expected:
            raise ValueError("projected_tokens does not match the preflight components")
        return self


class RunManifest(BaseModel):
    """Recoverable metadata for one local event stream."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1] = 1
    run_id: UUID
    session_id: str = Field(min_length=1, max_length=80)
    profile_id: str = Field(min_length=1, max_length=80)
    created_at: datetime
    updated_at: datetime
    finished_at: datetime | None = None
    status: Literal[
        "running",
        "pending",
        "completed",
        "failed",
        "interrupted",
        "trace_degraded",
    ] = "running"
    event_count: int = Field(default=0, ge=0)
    final_sequence: int = Field(default=0, ge=0)
    final_hash: str = Field(default=ZERO_HASH, pattern=r"^[0-9a-f]{64}$")
    sync_ack_sequence: int = Field(default=0, ge=0)
    sealed: bool = False

    _normalize_created_at = field_validator("created_at")(_utc_datetime)
    _normalize_updated_at = field_validator("updated_at")(_utc_datetime)
    _normalize_finished_at = field_validator("finished_at")(
        lambda value: None if value is None else _utc_datetime(value)
    )

    @model_validator(mode="after")
    def validate_tail(self) -> "RunManifest":
        if self.event_count != self.final_sequence:
            raise ValueError("event_count and final_sequence must match")
        if self.sync_ack_sequence > self.final_sequence:
            raise ValueError("sync acknowledgement cannot exceed the local sequence")
        if self.sealed and self.finished_at is None:
            raise ValueError("sealed manifests require finished_at")
        if not self.sealed and self.finished_at is not None:
            raise ValueError("unsealed manifests cannot contain finished_at")
        return self
