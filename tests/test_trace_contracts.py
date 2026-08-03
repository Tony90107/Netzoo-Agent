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
from netzoo_agent_core.llm import append_llm_usage, evaluate_budget_call  # noqa: E402
from netzoo_agent_core.contracts import LLMUsage  # noqa: E402
from netzoo_agent_core.pricing import PriceCatalog  # noqa: E402


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


def test_price_catalog_loads_exact_integer_rates(monkeypatch):
    monkeypatch.setenv(
        "NETZOO_MODEL_PRICING_JSON",
        """{"openai/gpt-4o-mini":{"input_micro_usd_per_million":150000,"output_micro_usd_per_million":600000,"effective_at":"2026-08-03T00:00:00Z"}}""",
    )

    snapshot = PriceCatalog.from_environment().snapshot("openai/gpt-4o-mini")

    assert snapshot.provenance == "estimated"
    assert snapshot.input_micro_usd_per_million == 150_000
    assert snapshot.output_micro_usd_per_million == 600_000


def test_predictive_budget_reserves_finalization_and_reports_thresholds():
    warning = evaluate_budget_call(
        {"total_tokens": 13_600, "calls": [], "budget_tokens": 20_000},
        estimated_input_tokens=100,
        reserved_output_tokens=500,
        budget_tokens=20_000,
        reserve_tokens=1_500,
        allow_reserve=False,
    )
    blocked = evaluate_budget_call(
        {"total_tokens": 18_000, "calls": [], "budget_tokens": 20_000},
        estimated_input_tokens=100,
        reserved_output_tokens=500,
        budget_tokens=20_000,
        reserve_tokens=1_500,
        allow_reserve=False,
    )

    assert warning.status == "warning_70"
    assert warning.projected_tokens == 14_200
    assert blocked.status == "blocked"


def test_append_usage_prefers_provider_tokens_and_actual_cost():
    response = type(
        "UsageMessage",
        (),
        {
            "usage_metadata": {"input_tokens": 120, "output_tokens": 30},
            "response_metadata": {
                "id": "request-123",
                "usage": {"cost": "0.000036"},
            },
        },
    )()

    usage = append_llm_usage(
        None,
        role="router",
        model="openai/gpt-4o-mini",
        response=response,
        input_text="ignored estimate",
        output_text="ignored estimate",
        budget_tokens=20_000,
        duration_ms=25,
    )

    call = usage.calls[0]
    assert call.input_tokens == 120
    assert call.output_tokens == 30
    assert call.usage_provenance == "actual"
    assert call.cost_provenance == "actual"
    assert call.cost_micro_usd == 36
    assert call.provider_request_id == "request-123"


def test_legacy_estimated_call_migrates_to_typed_usage():
    usage = LLMUsage.model_validate(
        {
            "input_tokens": 10,
            "output_tokens": 2,
            "total_tokens": 12,
            "budget_tokens": 20_000,
            "calls": [
                {
                    "role": "router",
                    "model": "legacy/model",
                    "input_tokens": 10,
                    "output_tokens": 2,
                    "total_tokens": 12,
                    "estimated": True,
                }
            ],
        }
    )

    assert usage.calls[0].usage_provenance == "estimated"
    assert usage.calls[0]["estimated"] is True
