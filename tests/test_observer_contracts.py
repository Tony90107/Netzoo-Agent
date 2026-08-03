import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.trace_contracts import ZERO_HASH, TraceEvent  # noqa: E402
from netzoo_observer.auth import hash_credential, verify_credential  # noqa: E402
from netzoo_observer.contracts import EventBatch  # noqa: E402
from netzoo_observer.settings import CollectorSettings  # noqa: E402


def test_settings_and_agent_hash_fail_closed(monkeypatch):
    monkeypatch.delenv("NETZOO_OBSERVER_CREDENTIAL_PEPPER", raising=False)
    monkeypatch.setenv("NETZOO_OBSERVER_AGENT_KEY", "a" * 32)
    monkeypatch.setenv("NETZOO_OBSERVER_ADMIN_KEY", "b" * 32)

    with pytest.raises(ValueError, match="NETZOO_OBSERVER_CREDENTIAL_PEPPER"):
        CollectorSettings.from_environment()

    digest = hash_credential("agent-secret", "pepper-with-at-least-32-bytes-000")
    assert digest != "agent-secret"
    assert verify_credential(
        "agent-secret",
        "pepper-with-at-least-32-bytes-000",
        digest,
    )
    assert not verify_credential(
        "wrong-secret",
        "pepper-with-at-least-32-bytes-000",
        digest,
    )


def test_event_batch_accepts_one_run_and_rejects_more_than_100_events():
    run_id = UUID("11111111-1111-4111-8111-111111111111")
    stamp = datetime(2026, 8, 3, tzinfo=timezone.utc)
    event = TraceEvent.create(
        run_id=run_id,
        sequence=1,
        event_type="run.started",
        node="cli",
        payload={"status": "running"},
        previous_hash=ZERO_HASH,
        occurred_at=stamp,
        recorded_at=stamp,
    )

    batch = EventBatch(run_id=run_id, events=[event])

    assert batch.events[0].event_hash == event.event_hash
    with pytest.raises(ValidationError):
        EventBatch(run_id=run_id, events=[event] * 101)
