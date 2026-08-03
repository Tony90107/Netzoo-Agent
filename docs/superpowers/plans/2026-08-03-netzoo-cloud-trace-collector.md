# NetZoo Cloud Trace Collector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upload locally durable NetZoo traces to a secure central API that preserves ordering and integrity, supports live readers, and issues revocable read-only run links for the future web Dashboard.

**Architecture:** A FastAPI collector accepts authenticated run creation and contiguous event batches, persists structured records through a SQLAlchemy repository, and stores large sanitized blobs behind an object-store interface. A background `TraceSyncWorker` reads the phase-one JSONL source of truth, resumes from the server acknowledgement, and retries without blocking the Agent.

**Tech Stack:** Python 3.10, FastAPI 0.121+, Pydantic 2, SQLAlchemy 2, PostgreSQL 16 with psycopg 3 in deployment, SQLite in repository tests, boto3/S3-compatible object storage, HTTPX 0.26+, pytest.

## Global Constraints

- Cloud failure never blocks or deletes the local JSONL source of truth.
- Event identity is exactly `run_id + sequence`; duplicate digest matches are idempotent and digest mismatches are integrity failures.
- The server rejects sequence gaps and returns `next_required_sequence`.
- Agent credentials can create runs, append events, upload authorized blobs, and read sync acknowledgement only.
- Admin credentials manage budgets, retention, and share tokens; they are never Agent runtime credentials.
- Share credentials can read one run's `shareable` projection only.
- Raw credentials never enter URL queries, event payloads, application logs, or database rows.
- Share tokens use 32 random bytes, keyed hashing at rest, seven-day default expiry, revocation, rotation, and fragment-to-session exchange.
- API text fields are data, never executable HTML or instructions.

## File Structure

- Create `scripts/netzoo_observer/contracts.py`: collector request/response and auth-scope models.
- Create `scripts/netzoo_observer/settings.py`: fail-closed environment settings and secret loading.
- Create `scripts/netzoo_observer/auth.py`: keyed credential hashes and FastAPI scope dependencies.
- Create `scripts/netzoo_observer/database.py`: SQLAlchemy engine/session and schema metadata.
- Create `scripts/netzoo_observer/models.py`: run, event, blob, share, and access-session tables.
- Create `scripts/netzoo_observer/repository.py`: transactional contiguous append and sanitized reads.
- Create `scripts/netzoo_observer/blob_store.py`: object-store protocol plus filesystem test backend and S3 backend.
- Create `scripts/netzoo_observer/api.py`: FastAPI ingestion, sync, share, blob, and SSE routes.
- Create `scripts/netzoo_agent_core/trace_sync.py`: non-blocking batch upload and acknowledgement state.
- Create `tests/test_observer_contracts.py`, `tests/test_observer_repository.py`, `tests/test_observer_api.py`, and `tests/test_trace_sync.py`.
- Modify `environment.yml`, `docker-compose.yml`, `Dockerfile`, `.env.example`, and `AGENT_USAGE.md`.

---

### Task 1: Collector contracts, settings, and credential scopes

**Interfaces:**
- Consumes: phase-one `TraceEvent`, `RunManifest`, and environment variables.
- Produces: `CollectorSettings.from_environment()`, `hash_credential(secret, pepper)`, `verify_credential`, `RunCreate`, `EventBatch`, `BatchAck`, `ShareGrant`, and `AccessScope`.

- [ ] Write a failing test that rejects missing pepper, accepts a 32-byte Agent key, round-trips a phase-one event batch, and proves hashes never equal raw credentials.

```python
def test_settings_and_agent_hash_fail_closed(monkeypatch):
    monkeypatch.delenv("NETZOO_OBSERVER_CREDENTIAL_PEPPER", raising=False)
    with pytest.raises(ValueError, match="CREDENTIAL_PEPPER"):
        CollectorSettings.from_environment()

    digest = hash_credential("agent-secret", "pepper-with-at-least-32-bytes-000")
    assert digest != "agent-secret"
    assert verify_credential("agent-secret", "pepper-with-at-least-32-bytes-000", digest)
```

- [ ] Run `python -m pytest tests/test_observer_contracts.py -v`; expect import failure.
- [ ] Implement strict Pydantic contracts, URL-safe credential parsing, HMAC-SHA256 hashes, `hmac.compare_digest`, UTC expiry validation, and maximum 100 events per batch.
- [ ] Run the focused test and `ruff check` on the new package; expect all pass.
- [ ] Commit with `git commit -m "feat: define secure observer API contracts"`.

### Task 2: Transactional repository and integrity rules

**Interfaces:**
- Consumes: `RunCreate`, `list[TraceEvent]`, SQLAlchemy `Session`.
- Produces: `ObserverRepository.create_run`, `append_batch`, `sync_status`, `read_shareable_events`, `create_share`, `revoke_share`, and `exchange_share`.

- [ ] Write a failing SQLite repository test for first append, identical retry, digest-mismatch retry, and sequence gap.

```python
def test_batch_append_is_contiguous_and_idempotent(repository, two_events):
    repository.create_run(RunCreate.from_event(two_events[0]))
    first = repository.append_batch(two_events[0].run_id, two_events)
    retried = repository.append_batch(two_events[0].run_id, two_events)
    assert first.next_required_sequence == 3
    assert retried.next_required_sequence == 3
    with pytest.raises(SequenceGapError) as gap:
        repository.append_batch(two_events[0].run_id, [two_events[1].model_copy(update={"sequence": 4})])
    assert gap.value.next_required_sequence == 3
```

- [ ] Run the repository test; expect missing database modules.
- [ ] Implement tables with unique `(run_id, sequence)`, unique `event_id`, immutable event JSON, event hash, visibility, indexed event type/time, hashed credentials, and UTC timestamps.
- [ ] Implement one transaction that locks the run row, compares duplicate digests, rejects gaps, appends contiguous events, and updates acknowledgement only after commit.
- [ ] Add tests for visibility filtering, expired/revoked shares, and rollback after the middle event fails.
- [ ] Run repository tests on SQLite and a PostgreSQL container smoke; expect identical observable behavior.
- [ ] Commit with `git commit -m "feat: persist contiguous observer event batches"`.

### Task 3: FastAPI ingestion, share, blob, and live routes

**Interfaces:**
- Consumes: repository, blob-store protocol, scoped credentials.
- Produces: `create_app(settings, repository, blob_store) -> FastAPI` and the approved `/v1` routes.

- [ ] Write failing HTTPX tests for Agent-key run creation/batch append, unauthorized read, admin share creation, fragment-token exchange, revoked session, and shareable-only event reads.

```python
def test_agent_can_append_but_cannot_read(client, agent_headers, run_payload, batch_payload):
    assert client.post("/v1/runs", json=run_payload, headers=agent_headers).status_code == 201
    assert client.post(f"/v1/runs/{run_payload['run_id']}/events:batch", json=batch_payload, headers=agent_headers).status_code == 200
    assert client.get(f"/v1/share/runs/{run_payload['run_id']}", headers=agent_headers).status_code == 403
```

- [ ] Run API tests; expect `create_app` import failure.
- [ ] Implement create run, batch append, sync status, bounded blob upload, admin share create/revoke, share exchange to Secure/HttpOnly/SameSite=Strict cookie, sanitized snapshot/events, and SSE with `Last-Event-ID` resume.
- [ ] Add `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, CSP, `X-Content-Type-Options`, body-size limits, escaped JSON responses, and request logs that exclude Authorization/cookie/body.
- [ ] Test expired tokens, 101-event rejection, cross-run blob access, malicious HTML as inert JSON text, and SSE reconnection.
- [ ] Commit with `git commit -m "feat: expose secure trace collector and share API"`.

### Task 4: Local TraceSyncWorker

**Interfaces:**
- Consumes: `LocalTraceStore`, collector base URL, Agent key, HTTPX transport.
- Produces: `TraceSyncWorker.sync_run(run_id) -> SyncResult` and manifest `sync_ack_sequence` updates.

- [ ] Write a failing test whose fake transport accepts events 1–2, disconnects, then requires event 3; assert the worker retries without duplicating acknowledged events.
- [ ] Run `python -m pytest tests/test_trace_sync.py -v`; expect missing module.
- [ ] Implement batches of at most 100 events, 5-second request timeout, exponential backoff with jitter capped at 60 seconds, server-directed gap recovery, digest mismatch hard failure, and atomic acknowledgement persistence.
- [ ] Add tests for offline no-op, duplicate acknowledgement, server-behind recovery, server-ahead integrity failure, and secret-free error output.
- [ ] Integrate the worker as a daemon background thread only when collector URL and Agent key are configured; Agent task execution never waits for retry sleep.
- [ ] Commit with `git commit -m "feat: sync durable traces to the collector"`.

### Task 5: Deployment, integration, and security verification

**Interfaces:**
- Consumes: collector image, PostgreSQL, MinIO-compatible S3, NetZoo Agent.
- Produces: reproducible Docker Compose deployment and end-to-end Collector acceptance.

- [ ] Add pinned FastAPI, Uvicorn, SQLAlchemy, psycopg binary, HTTPX, and boto3 dependencies to `environment.yml`; add collector startup healthcheck.
- [ ] Extend Compose with `observer-api`, `observer-db`, and `observer-object-store`, private internal networks, named volumes, health dependencies, no default database/object-store host exposure, and explicit secret environment variables.
- [ ] Write an end-to-end test that creates a local toy trace, syncs it, reconnects SSE from a sequence, creates/exchanges/revokes a share, and verifies event/hash/token totals.
- [ ] Run unit tests, PostgreSQL integration, Docker healthcheck, secret scan, rate/body-limit tests, and `ruff check`.
- [ ] Document startup, key generation, rotation, backup, retention, and the boundary between Collector API and the next-stage web Dashboard.
- [ ] Commit with `git commit -m "feat: deploy the NetZoo trace collector"`.

## Definition of Done

- A local run reaches the collector after an offline interval without gaps or duplicates.
- Digest conflicts and sequence gaps fail closed with actionable acknowledgement data.
- Agent, admin, and share scopes cannot substitute for one another.
- A revoked or expired share immediately loses read access.
- Only `shareable` projections and authorized blobs are readable.
- SSE resumes from the last event id.
- No credential appears in URLs, logs, events, database credential fields, or test output.
- The deployment runs with PostgreSQL and S3-compatible object storage and exposes a health endpoint for the future web Dashboard.

