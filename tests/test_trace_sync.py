from __future__ import annotations

from pathlib import Path

import httpx

from netzoo_agent_core.trace_store import LocalTraceStore
from netzoo_agent_core.trace_sync import SyncStatus, TraceSyncWorker


def _three_event_run(tmp_path: Path):
    store = LocalTraceStore(tmp_path / "traces")
    run_id = store.start_run({"session_id": "sync-test", "profile_id": "panda"})
    store.append(run_id, "run.started", "agent", {"task": "demo"})
    store.append(run_id, "tool.completed", "tool", {"tool": "panda"})
    store.append(run_id, "run.finished", "agent", {"status": "completed"})
    return store, run_id


def test_sync_resumes_after_disconnect_without_duplicate_events(tmp_path: Path) -> None:
    store, run_id = _three_event_run(tmp_path)
    uploaded: list[list[int]] = []
    disconnected = False
    server_ack = 0
    server_hash = "0" * 64

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal disconnected, server_ack, server_hash
        if request.method == "POST" and request.url.path == "/v1/runs":
            return httpx.Response(201, json={"created": True})
        if request.method == "GET" and request.url.path.endswith("/sync"):
            return httpx.Response(
                200,
                json={
                    "run_id": str(run_id),
                    "accepted_count": 0,
                    "next_required_sequence": server_ack + 1,
                    "final_hash": server_hash,
                },
            )
        if request.method == "POST" and request.url.path.endswith("/events:batch"):
            body = __import__("json").loads(request.content)
            sequences = [event["sequence"] for event in body["events"]]
            if sequences == [3] and not disconnected:
                disconnected = True
                raise httpx.ConnectError("temporary offline", request=request)
            uploaded.append(sequences)
            final_hash = body["events"][-1]["event_hash"]
            server_ack = sequences[-1]
            server_hash = final_hash
            return httpx.Response(
                200,
                json={
                    "run_id": str(run_id),
                    "accepted_count": len(sequences),
                    "next_required_sequence": sequences[-1] + 1,
                    "final_hash": final_hash,
                },
            )
        raise AssertionError(f"unexpected request: {request.method} {request.url}")

    client = httpx.Client(
        base_url="https://observer.test",
        transport=httpx.MockTransport(handler),
    )
    worker = TraceSyncWorker(
        store,
        "https://observer.test",
        "agent-key-with-at-least-thirty-two-bytes",
        client=client,
        batch_size=2,
        max_attempts=3,
        sleeper=lambda _seconds: None,
        jitter=lambda: 0,
    )

    result = worker.sync_run(run_id)

    assert result.status is SyncStatus.SYNCED
    assert result.acknowledged_sequence == 3
    assert uploaded == [[1, 2], [3]]
    assert store.load_manifest(run_id).sync_ack_sequence == 3


def test_offline_sync_preserves_local_trace_and_hides_key(tmp_path: Path) -> None:
    store, run_id = _three_event_run(tmp_path)
    key = "agent-key-that-must-never-appear-in-errors"

    def offline(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"offline while using {key}", request=request)

    worker = TraceSyncWorker(
        store,
        "https://observer.test",
        key,
        client=httpx.Client(transport=httpx.MockTransport(offline)),
        max_attempts=1,
        sleeper=lambda _seconds: None,
    )

    result = worker.sync_run(run_id)

    assert result.status is SyncStatus.DEFERRED
    assert key not in (result.error or "")
    assert store.verify_run(run_id).event_count == 3
    assert store.load_manifest(run_id).sync_ack_sequence == 0
