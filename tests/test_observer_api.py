from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from netzoo_agent_core.trace_contracts import ZERO_HASH, TraceEvent
from netzoo_observer.api import create_app
from netzoo_observer.blob_store import MemoryBlobStore
from netzoo_observer.database import Base
from netzoo_observer.repository import ObserverRepository
from netzoo_observer.settings import CollectorSettings


AGENT_KEY = "agent-key-with-at-least-thirty-two-bytes"
ADMIN_KEY = "admin-key-with-at-least-thirty-two-bytes"
PEPPER = "pepper-with-at-least-thirty-two-bytes"
RUN_ID = UUID("11111111-1111-4111-8111-111111111111")


def _client() -> TestClient:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    repository = ObserverRepository(sessionmaker(engine, expire_on_commit=False))
    settings = CollectorSettings(
        credential_pepper=SecretStr(PEPPER),
        agent_key=SecretStr(AGENT_KEY),
        admin_key=SecretStr(ADMIN_KEY),
    )
    return TestClient(
        create_app(settings, repository, MemoryBlobStore()),
        base_url="https://observer.test",
    )


def _trace_payloads() -> tuple[dict, dict]:
    stamp = datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc)
    first = TraceEvent.create(
        run_id=RUN_ID,
        sequence=1,
        event_type="run.started",
        node="agent",
        payload={
            "session_id": "class-demo",
            "profile_id": "panda",
            "task": "<script>alert('must stay inert')</script>",
        },
        previous_hash=ZERO_HASH,
        occurred_at=stamp,
        recorded_at=stamp,
    )
    second = TraceEvent.create(
        run_id=RUN_ID,
        sequence=2,
        event_type="memory.read",
        node="memory",
        payload={"secret": "not shared"},
        previous_hash=first.event_hash,
        visibility="restricted",
        occurred_at=stamp,
        recorded_at=stamp,
    )
    run = {
        "run_id": str(RUN_ID),
        "agent_id": "student-agent",
        "session_id": "class-demo",
        "profile_id": "panda",
        "created_at": stamp.isoformat(),
    }
    batch = {
        "run_id": str(RUN_ID),
        "events": [
            first.model_dump(mode="json"),
            second.model_dump(mode="json"),
        ],
    }
    return run, batch


def test_agent_ingests_admin_shares_and_revocation_is_immediate() -> None:
    client = _client()
    run, batch = _trace_payloads()
    agent_headers = {"Authorization": f"Bearer {AGENT_KEY}"}
    admin_headers = {"Authorization": f"Bearer {ADMIN_KEY}"}

    created = client.post("/v1/runs", json=run, headers=agent_headers)
    appended = client.post(
        f"/v1/runs/{RUN_ID}/events:batch",
        json=batch,
        headers=agent_headers,
    )

    assert created.status_code == 201
    assert appended.status_code == 200
    assert appended.json()["next_required_sequence"] == 3
    assert client.get(f"/v1/share/runs/{RUN_ID}", headers=agent_headers).status_code == 403

    shared = client.post(
        f"/v1/admin/runs/{RUN_ID}/shares",
        json={"expires_in_seconds": 3600},
        headers=admin_headers,
    )
    assert shared.status_code == 201
    share = shared.json()
    assert share["token"] not in share["share_path"].split("#", 1)[0]
    assert "#token=" in share["share_path"]

    exchanged = client.post(
        "/v1/share/exchange",
        json={"share_id": share["share_id"], "token": share["token"]},
    )
    assert exchanged.status_code == 204
    assert "HttpOnly" in exchanged.headers["set-cookie"]
    assert "SameSite=strict" in exchanged.headers["set-cookie"]

    snapshot = client.get(f"/v1/share/runs/{RUN_ID}")
    assert snapshot.status_code == 200
    assert [event["sequence"] for event in snapshot.json()["events"]] == [1]
    assert "<script>" in snapshot.text
    assert snapshot.headers["content-type"].startswith("application/json")
    assert snapshot.headers["content-security-policy"] == "default-src 'none'"
    assert snapshot.headers["cache-control"] == "no-store"

    visible_blob = client.post(
        f"/v1/runs/{RUN_ID}/blobs?visibility=shareable",
        content=b"sanitized-result",
        headers={**agent_headers, "Content-Type": "text/plain"},
    )
    hidden_blob = client.post(
        f"/v1/runs/{RUN_ID}/blobs?visibility=restricted",
        content=b"private-result",
        headers={**agent_headers, "Content-Type": "text/plain"},
    )
    assert visible_blob.status_code == 201
    assert hidden_blob.status_code == 201
    assert client.get(
        f"/v1/share/runs/{RUN_ID}/blobs/{visible_blob.json()['blob_id']}"
    ).content == b"sanitized-result"
    assert (
        client.get(
            f"/v1/share/runs/{RUN_ID}/blobs/{hidden_blob.json()['blob_id']}"
        ).status_code
        == 404
    )

    stream = client.get(
        f"/v1/share/runs/{RUN_ID}/events?once=true",
        headers={"Last-Event-ID": "0"},
    )
    assert stream.status_code == 200
    assert "id: 1" in stream.text
    assert "id: 2" not in stream.text
    resumed = client.get(
        f"/v1/share/runs/{RUN_ID}/events?once=true",
        headers={"Last-Event-ID": "1"},
    )
    assert "id: 1" not in resumed.text

    revoked = client.delete(
        f"/v1/admin/shares/{share['share_id']}", headers=admin_headers
    )
    assert revoked.status_code == 204
    assert client.get(f"/v1/share/runs/{RUN_ID}").status_code == 401


def test_auth_and_payload_limits_fail_closed() -> None:
    client = _client()
    run, batch = _trace_payloads()

    assert client.post("/v1/runs", json=run).status_code == 401
    assert (
        client.post(
            "/v1/runs",
            json=run,
            headers={"Authorization": f"Bearer {ADMIN_KEY}"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/v1/runs/{RUN_ID}/events:batch",
            json={"run_id": str(RUN_ID), "events": batch["events"] * 51},
            headers={"Authorization": f"Bearer {AGENT_KEY}"},
        ).status_code
        == 422
    )
