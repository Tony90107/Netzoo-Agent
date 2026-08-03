"""Immutable, explicitly configured model price snapshots."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from pydantic import BaseModel, ConfigDict, Field

from .trace_contracts import PriceSnapshot


__all__ = ["PriceCatalog"]


class _ConfiguredPrice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_micro_usd_per_million: int = Field(ge=0)
    output_micro_usd_per_million: int = Field(ge=0)
    effective_at: datetime


class PriceCatalog:
    """Exact model-name lookup with no guessed fallback rates."""

    def __init__(self, entries: dict[str, _ConfiguredPrice] | None = None):
        self._entries = entries or {}

    @classmethod
    def from_environment(cls) -> "PriceCatalog":
        raw = os.environ.get("NETZOO_MODEL_PRICING_JSON", "{}").strip() or "{}"
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValueError("NETZOO_MODEL_PRICING_JSON must be valid JSON") from error
        if not isinstance(decoded, dict):
            raise ValueError("NETZOO_MODEL_PRICING_JSON must be a model-keyed object")
        entries = {
            str(model): _ConfiguredPrice.model_validate(value)
            for model, value in decoded.items()
        }
        return cls(entries)

    def snapshot(self, model: str) -> PriceSnapshot:
        entry = self._entries.get(model)
        if entry is None:
            effective_at = datetime.now(timezone.utc)
            identity = f"{model}|unavailable|{effective_at.isoformat()}"
            return PriceSnapshot(
                snapshot_id=uuid5(NAMESPACE_URL, identity),
                model=model,
                provenance="unavailable",
                effective_at=effective_at,
            )
        effective_at = entry.effective_at
        if effective_at.tzinfo is None:
            raise ValueError(f"price effective_at for '{model}' must include a timezone")
        identity = (
            f"{model}|{effective_at.isoformat()}|"
            f"{entry.input_micro_usd_per_million}|"
            f"{entry.output_micro_usd_per_million}"
        )
        return PriceSnapshot(
            snapshot_id=uuid5(NAMESPACE_URL, identity),
            model=model,
            provenance="estimated",
            effective_at=effective_at,
            input_micro_usd_per_million=entry.input_micro_usd_per_million,
            output_micro_usd_per_million=entry.output_micro_usd_per_million,
        )
