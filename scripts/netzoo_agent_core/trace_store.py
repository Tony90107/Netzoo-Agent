"""Durable append-only local storage for NetZoo trace events."""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import tarfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict

from .trace_contracts import (
    ZERO_HASH,
    RunManifest,
    TraceEvent,
    Visibility,
    canonical_json,
)
from .trace_redaction import sanitize_payload


__all__ = [
    "LocalTraceStore",
    "RunVerification",
    "TraceIntegrityError",
    "TraceStorageError",
]


class TraceStorageError(RuntimeError):
    """Raised when the recorder cannot durably persist an event."""


class TraceIntegrityError(TraceStorageError):
    """Raised when a stored hash chain or manifest is inconsistent."""


class RunVerification(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    valid: bool
    event_count: int
    final_sequence: int
    final_hash: str
    status: str
    sealed: bool


class LocalTraceStore:
    """Manage private per-run JSONL chains beneath one configured root."""

    minimum_free_bytes = 10 * 1024 * 1024

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self._locks: dict[UUID, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def preflight(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)
        if shutil.disk_usage(self.root).free < self.minimum_free_bytes:
            raise TraceStorageError("trace storage has less than 10 MiB free")
        smoke = self.root / f".preflight-{uuid4().hex}"
        try:
            descriptor = os.open(smoke, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                os.write(descriptor, b"ok")
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        except OSError as error:
            raise TraceStorageError("trace storage preflight write failed") from error
        finally:
            try:
                smoke.unlink()
            except FileNotFoundError:
                pass

    def _run_id(self, run_id: UUID | str) -> UUID:
        try:
            return run_id if isinstance(run_id, UUID) else UUID(str(run_id))
        except (TypeError, ValueError) as error:
            raise TraceStorageError("run id must be a UUID") from error

    def run_path(self, run_id: UUID | str) -> Path:
        parsed = self._run_id(run_id)
        path = (self.root / str(parsed)).resolve()
        if path.parent != self.root:
            raise TraceStorageError("trace run path escaped the configured root")
        return path

    def _manifest_path(self, run_id: UUID | str) -> Path:
        return self.run_path(run_id) / "manifest.json"

    def _events_path(self, run_id: UUID | str) -> Path:
        return self.run_path(run_id) / "events.jsonl"

    def _lock_for(self, run_id: UUID) -> threading.Lock:
        with self._locks_guard:
            return self._locks.setdefault(run_id, threading.Lock())

    def _write_json_atomic(self, path: Path, value: dict) -> None:
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        try:
            data = (canonical_json(value) + "\n").encode("utf-8")
            os.write(descriptor, data)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary, path)
        os.chmod(path, 0o600)

    def _load_manifest(self, run_id: UUID | str) -> RunManifest:
        path = self._manifest_path(run_id)
        try:
            return RunManifest.model_validate_json(path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise TraceStorageError(f"trace run does not exist: {run_id}") from error
        except (OSError, ValueError) as error:
            raise TraceIntegrityError(f"trace manifest is invalid: {run_id}") from error

    def load_manifest(self, run_id: UUID | str) -> RunManifest:
        """Return validated run metadata for status and synchronization clients."""
        return self._load_manifest(run_id)

    def start_run(self, context: dict) -> UUID:
        self.preflight()
        session_id = str(context.get("session_id") or "").strip()
        profile_id = str(context.get("profile_id") or "default").strip()
        if not session_id or not profile_id:
            raise TraceStorageError("session_id and profile_id are required")
        run_id = uuid4()
        run_path = self.run_path(run_id)
        run_path.mkdir(mode=0o700)
        os.chmod(run_path, 0o700)
        blobs = run_path / "blobs"
        blobs.mkdir(mode=0o700)
        events_path = run_path / "events.jsonl"
        lock_path = run_path / "events.lock"
        for path in (events_path, lock_path):
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(descriptor)
        now = datetime.now(timezone.utc)
        manifest = RunManifest(
            run_id=run_id,
            session_id=session_id,
            profile_id=profile_id,
            created_at=now,
            updated_at=now,
        )
        self._write_json_atomic(
            self._manifest_path(run_id),
            manifest.model_dump(mode="json"),
        )
        return run_id

    def append(
        self,
        run_id: UUID | str,
        event_type: str,
        node: str,
        payload: dict,
        *,
        parent_event_id: UUID | str | None = None,
        visibility: Visibility = "shareable",
        occurred_at: datetime | None = None,
    ) -> TraceEvent:
        parsed_run_id = self._run_id(run_id)
        local_lock = self._lock_for(parsed_run_id)
        lock_path = self.run_path(parsed_run_id) / "events.lock"
        with local_lock, lock_path.open("r+b") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                manifest = self._load_manifest(parsed_run_id)
                if manifest.sealed:
                    raise TraceStorageError("cannot append to a sealed trace run")
                sanitized, redactions = sanitize_payload(payload)
                if not isinstance(sanitized, dict):
                    raise TraceStorageError("trace payload must serialize to an object")
                if redactions:
                    sanitized["redactions"] = [
                        item.model_dump(mode="json") for item in redactions
                    ]
                event = TraceEvent.create(
                    run_id=parsed_run_id,
                    sequence=manifest.final_sequence + 1,
                    event_type=event_type,
                    node=node,
                    payload=sanitized,
                    previous_hash=manifest.final_hash,
                    parent_event_id=parent_event_id,
                    visibility=visibility,
                    occurred_at=occurred_at,
                )
                descriptor = os.open(
                    self._events_path(parsed_run_id),
                    os.O_WRONLY | os.O_APPEND,
                )
                try:
                    os.write(
                        descriptor,
                        (canonical_json(event.model_dump(mode="json")) + "\n").encode(
                            "utf-8"
                        ),
                    )
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
                updated = manifest.model_copy(
                    update={
                        "updated_at": datetime.now(timezone.utc),
                        "event_count": event.sequence,
                        "final_sequence": event.sequence,
                        "final_hash": event.event_hash,
                    }
                )
                self._write_json_atomic(
                    self._manifest_path(parsed_run_id),
                    updated.model_dump(mode="json"),
                )
                return event
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def read_events(
        self,
        run_id: UUID | str,
        *,
        after_sequence: int = 0,
    ) -> list[TraceEvent]:
        path = self._events_path(run_id)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError as error:
            raise TraceStorageError(f"trace run does not exist: {run_id}") from error
        events: list[TraceEvent] = []
        for line_number, line in enumerate(lines, start=1):
            if not line:
                raise TraceIntegrityError(f"blank trace line at {line_number}")
            try:
                event = TraceEvent.model_validate(json.loads(line))
            except (ValueError, TypeError) as error:
                raise TraceIntegrityError(
                    f"invalid trace event at line {line_number}"
                ) from error
            if event.sequence > after_sequence:
                events.append(event)
        return events

    def verify_run(self, run_id: UUID | str) -> RunVerification:
        parsed_run_id = self._run_id(run_id)
        events = self.read_events(parsed_run_id)
        expected_previous = ZERO_HASH
        for expected_sequence, event in enumerate(events, start=1):
            if event.run_id != parsed_run_id:
                raise TraceIntegrityError(f"event {expected_sequence} has the wrong run id")
            if event.sequence != expected_sequence:
                raise TraceIntegrityError(f"event sequence gap at {expected_sequence}")
            if event.previous_hash != expected_previous:
                raise TraceIntegrityError(
                    f"event {expected_sequence} has the wrong previous hash"
                )
            if not event.verify():
                raise TraceIntegrityError(f"event {expected_sequence} hash is invalid")
            expected_previous = event.event_hash
        manifest = self._load_manifest(parsed_run_id)
        if manifest.event_count != len(events):
            raise TraceIntegrityError("manifest event count does not match JSONL")
        if manifest.final_sequence != len(events):
            raise TraceIntegrityError("manifest final sequence does not match JSONL")
        if manifest.final_hash != expected_previous:
            raise TraceIntegrityError("manifest final hash does not match JSONL")
        return RunVerification(
            valid=True,
            event_count=len(events),
            final_sequence=manifest.final_sequence,
            final_hash=manifest.final_hash,
            status=manifest.status,
            sealed=manifest.sealed,
        )

    def _replace_manifest(self, manifest: RunManifest, **updates) -> RunManifest:
        values = manifest.model_dump(mode="json")
        values.update(updates)
        updated = RunManifest.model_validate(values)
        self._write_json_atomic(
            self._manifest_path(updated.run_id),
            updated.model_dump(mode="json"),
        )
        return updated

    def update_sync_ack(
        self,
        run_id: UUID | str,
        acknowledged_sequence: int,
        final_hash: str,
    ) -> RunManifest:
        """Atomically advance the cloud acknowledgement after hash validation."""
        parsed_run_id = self._run_id(run_id)
        local_lock = self._lock_for(parsed_run_id)
        lock_path = self.run_path(parsed_run_id) / "events.lock"
        with local_lock, lock_path.open("r+b") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                manifest = self._load_manifest(parsed_run_id)
                if acknowledged_sequence < manifest.sync_ack_sequence:
                    return manifest
                if acknowledged_sequence > manifest.final_sequence:
                    raise TraceIntegrityError(
                        "sync acknowledgement exceeds the local event stream"
                    )
                expected_hash = ZERO_HASH
                if acknowledged_sequence:
                    events = self.read_events(
                        parsed_run_id,
                        after_sequence=acknowledged_sequence - 1,
                    )
                    if not events or events[0].sequence != acknowledged_sequence:
                        raise TraceIntegrityError(
                            "sync acknowledgement event is missing locally"
                        )
                    expected_hash = events[0].event_hash
                if final_hash != expected_hash:
                    raise TraceIntegrityError(
                        "sync acknowledgement hash differs from the local event"
                    )
                return self._replace_manifest(
                    manifest,
                    sync_ack_sequence=acknowledged_sequence,
                    updated_at=datetime.now(timezone.utc),
                )
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def pause_run(self, run_id: UUID | str, summary: dict) -> RunManifest:
        """Record a resumable pause while leaving the event stream appendable."""
        self.append(
            run_id,
            "run.paused",
            "cli",
            {"status": "pending", **summary},
        )
        manifest = self._load_manifest(run_id)
        return self._replace_manifest(
            manifest,
            status="pending",
            updated_at=datetime.now(timezone.utc),
        )

    def finish_run(
        self,
        run_id: UUID | str,
        status: str,
        summary: dict,
    ) -> RunManifest:
        """Append the terminal event and seal a completed or failed run."""
        if status not in {"completed", "failed"}:
            raise TraceStorageError("terminal trace status must be completed or failed")
        self.append(
            run_id,
            "run.finished",
            "cli",
            {"status": status, **summary},
        )
        manifest = self._load_manifest(run_id)
        now = datetime.now(timezone.utc)
        return self._replace_manifest(
            manifest,
            status=status,
            updated_at=now,
            finished_at=now,
            sealed=True,
        )

    def export_run(self, run_id: UUID | str, destination: Path) -> Path:
        """Create a verified non-overwriting local audit archive."""
        self.verify_run(run_id)
        destination = Path(destination)
        if destination.exists():
            raise FileExistsError(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        run_path = self.run_path(run_id)
        with tarfile.open(destination, mode="x:gz") as archive:
            archive.add(run_path / "events.jsonl", arcname="events.jsonl")
            archive.add(run_path / "manifest.json", arcname="manifest.json")
        return destination

    def repair_partial_tail(self, run_id: UUID | str) -> Path:
        """Quarantine and remove only an incomplete, non-newline final JSONL suffix."""
        parsed_run_id = self._run_id(run_id)
        local_lock = self._lock_for(parsed_run_id)
        lock_path = self.run_path(parsed_run_id) / "events.lock"
        events_path = self._events_path(parsed_run_id)
        with local_lock, lock_path.open("r+b") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                data = events_path.read_bytes()
                last_newline = data.rfind(b"\n")
                if not data or last_newline == len(data) - 1:
                    raise TraceStorageError("trace has no incomplete final line to repair")
                if last_newline < 0:
                    raise TraceIntegrityError("trace has no complete event before the partial tail")
                valid_prefix = data[: last_newline + 1]
                corrupt_suffix = data[last_newline + 1 :]
                for line_number, line in enumerate(valid_prefix.splitlines(), start=1):
                    try:
                        event = TraceEvent.model_validate_json(line)
                    except ValueError as error:
                        raise TraceIntegrityError(
                            f"complete event {line_number} is invalid; partial repair refused"
                        ) from error
                    if not event.verify():
                        raise TraceIntegrityError(
                            f"complete event {line_number} hash is invalid; partial repair refused"
                        )
                quarantine = self.run_path(parsed_run_id) / "events.corrupt"
                if quarantine.exists():
                    quarantine = self.run_path(parsed_run_id) / f"events-{uuid4().hex}.corrupt"
                descriptor = os.open(
                    quarantine,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o600,
                )
                try:
                    os.write(descriptor, corrupt_suffix)
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
                with events_path.open("r+b") as stream:
                    stream.truncate(last_newline + 1)
                    stream.flush()
                    os.fsync(stream.fileno())
                self.verify_run(parsed_run_id)
                return quarantine
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
