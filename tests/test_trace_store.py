import sys
import json
import os
import tarfile
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.trace_store import (  # noqa: E402
    LocalTraceStore,
    TraceIntegrityError,
    TraceStorageError,
)
from netzoo_agent_core.session import cleanup_trace_storage  # noqa: E402


def test_store_appends_a_contiguous_private_hash_chain(tmp_path: Path):
    store = LocalTraceStore(tmp_path / "traces")
    run_id = store.start_run({"session_id": "demo", "profile_id": "default"})

    first = store.append(run_id, "run.started", "cli", {"status": "running"})
    second = store.append(
        run_id,
        "policy.loaded",
        "apply_project_policy",
        {"version": 1},
    )
    verification = store.verify_run(run_id)

    assert [first.sequence, second.sequence] == [1, 2]
    assert second.previous_hash == first.event_hash
    assert verification.valid is True
    assert verification.event_count == 2
    assert (store.root / str(run_id)).stat().st_mode & 0o777 == 0o700
    assert (store.root / str(run_id) / "events.jsonl").stat().st_mode & 0o777 == 0o600


def test_store_redacts_before_jsonl_and_never_persists_the_secret(tmp_path: Path):
    store = LocalTraceStore(tmp_path / "traces")
    run_id = store.start_run({"session_id": "demo", "profile_id": "default"})

    event = store.append(
        run_id,
        "llm.completed",
        "classify",
        {"Authorization": "Bearer sk-or-v1-never-write-this", "total_tokens": 9},
    )

    persisted = (store.run_path(run_id) / "events.jsonl").read_text()
    assert "never-write-this" not in persisted
    assert event.payload["Authorization"] == "[REDACTED]"
    assert event.payload["redactions"] == [
        {"path": "$.Authorization", "reason": "sensitive_key"}
    ]


def test_store_detects_a_modified_persisted_event(tmp_path: Path):
    store = LocalTraceStore(tmp_path / "traces")
    run_id = store.start_run({"session_id": "demo", "profile_id": "default"})
    store.append(run_id, "run.started", "cli", {"status": "running"})
    path = store.run_path(run_id) / "events.jsonl"
    payload = json.loads(path.read_text())
    payload["payload"]["status"] = "changed"
    path.write_text(json.dumps(payload) + "\n")

    with pytest.raises(TraceIntegrityError, match="hash is invalid"):
        store.verify_run(run_id)


def test_pending_run_can_resume_but_completed_run_is_sealed(tmp_path: Path):
    store = LocalTraceStore(tmp_path / "traces")
    run_id = store.start_run({"session_id": "demo", "profile_id": "default"})
    store.append(run_id, "run.started", "cli", {"status": "running"})

    store.pause_run(run_id, {"reason": "needs_input"})
    resumed = store.append(run_id, "run.resumed", "cli", {"status": "running"})
    manifest = store.finish_run(run_id, "completed", {"result": "ok"})

    assert resumed.event_type == "run.resumed"
    assert manifest.status == "completed"
    assert manifest.sealed is True
    with pytest.raises(TraceStorageError, match="sealed"):
        store.append(run_id, "node.started", "classify", {})


def test_concurrent_append_produces_one_contiguous_chain(tmp_path: Path):
    store = LocalTraceStore(tmp_path / "traces")
    run_id = store.start_run({"session_id": "demo", "profile_id": "default"})

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(
            executor.map(
                lambda index: store.append(
                    run_id,
                    "node.finished",
                    "worker",
                    {"index": index},
                ),
                range(40),
            )
        )

    events = store.read_events(run_id)
    assert [event.sequence for event in events] == list(range(1, 41))
    assert store.verify_run(run_id).valid is True


def test_export_refuses_overwrite_and_uses_fixed_archive_paths(tmp_path: Path):
    store = LocalTraceStore(tmp_path / "traces")
    run_id = store.start_run({"session_id": "demo", "profile_id": "default"})
    store.append(run_id, "run.started", "cli", {"status": "running"})
    store.finish_run(run_id, "completed", {"result": "ok"})
    archive = tmp_path / "audit.tar.gz"

    store.export_run(run_id, archive)

    with tarfile.open(archive) as package:
        assert package.getnames() == ["events.jsonl", "manifest.json"]
    with pytest.raises(FileExistsError):
        store.export_run(run_id, archive)


def test_partial_final_line_requires_explicit_repair_and_is_quarantined(tmp_path: Path):
    store = LocalTraceStore(tmp_path / "traces")
    run_id = store.start_run({"session_id": "demo", "profile_id": "default"})
    store.append(run_id, "run.started", "cli", {"status": "running"})
    events_path = store.run_path(run_id) / "events.jsonl"
    with events_path.open("ab") as stream:
        stream.write(b'{"sequence":2')

    with pytest.raises(TraceIntegrityError, match="invalid trace event"):
        store.verify_run(run_id)

    quarantine = store.repair_partial_tail(run_id)

    assert quarantine.read_bytes() == b'{"sequence":2'
    assert quarantine.stat().st_mode & 0o777 == 0o600
    assert store.verify_run(run_id).valid is True


def test_trace_retention_removes_only_old_sealed_runs(tmp_path: Path):
    root = tmp_path / "traces"
    store = LocalTraceStore(root)
    sealed_id = store.start_run({"session_id": "sealed", "profile_id": "default"})
    pending_id = store.start_run({"session_id": "pending", "profile_id": "default"})
    store.finish_run(sealed_id, "completed", {"result": "ok"})
    store.pause_run(pending_id, {"reason": "needs_input"})
    manifest_path = store.run_path(sealed_id) / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    old = datetime.now(timezone.utc) - timedelta(days=100)
    manifest["finished_at"] = old.isoformat().replace("+00:00", "Z")
    manifest["updated_at"] = manifest["finished_at"]
    manifest_path.write_text(json.dumps(manifest))
    os.utime(manifest_path, (old.timestamp(), old.timestamp()))
    os.utime(store.run_path(sealed_id), (old.timestamp(), old.timestamp()))

    removed = cleanup_trace_storage(90, trace_root=root)

    assert removed == 1
    assert not store.run_path(sealed_id).exists()
    assert store.run_path(pending_id).exists()
