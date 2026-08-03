import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.trace_contracts import (  # noqa: E402
    ZERO_HASH,
    BudgetDecision,
    LLMCallUsage,
    PriceSnapshot,
    RunManifest,
    TraceEvent,
)


RUN_ID = UUID("11111111-1111-4111-8111-111111111111")
EVENT_ID = UUID("22222222-2222-4222-8222-222222222222")
SNAPSHOT_ID = UUID("33333333-3333-4333-8333-333333333333")
STAMP = datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc)


def test_trace_event_has_a_stable_hash_and_detects_payload_changes():
    event = TraceEvent.create(
        event_id=EVENT_ID,
        run_id=RUN_ID,
        sequence=1,
        event_type="run.started",
        node="cli",
        payload={"workflow": "PANDA", "status": "running"},
        previous_hash=ZERO_HASH,
        occurred_at=STAMP,
        recorded_at=STAMP,
    )

    assert event.verify()
    assert event.event_hash == "b5a962595140a2a30a77fbaac99d04c4e3da669f9fdaa6bdaa9d52b886707aa8"
    assert event.model_copy(update={"payload": {"status": "changed"}}).verify() is False


def test_trace_event_rejects_non_uuid_run_and_zero_sequence():
    with pytest.raises(ValidationError):
        TraceEvent.create(
            run_id="session-name",
            sequence=0,
            event_type="run.started",
            node="cli",
            payload={},
            previous_hash=ZERO_HASH,
        )


def test_manifest_cannot_be_mutated_after_validation():
    manifest = RunManifest(
        run_id=RUN_ID,
        session_id="demo",
        profile_id="default",
        created_at=STAMP,
        updated_at=STAMP,
    )

    with pytest.raises(ValidationError):
        manifest.status = "completed"


def test_usage_and_budget_contracts_preserve_cost_provenance():
    price = PriceSnapshot(
        snapshot_id=SNAPSHOT_ID,
        model="openai/gpt-4o-mini",
        provenance="estimated",
        effective_at=STAMP,
        input_micro_usd_per_million=150_000,
        output_micro_usd_per_million=600_000,
    )
    call = LLMCallUsage(
        role="router",
        model=price.model,
        input_tokens=120,
        output_tokens=30,
        total_tokens=150,
        usage_provenance="actual",
        cost_provenance="estimated",
        cost_micro_usd=36,
        price_snapshot=price,
        duration_ms=25,
        status="success",
    )
    decision = BudgetDecision(
        status="warning_70",
        consumed_tokens=13_500,
        estimated_input_tokens=100,
        reserved_output_tokens=500,
        projected_tokens=14_100,
        hard_limit_tokens=20_000,
        reserve_tokens=1_500,
    )

    assert call.cost_micro_usd == 36
    assert call.price_snapshot.provenance == "estimated"
    assert decision.projected_tokens == 14_100


def test_unavailable_price_cannot_claim_a_numeric_rate():
    with pytest.raises(ValidationError):
        PriceSnapshot(
            snapshot_id=SNAPSHOT_ID,
            model="unknown/model",
            provenance="unavailable",
            effective_at=STAMP,
            input_micro_usd_per_million=1,
        )
