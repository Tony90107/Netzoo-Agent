"""Best-effort background upload for durable local NetZoo traces."""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable
from uuid import UUID

import httpx
from pydantic import SecretStr

from netzoo_observer.contracts import BatchAck, EventBatch, RunCreate

from .trace_contracts import ZERO_HASH
from .trace_store import LocalTraceStore, TraceIntegrityError


class SyncStatus(str, Enum):
    SYNCED = "synced"
    DEFERRED = "deferred"
    FAILED = "failed"


class SyncIntegrityError(RuntimeError):
    pass


@dataclass(frozen=True)
class SyncResult:
    status: SyncStatus
    acknowledged_sequence: int
    uploaded_events: int = 0
    attempts: int = 1
    error: str | None = None


class TraceSyncWorker:
    """Resume trace uploads from server acknowledgements without blocking a run."""

    def __init__(
        self,
        store: LocalTraceStore,
        collector_url: str,
        agent_key: str,
        *,
        client: httpx.Client | None = None,
        agent_id: str = "netzoo-agent",
        batch_size: int = 100,
        max_attempts: int = 4,
        sleeper: Callable[[float], None] = time.sleep,
        jitter: Callable[[], float] = random.random,
    ) -> None:
        if not collector_url.startswith(("https://", "http://localhost", "http://127.0.0.1")):
            raise ValueError("collector URL must use HTTPS except on loopback")
        if not 1 <= batch_size <= 100:
            raise ValueError("sync batch size must be between 1 and 100")
        if max_attempts < 1:
            raise ValueError("sync max attempts must be positive")
        self._store = store
        self._collector_url = collector_url.rstrip("/")
        self._agent_key = SecretStr(agent_key)
        self._client = client or httpx.Client(timeout=5.0)
        self._agent_id = agent_id
        self._batch_size = batch_size
        self._max_attempts = max_attempts
        self._sleeper = sleeper
        self._jitter = jitter

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._agent_key.get_secret_value()}",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self._collector_url}{path}"

    def _validate_ack(self, run_id: UUID, ack: BatchAck) -> None:
        manifest = self._store.load_manifest(run_id)
        acknowledged = ack.next_required_sequence - 1
        if ack.run_id != run_id or acknowledged > manifest.final_sequence:
            raise SyncIntegrityError("collector acknowledgement exceeds local history")
        if acknowledged == 0:
            expected_hash = ZERO_HASH
        else:
            tail = self._store.read_events(
                run_id, after_sequence=acknowledged - 1
            )
            if not tail or tail[0].sequence != acknowledged:
                raise SyncIntegrityError("collector acknowledgement is missing locally")
            expected_hash = tail[0].event_hash
        if ack.final_hash != expected_hash:
            raise SyncIntegrityError("collector hash differs from local history")

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        response = self._client.request(
            method,
            self._url(path),
            headers=self._headers,
            timeout=5.0,
            **kwargs,
        )
        return response

    def _sync_once(self, run_id: UUID) -> tuple[int, int]:
        manifest = self._store.load_manifest(run_id)
        create_request = RunCreate(
            run_id=run_id,
            agent_id=self._agent_id,
            session_id=manifest.session_id,
            profile_id=manifest.profile_id,
            created_at=manifest.created_at,
        )
        created = self._request(
            "POST",
            "/v1/runs",
            content=create_request.model_dump_json(),
        )
        if created.status_code not in {200, 201}:
            raise SyncIntegrityError(f"collector rejected run creation ({created.status_code})")

        status_response = self._request("GET", f"/v1/runs/{run_id}/sync")
        if status_response.status_code != 200:
            raise SyncIntegrityError(
                f"collector rejected sync status ({status_response.status_code})"
            )
        ack = BatchAck.model_validate(status_response.json())
        self._validate_ack(run_id, ack)
        cursor = ack.next_required_sequence - 1
        uploaded = 0

        while True:
            local_events = self._store.read_events(run_id, after_sequence=cursor)
            if not local_events:
                self._store.update_sync_ack(run_id, cursor, ack.final_hash)
                return cursor, uploaded
            batch_events = local_events[: self._batch_size]
            batch = EventBatch(run_id=run_id, events=batch_events)
            response = self._request(
                "POST",
                f"/v1/runs/{run_id}/events:batch",
                content=batch.model_dump_json(),
            )
            if response.status_code == 409:
                body = response.json()
                required = body.get("next_required_sequence")
                if not isinstance(required, int):
                    raise SyncIntegrityError("collector reported an event digest conflict")
                status_response = self._request("GET", f"/v1/runs/{run_id}/sync")
                if status_response.status_code != 200:
                    raise SyncIntegrityError("collector gap recovery failed")
                ack = BatchAck.model_validate(status_response.json())
                if ack.next_required_sequence != required:
                    raise SyncIntegrityError("collector gap response was inconsistent")
                self._validate_ack(run_id, ack)
                cursor = required - 1
                continue
            if response.status_code != 200:
                raise SyncIntegrityError(
                    f"collector rejected event batch ({response.status_code})"
                )
            ack = BatchAck.model_validate(response.json())
            self._validate_ack(run_id, ack)
            next_cursor = ack.next_required_sequence - 1
            if next_cursor <= cursor:
                raise SyncIntegrityError("collector acknowledgement did not advance")
            uploaded += ack.accepted_count
            cursor = next_cursor
            self._store.update_sync_ack(run_id, cursor, ack.final_hash)

    def sync_run(self, run_id: UUID | str) -> SyncResult:
        run_uuid = UUID(str(run_id))
        uploaded_total = 0
        for attempt in range(1, self._max_attempts + 1):
            try:
                acknowledged, uploaded = self._sync_once(run_uuid)
                uploaded_total += uploaded
                return SyncResult(
                    status=SyncStatus.SYNCED,
                    acknowledged_sequence=acknowledged,
                    uploaded_events=uploaded_total,
                    attempts=attempt,
                )
            except httpx.RequestError:
                if attempt == self._max_attempts:
                    manifest = self._store.load_manifest(run_uuid)
                    return SyncResult(
                        status=SyncStatus.DEFERRED,
                        acknowledged_sequence=manifest.sync_ack_sequence,
                        uploaded_events=uploaded_total,
                        attempts=attempt,
                        error="collector temporarily unavailable; local trace is safe",
                    )
                delay = min(60.0, 2 ** (attempt - 1)) + self._jitter()
                self._sleeper(delay)
            except (SyncIntegrityError, TraceIntegrityError, ValueError) as error:
                manifest = self._store.load_manifest(run_uuid)
                return SyncResult(
                    status=SyncStatus.FAILED,
                    acknowledged_sequence=manifest.sync_ack_sequence,
                    uploaded_events=uploaded_total,
                    attempts=attempt,
                    error=str(error),
                )
        raise AssertionError("unreachable sync retry state")

    def start_background(
        self,
        run_id: UUID | str,
        *,
        poll_interval: float = 2.0,
    ) -> threading.Thread:
        """Poll one run in a daemon thread until a sealed trace is fully synced."""
        run_uuid = UUID(str(run_id))

        def synchronize() -> None:
            while True:
                result = self.sync_run(run_uuid)
                manifest = self._store.load_manifest(run_uuid)
                if result.status is SyncStatus.FAILED:
                    return
                if manifest.sealed and manifest.sync_ack_sequence == manifest.final_sequence:
                    return
                self._sleeper(poll_interval)

        thread = threading.Thread(
            target=synchronize,
            name=f"netzoo-trace-sync-{run_uuid}",
            daemon=True,
        )
        thread.start()
        return thread


__all__ = [
    "SyncIntegrityError",
    "SyncResult",
    "SyncStatus",
    "TraceSyncWorker",
]
