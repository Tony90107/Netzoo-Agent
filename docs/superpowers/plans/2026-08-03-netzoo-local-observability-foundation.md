# NetZoo Local Observability Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the local, append-only NetZoo trace foundation that records graph, LLM, tool, recovery, token, cost-provenance, and budget events without depending on the future cloud service or Dashboard.

**Architecture:** A versioned `TraceEvent` envelope is sanitized and appended to a per-run JSONL hash chain by `LocalTraceStore`. A small `TraceRecorder` is injected into the CLI and LangGraph orchestration; graph wrappers record node boundaries while domain events preserve plan, evaluation, tool, and budget meaning. Session checkpoints retain the run id so clarification and crash recovery append to the original trace.

**Tech Stack:** Python 3.10, Pydantic 2, Python standard library (`hashlib`, `json`, `os`, `uuid`, `pathlib`), LangGraph 1.x, unittest/pytest.

## Global Constraints

- Every observable event must be durably appended locally before the next Agent boundary begins.
- Never record or infer hidden chain-of-thought; record typed decisions, evidence references, reason codes, and state deltas only.
- Redact API keys, authorization values, cookies, passwords, private keys, and sensitive environment values before the first local trace write.
- Use `.netzoo/traces/<run_id>/events.jsonl`, monotonically increasing `sequence`, canonical JSON, `previous_hash`, and `event_hash`.
- Default per-task hard limit is exactly 20,000 tokens; warn at 14,000 and 17,000; reserve 1,500 tokens for safe finalization.
- A running deterministic scientific tool may finish after a budget warning, but no new LLM-dependent step may start after a hard block.
- Provider-reported usage and cost are `actual`; locally derived values are `estimated`; missing trustworthy prices are `unavailable`, never zero.
- Agent-authored CLI text remains English, matching the project policy.
- Preserve the historical `scripts/netzoo_agent.py` import facade and existing session callers.
- Do not modify unrelated dirty-worktree files, especially `scripts/netzoo_agent_core/memory.py` and `tests/test_agent_stability.py`.

## File Structure

### New files

- `scripts/netzoo_agent_core/trace_contracts.py`: versioned trace, manifest, pricing, and budget Pydantic contracts plus canonical hashing.
- `scripts/netzoo_agent_core/trace_redaction.py`: allowlist-first recursive sanitizer and secret-pattern scanner.
- `scripts/netzoo_agent_core/trace_store.py`: atomic per-run JSONL append, manifest lifecycle, preflight, integrity verification, and export.
- `scripts/netzoo_agent_core/tracing.py`: `TraceRecorder`, graph-node wrapper, domain-event helpers, and no-op recorder.
- `scripts/netzoo_agent_core/pricing.py`: provider metadata extraction and immutable environment-configured price snapshots.
- `tests/test_trace_contracts.py`: event, hash, manifest, pricing, and budget model tests.
- `tests/test_trace_redaction.py`: nested secret and log scanner tests.
- `tests/test_trace_store.py`: durability, permissions, concurrency, corruption, resume, and export tests.
- `tests/test_graph_tracing.py`: graph event ordering, failure, recovery, LLM, tool, and resume integration tests.

### Modified files

- `scripts/netzoo_agent_core/contracts.py`: add `TRACE_ROOT`, typed LLM-call details, budget state, and trace fields in `AgentState`.
- `scripts/netzoo_agent_core/llm.py`: return structured usage/cost provenance and a `BudgetDecision` preflight.
- `scripts/netzoo_agent_core/graph.py`: accept a recorder, wrap every node, and emit domain events.
- `scripts/netzoo_agent_core/session.py`: persist and restore `run_id`; include trace directories in retention.
- `scripts/netzoo_agent_core/cli.py`: create/resume/finalize traces and expose local status/export commands.
- `scripts/netzoo_agent_core/__init__.py`: export stable trace interfaces.
- `scripts/netzoo_agent.py`: include new implementation modules in the compatibility facade.
- `scripts/netzoo_agent_core/runtime.py`: propagate `TRACE_ROOT` in legacy runtime overrides.
- `AGENT_USAGE.md`: document local trace files, budget semantics, export, and privacy guarantees.

---

### Task 1: Versioned trace and budget contracts

**Files:**
- Create: `scripts/netzoo_agent_core/trace_contracts.py`
- Create: `tests/test_trace_contracts.py`
- Modify: `scripts/netzoo_agent_core/contracts.py:177-237`

**Interfaces:**
- Consumes: Pydantic `BaseModel`, `Field`, and `ConfigDict`; Python UTC datetimes and SHA-256.
- Produces: `TraceEvent.create(**values)`, `TraceEvent.verify()`, `RunManifest`, `LLMCallUsage`, `PriceSnapshot`, `BudgetDecision`, `canonical_json(value)`, and `TRACE_ROOT`.

- [ ] **Step 1: Write failing event-chain and immutable-contract tests**

```python
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from netzoo_agent_core.trace_contracts import TraceEvent


def test_trace_event_hashes_canonical_payload_and_previous_hash():
    event = TraceEvent.create(
        run_id="11111111-1111-4111-8111-111111111111",
        sequence=1,
        event_type="run.started",
        node="cli",
        payload={"workflow": "PANDA", "status": "running"},
        previous_hash="0" * 64,
        occurred_at=datetime(2026, 8, 3, tzinfo=timezone.utc),
    )

    assert event.verify()
    assert len(event.event_hash) == 64
    assert event.model_copy(update={"payload": {"status": "changed"}}).verify() is False


def test_trace_event_rejects_non_uuid_run_and_zero_sequence():
    with pytest.raises(ValidationError):
        TraceEvent.create(
            run_id="session-name",
            sequence=0,
            event_type="run.started",
            node="cli",
            payload={},
            previous_hash="0" * 64,
        )
```

- [ ] **Step 2: Run the focused tests and verify the module is missing**

Run: `python -m pytest tests/test_trace_contracts.py -v`

Expected: collection fails with `ModuleNotFoundError: No module named 'netzoo_agent_core.trace_contracts'`.

- [ ] **Step 3: Implement strict contracts and canonical hashing**

Create frozen models with these exact public fields and validation boundaries:

```python
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

ZERO_HASH = "0" * 64
Visibility = Literal["shareable", "restricted", "local_only"]


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


class TraceEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1] = 1
    event_id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    sequence: int = Field(ge=1)
    event_type: str = Field(min_length=3, max_length=80, pattern=r"^[a-z][a-z0-9_.-]+$")
    occurred_at: datetime
    recorded_at: datetime
    node: str = Field(min_length=1, max_length=80)
    parent_event_id: UUID | None = None
    visibility: Visibility = "shareable"
    payload: dict
    previous_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    event_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    def hash_material(self) -> dict:
        return self.model_dump(mode="json", exclude={"event_hash"})

    def verify(self) -> bool:
        digest = hashlib.sha256(canonical_json(self.hash_material()).encode()).hexdigest()
        return digest == self.event_hash

    @classmethod
    def create(cls, *, occurred_at: datetime | None = None, **values) -> "TraceEvent":
        now = datetime.now(timezone.utc)
        provisional = cls(
            occurred_at=occurred_at or now,
            recorded_at=now,
            event_hash=ZERO_HASH,
            **values,
        )
        digest = hashlib.sha256(
            canonical_json(provisional.hash_material()).encode()
        ).hexdigest()
        return provisional.model_copy(update={"event_hash": digest})
```

In the same module, define these frozen models and exact fields:

- `RunManifest`: schema version, run UUID, session id, profile id, created/updated/finished timestamps, status (`running`, `pending`, `completed`, `failed`, `interrupted`, `trace_degraded`), event count, final sequence, final hash, acknowledged sync sequence, and sealed flag.
- `PriceSnapshot`: snapshot UUID, exact model name, provenance (`estimated` or `unavailable`), effective timestamp, and nullable integer input/output micro-USD-per-million rates.
- `LLMCallUsage`: call UUID, role, model, nullable provider request id, input/output/cache/total tokens, usage provenance, nullable cost micro-USD, nullable price snapshot, duration milliseconds, and status (`success`, `failed`, `blocked`).
- `BudgetDecision`: status (`allowed`, `warning_70`, `warning_85`, `blocked`), consumed, estimated input, reserved output, projected, hard-limit, and reserve token counts.

Monetary values use integer micro-USD to avoid float drift. Token and duration values are non-negative integers; `total_tokens` must equal input plus output plus cache-write tokens under the selected provider normalization rule.

- [ ] **Step 4: Add `TRACE_ROOT` and replace untyped LLM calls**

In `contracts.py`, define `TRACE_ROOT = PROJECT_ROOT / ".netzoo" / "traces"`, export it, add `run_id: NotRequired[str]` to `AgentState`, and change `LLMUsage.calls` from `list[dict]` to `list[LLMCallUsage]`. Import `LLMCallUsage` from `trace_contracts`; do not move unrelated workflow contracts.

- [ ] **Step 5: Run contract and existing token tests**

Run: `python -m pytest tests/test_trace_contracts.py tests/test_agent_gate.py -k 'token_usage or budget' -v`

Expected: all selected tests pass; serialized `LLMUsage.model_dump()` still contains dictionaries under `calls`.

- [ ] **Step 6: Commit the contracts**

```bash
git add scripts/netzoo_agent_core/trace_contracts.py scripts/netzoo_agent_core/contracts.py tests/test_trace_contracts.py
git commit -m "feat: define versioned NetZoo trace contracts"
```

---

### Task 2: Secret redaction before local persistence

**Files:**
- Create: `scripts/netzoo_agent_core/trace_redaction.py`
- Create: `tests/test_trace_redaction.py`

**Interfaces:**
- Consumes: JSON-compatible dict/list/scalar payloads and plain-text tool logs.
- Produces: `sanitize_payload(value) -> tuple[object, list[Redaction]]` and `sanitize_text(text) -> tuple[str, list[Redaction]]`.

- [ ] **Step 1: Write failing nested-secret and value-pattern tests**

```python
from netzoo_agent_core.trace_redaction import sanitize_payload, sanitize_text


def test_sanitize_payload_removes_named_and_embedded_secrets():
    value = {
        "headers": {"Authorization": "Bearer sk-or-v1-secret-value"},
        "OPENROUTER_API_KEY": "sk-or-v1-second-secret",
        "arguments": {"expression_file": "data/expression.tsv"},
    }

    sanitized, redactions = sanitize_payload(value)

    assert sanitized["headers"]["Authorization"] == "[REDACTED]"
    assert sanitized["OPENROUTER_API_KEY"] == "[REDACTED]"
    assert sanitized["arguments"]["expression_file"] == "data/expression.tsv"
    assert {item.reason for item in redactions} == {"sensitive_key"}


def test_sanitize_text_masks_private_key_and_cookie_without_echoing_original():
    raw = "Cookie: session=abc123\n-----BEGIN PRIVATE KEY-----\nsecret\n-----END PRIVATE KEY-----"
    sanitized, redactions = sanitize_text(raw)

    assert "abc123" not in sanitized
    assert "PRIVATE KEY" not in sanitized
    assert len(redactions) == 2
```

- [ ] **Step 2: Run tests and verify the redaction module is missing**

Run: `python -m pytest tests/test_trace_redaction.py -v`

Expected: collection fails with `ModuleNotFoundError`.

- [ ] **Step 3: Implement allowlist-first recursive sanitization**

Define a frozen `Redaction(path: str, reason: Literal["sensitive_key", "secret_pattern", "unsupported_type"])`. Normalize keys with `casefold()` and remove punctuation before matching `authorization`, `cookie`, `password`, `secret`, `token`, `api_key`, `private_key`, and credential-bearing environment names. Preserve safe file-role keys such as `input_tokens`, `output_tokens`, and `token_usage` through an explicit allowlist.

Use compiled patterns for Bearer values, OpenRouter-style keys, PEM private-key blocks, cookie headers, and common `NAME=value` secrets. Replacement is always `[REDACTED]`; the `Redaction` stores only path and reason, never the original substring.

```python
SAFE_TOKEN_KEYS = frozenset({"input_tokens", "output_tokens", "total_tokens", "token_usage"})
SENSITIVE_KEY_PARTS = frozenset({"authorization", "cookie", "password", "secret", "apikey", "privatekey"})


def _normalized_key(key: str) -> str:
    return "".join(character for character in key.casefold() if character.isalnum())


def _is_sensitive_key(key: str) -> bool:
    normalized = _normalized_key(key)
    if key.casefold() in SAFE_TOKEN_KEYS:
        return False
    return normalized == "token" or any(part in normalized for part in SENSITIVE_KEY_PARTS)
```

- [ ] **Step 4: Add depth, item-count, and unsupported-type bounds**

Reject recursion deeper than 12 levels, truncate lists after 1,000 items with a structured marker, and convert `Path`, UUID, datetime, and Pydantic models through their public serialized forms. For an unsupported object, emit `[UNSUPPORTED:<type name>]` and an `unsupported_type` redaction instead of calling arbitrary `repr()`.

- [ ] **Step 5: Run redaction tests and a repository secret fixture scan**

Run: `python -m pytest tests/test_trace_redaction.py -v`

Expected: all tests pass, and no assertion output contains the test secret values.

- [ ] **Step 6: Commit redaction**

```bash
git add scripts/netzoo_agent_core/trace_redaction.py tests/test_trace_redaction.py
git commit -m "feat: redact secrets before trace persistence"
```

---

### Task 3: Durable append-only local trace store

**Files:**
- Create: `scripts/netzoo_agent_core/trace_store.py`
- Create: `tests/test_trace_store.py`

**Interfaces:**
- Consumes: `TraceEvent`, sanitized payloads, a root `Path`, and UUID run ids.
- Produces: `LocalTraceStore.preflight()`, `start_run(context)`, `append(run_id, event_type, node, payload)`, `pause_run(run_id, summary)`, `finish_run(run_id, status, summary)`, `verify_run(run_id)`, `read_events(run_id, after_sequence=0)`, and `export_run(run_id, destination)`.

- [ ] **Step 1: Write failing append, permission, and tamper tests**

```python
import json
from pathlib import Path

import pytest

from netzoo_agent_core.trace_store import LocalTraceStore, TraceIntegrityError


def test_store_appends_contiguous_private_jsonl(tmp_path: Path):
    store = LocalTraceStore(tmp_path)
    run_id = store.start_run({"session_id": "demo"})
    first = store.append(run_id, "run.started", "cli", {"status": "running"})
    second = store.append(run_id, "policy.loaded", "apply_project_policy", {"version": 1})

    assert [first.sequence, second.sequence] == [1, 2]
    assert second.previous_hash == first.event_hash
    assert (tmp_path / str(run_id)).stat().st_mode & 0o777 == 0o700
    assert (tmp_path / str(run_id) / "events.jsonl").stat().st_mode & 0o777 == 0o600


def test_store_detects_modified_event(tmp_path: Path):
    store = LocalTraceStore(tmp_path)
    run_id = store.start_run({"session_id": "demo"})
    store.append(run_id, "run.started", "cli", {"status": "running"})
    path = tmp_path / str(run_id) / "events.jsonl"
    line = json.loads(path.read_text())
    line["payload"]["status"] = "changed"
    path.write_text(json.dumps(line) + "\n")

    with pytest.raises(TraceIntegrityError):
        store.verify_run(run_id)
```

- [ ] **Step 2: Run tests and verify the store is missing**

Run: `python -m pytest tests/test_trace_store.py -v`

Expected: collection fails with `ModuleNotFoundError`.

- [ ] **Step 3: Implement preflight and run creation**

`preflight()` creates the root with `0700`, verifies it resolves beneath the configured project trace root, performs an atomic create/fsync/replace smoke test, and checks at least 10 MiB free with `shutil.disk_usage`. `start_run()` generates UUID4, creates `events.jsonl`, `manifest.json`, and `blobs/`, hardens permissions, then returns the UUID. Manifest writes use the existing atomic-write pattern but live in `trace_store.py` to avoid depending on memory internals.

- [ ] **Step 4: Implement locked append and integrity verification**

Use an in-process `threading.Lock` per run plus `fcntl.flock` on `<run>/events.lock`. While holding the lock, read the manifest tail, sanitize payload, create the next `TraceEvent`, append one canonical JSON line, flush, `os.fsync`, atomically update manifest, and release. If event append succeeds but manifest update fails, the next open reconstructs the tail from JSONL and repairs only the manifest metadata.

`verify_run()` checks schema, UUID, contiguous sequence, previous hash, event hash, and manifest final digest. It returns `RunVerification(valid: bool, event_count: int, final_hash: str)` and raises `TraceIntegrityError` at the first invalid line.

- [ ] **Step 5: Implement finish, read, and export**

`pause_run(run_id, summary)` appends `run.paused`, sets manifest status to `pending`, and leaves the manifest unsealed so resume can append. `finish_run(run_id, status, summary)` accepts only terminal statuses, appends `run.finished`, and seals the manifest with `finished_at`, status, final sequence, and final hash. `read_events(run_id, after_sequence=0)` validates every returned event. `export_run(run_id, destination)` creates a `.tar.gz` containing `events.jsonl`, `manifest.json`, and shareable blobs only; archive paths are fixed relative names and never derived from payload paths.

- [ ] **Step 6: Add concurrent append and partial-tail recovery tests**

Add a `ThreadPoolExecutor(max_workers=4)` test that performs 40 appends and asserts sequences 1–40 with a valid chain. Add a partial-final-line fixture and assert startup moves the invalid suffix to `events.corrupt` with `0600`, reports `TraceIntegrityError`, and refuses to append until an explicit `repair_partial_tail(run_id)` removes only the incomplete final bytes.

- [ ] **Step 7: Run store and redaction suites**

Run: `python -m pytest tests/test_trace_store.py tests/test_trace_redaction.py -v`

Expected: all tests pass; the concurrency test produces one contiguous chain.

- [ ] **Step 8: Commit the local store**

```bash
git add scripts/netzoo_agent_core/trace_store.py tests/test_trace_store.py
git commit -m "feat: persist append-only local agent traces"
```

---

### Task 4: TraceRecorder lifecycle and resumable session identity

**Files:**
- Create: `scripts/netzoo_agent_core/tracing.py`
- Modify: `scripts/netzoo_agent_core/session.py:157-211`
- Modify: `scripts/netzoo_agent_core/__init__.py`
- Modify: `scripts/netzoo_agent.py:20-85`
- Modify: `scripts/netzoo_agent_core/runtime.py:13-28`
- Test: `tests/test_trace_store.py`
- Test: `tests/test_graph_tracing.py`

**Interfaces:**
- Consumes: `LocalTraceStore`, UUID run id, event type, node name, typed payload.
- Produces: `TraceRecorder.start_run(session_id, profile_id)`, `append(run_id, event_type, node, payload)`, `pause_run(run_id, summary)`, `finish_run(run_id, status, summary)`, `instrument_node(node_name, function)`, `NullTraceRecorder`, and session payload field `run_id`.

- [ ] **Step 1: Write failing recorder and session-resume tests**

```python
from pathlib import Path

from netzoo_agent_core.session import load_session_payload, save_session
from netzoo_agent_core.trace_store import LocalTraceStore
from netzoo_agent_core.tracing import TraceRecorder


def test_session_retains_trace_run_id(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("netzoo_agent_core.session.SESSION_ROOT", tmp_path / "sessions")
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="named-session", profile_id="default")

    save_session(
        "named-session",
        [],
        {"run_id": str(run_id), "plan": None, "tool_results": []},
    )

    assert load_session_payload("named-session")["run_id"] == str(run_id)
```

- [ ] **Step 2: Run focused tests and verify recorder imports fail**

Run: `python -m pytest tests/test_trace_store.py tests/test_graph_tracing.py -v`

Expected: collection fails because `tracing.py` and `load_session_payload` do not exist.

- [ ] **Step 3: Implement `TraceRecorder` and the no-op interface**

```python
class TraceRecorder:
    def __init__(self, store: LocalTraceStore):
        self.store = store

    def start_run(self, *, session_id: str, profile_id: str):
        run_id = self.store.start_run({"session_id": session_id, "profile_id": profile_id})
        self.append(run_id, "run.started", "cli", {"session_id": session_id, "profile_id": profile_id})
        return run_id

    def append(self, run_id, event_type: str, node: str, payload: dict, **options):
        return self.store.append(run_id, event_type, node, payload, **options)

    def pause_run(self, run_id, summary: dict):
        return self.store.pause_run(run_id, summary)

    def finish_run(self, run_id, status: str, summary: dict):
        return self.store.finish_run(run_id, status, summary)
```

`NullTraceRecorder` implements the same methods but returns `None`; it is used only by unit tests and non-Agent policy/memory status commands. Production task execution always receives a real recorder.

- [ ] **Step 4: Add an exception-safe graph node wrapper**

`instrument_node(node_name, function)` appends `node.started`, calls the function, appends `node.finished` with sanitized keys and duration, and appends `error.recorded` before re-raising any exception. It must use `time.monotonic_ns()` for duration and the run id from state. Never serialize the entire state; include only `update_keys`, `current_step`, and typed domain summaries.

- [ ] **Step 5: Add `load_session_payload` without breaking `load_session`**

Create `load_session_payload(session_id) -> dict` as the single JSON parser. Make the existing `load_session(session_id, include_usage=False)` call it and preserve both legacy return shapes. `save_session(session_id, messages, state, profile_id="default")` adds `run_id: state.get("run_id")`. CLI integration in Task 7 reads the payload to resume the original run.

- [ ] **Step 6: Export and facade-wire the new modules**

Export `TraceRecorder`, `NullTraceRecorder`, `LocalTraceStore`, `TraceEvent`, and `TraceIntegrityError` from `netzoo_agent_core.__init__`. Add `trace_contracts`, `trace_redaction`, `trace_store`, and `tracing` to the facade module imports and `_IMPLEMENTATION_MODULES`; Task 6 adds `pricing` when that module is created. Add `TRACE_ROOT` to `MUTABLE_RUNTIME_NAMES` so temporary-directory tests can redirect trace writes.

- [ ] **Step 7: Run session and facade tests**

Run: `python -m pytest tests/test_trace_store.py tests/test_legacy_facade.py tests/test_agent_gate.py -k 'session or facade' -v`

Expected: all selected tests pass; historical `load_session(session_id, include_usage=True)` remains a three-tuple.

- [ ] **Step 8: Commit recorder lifecycle**

```bash
git add scripts/netzoo_agent_core/tracing.py scripts/netzoo_agent_core/session.py scripts/netzoo_agent_core/__init__.py scripts/netzoo_agent.py scripts/netzoo_agent_core/runtime.py tests/test_trace_store.py tests/test_graph_tracing.py
git commit -m "feat: bind durable traces to resumable sessions"
```

---

### Task 5: LangGraph node and domain-event instrumentation

**Files:**
- Modify: `scripts/netzoo_agent_core/graph.py:101-640`
- Modify: `scripts/netzoo_agent_core/contracts.py:394-408`
- Test: `tests/test_graph_tracing.py`

**Interfaces:**
- Consumes: `TraceRecorder`, `AgentState.run_id`, existing typed plan/evaluation/tool contracts.
- Produces: ordered node events and domain events for policy, memory, routing, planning, plan evaluation, tools, result evaluation, recovery, response, and errors.

- [ ] **Step 1: Write a failing successful-run event-order test**

```python
import pytest

from netzoo_agent_core.contracts import HumanMessage, RouterDecision
from netzoo_agent_core.graph import build_graph
from netzoo_agent_core.memory import EpisodeStore, UserProfileStore
from netzoo_agent_core.trace_store import LocalTraceStore
from netzoo_agent_core.tracing import TraceRecorder


class DeterministicRouterLLM:
    def with_structured_output(self, *_args, **_kwargs):
        return self

    def invoke(self, _messages):
        return RouterDecision(
            action="run_panda",
            in_scope=True,
            intent_type="run_analysis",
            confidence=0.99,
            reason="Deterministic trace fixture",
        )


@pytest.fixture
def graph_fixture(tmp_path, monkeypatch):
    monkeypatch.setenv("NETZOO_ROUTER_MODEL_ALLOWLIST", "fake")
    monkeypatch.setenv("NETZOO_RESPONSE_MODEL_ALLOWLIST", "fake")
    monkeypatch.setattr(
        "netzoo_agent_core.graph.build_llm",
        lambda *_args, **_kwargs: DeterministicRouterLLM(),
    )
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    app = build_graph(
        "fake",
        0.0,
        profile_store=UserProfileStore(tmp_path / "profiles"),
        episode_store=EpisodeStore(tmp_path / "episodes"),
        trace_recorder=recorder,
    )

    class GraphHarness:
        def run(self, task: str):
            run_id = recorder.start_run(session_id="trace-test", profile_id="default")
            result = app.invoke(
                {"messages": [HumanMessage(content=task)], "run_id": str(run_id)}
            )
            return result, store, run_id

    return GraphHarness()


def test_graph_records_ordered_plan_tool_and_evaluation_events(graph_fixture):
    result, store, run_id = graph_fixture.run("Run a PANDA demo")
    event_types = [event.event_type for event in store.read_events(run_id)]

    assert "policy.loaded" in event_types
    assert "decision.recorded" in event_types
    assert "plan.created" in event_types
    assert "plan.approved" in event_types
    assert "tool.started" in event_types
    assert "tool.completed" in event_types
    assert "evaluation.recorded" in event_types
    assert event_types.index("plan.created") < event_types.index("tool.started")
    assert result["run_id"] == str(run_id)
```

The fixture uses the existing fake LLM pattern, temporary profile/episode stores, and `LocalTraceStore`; it starts a run before invoking the graph.

- [ ] **Step 2: Run the integration test and verify no graph events exist**

Run: `python -m pytest tests/test_graph_tracing.py::test_graph_records_ordered_plan_tool_and_evaluation_events -v`

Expected: FAIL because `build_graph` does not accept or use `trace_recorder`.

- [ ] **Step 3: Inject the recorder and wrap every graph node**

Add `trace_recorder: TraceRecorder | None = None` to `build_graph`; default to `NullTraceRecorder` for direct legacy test callers. Replace each `graph.add_node("name", function)` with `graph.add_node("name", recorder.instrument_node("name", function))`. Add `run_id` to every node update through LangGraph state preservation, not by re-generating it.

- [ ] **Step 4: Emit typed policy, routing, and plan events**

After policy validation, emit `policy.loaded` with version, policy hash, agents path display value, and workflow count. After routing, emit `decision.recorded` with action, confidence, in-scope status, selected action, reason code (`provider`, `deterministic_fallback`, or `budget_fallback`), and recommended actions. After planning, emit `plan.created` with workflow, objective, status, ordered steps, missing inputs, evidence ledger, and policy hash. Do not serialize retrieved episode contents into routing events.

- [ ] **Step 5: Emit plan gate, tool, evaluator, and recovery events**

Before `execute_selected_tool`, emit `tool.started` with `step_index`, action, purpose, sanitized arguments, execution mode, and attempt id. After structuring, emit `tool.completed` with status, summary, artifacts, metrics, warnings, errors, retryable, recovery hint, safe log reference, and attempt id. Emit `plan.approved` or `plan.rejected`, `evaluation.recorded`, and `recovery.selected` from the existing deterministic contracts.

- [ ] **Step 6: Add failure and recovery ordering tests**

Use existing forged-plan and recoverable-result fixtures. Assert rejected plans never emit `tool.started`; provider failures emit `error.recorded` followed by a deterministic `decision.recorded`; recovery produces `evaluation.recorded`, then `recovery.selected`, then a new `plan.created` before the next `tool.started`.

- [ ] **Step 7: Run graph tracing and regression suites**

Run: `python -m pytest tests/test_graph_tracing.py tests/test_agent_gate.py tests/test_agent_module_boundaries.py -v`

Expected: all tests pass; every graph event has contiguous sequence and a valid hash.

- [ ] **Step 8: Commit graph instrumentation**

```bash
git add scripts/netzoo_agent_core/graph.py scripts/netzoo_agent_core/contracts.py tests/test_graph_tracing.py
git commit -m "feat: record NetZoo graph and tool events"
```

---

### Task 6: Cost provenance and predictive token budget gate

**Files:**
- Create: `scripts/netzoo_agent_core/pricing.py`
- Modify: `scripts/netzoo_agent_core/llm.py:140-235`
- Modify: `scripts/netzoo_agent_core/graph.py:215-285, 544-608`
- Modify: `scripts/netzoo_agent_core/contracts.py:483-491`
- Test: `tests/test_trace_contracts.py`
- Test: `tests/test_graph_tracing.py`

**Interfaces:**
- Consumes: provider response metadata, model name, input/output text, current `LLMUsage`, reserved output tokens, and `NETZOO_MODEL_PRICING_JSON`.
- Produces: `extract_provider_usage(response)`, `PriceCatalog.snapshot(model)`, `append_llm_usage(current, role, model, response, input_text, output_text, budget_tokens) -> LLMUsage`, and `evaluate_budget_call(usage, estimated_input_tokens, reserved_output_tokens, budget_tokens, reserve_tokens, allow_reserve) -> BudgetDecision`.

- [ ] **Step 1: Write failing price-provenance and threshold tests**

```python
from netzoo_agent_core.llm import evaluate_budget_call
from netzoo_agent_core.pricing import PriceCatalog


def test_price_snapshot_uses_integer_micro_usd_per_million(monkeypatch):
    monkeypatch.setenv(
        "NETZOO_MODEL_PRICING_JSON",
        '{"openai/gpt-4o-mini":{"input_micro_usd_per_million":150000,"output_micro_usd_per_million":600000,"effective_at":"2026-08-03T00:00:00Z"}}',
    )
    snapshot = PriceCatalog.from_environment().snapshot("openai/gpt-4o-mini")
    assert snapshot.provenance == "estimated"
    assert snapshot.input_micro_usd_per_million == 150000


def test_budget_reserves_finalization_tokens_and_reports_threshold():
    warning = evaluate_budget_call(
        {"total_tokens": 13600, "calls": [], "budget_tokens": 20000},
        estimated_input_tokens=100,
        reserved_output_tokens=500,
        budget_tokens=20000,
        reserve_tokens=1500,
        allow_reserve=False,
    )
    blocked = evaluate_budget_call(
        {"total_tokens": 18000, "calls": [], "budget_tokens": 20000},
        estimated_input_tokens=100,
        reserved_output_tokens=500,
        budget_tokens=20000,
        reserve_tokens=1500,
        allow_reserve=False,
    )

    assert warning.status == "warning_70"
    assert blocked.status == "blocked"
```

- [ ] **Step 2: Run focused tests and confirm pricing imports fail**

Run: `python -m pytest tests/test_trace_contracts.py -k 'price or budget' -v`

Expected: collection fails because `pricing.py` and `evaluate_budget_call` do not exist.

- [ ] **Step 3: Implement strict price catalog loading**

`PriceCatalog.from_environment()` parses a JSON object keyed by exact model name. Each entry requires non-negative integer micro-USD-per-million input/output rates and an ISO-8601 `effective_at`. Invalid JSON or negative values raise `ValueError` before an Agent task starts. Missing model returns a snapshot with provenance `unavailable` and null rates; it never falls back to a guessed price.

- [ ] **Step 4: Extend provider usage extraction**

Read provider token metadata from `usage_metadata`, `response_metadata.token_usage`, or `response_metadata.usage`. Read actual cost only from explicitly named numeric metadata fields (`cost`, `total_cost`, or `usage.cost`) and convert decimal USD to integer micro-USD using `Decimal`. Store request id when available. Do not parse human-readable strings or infer currency.

- [ ] **Step 5: Implement predictive budget decisions**

```python
import math


def evaluate_budget_call(
    usage,
    *,
    estimated_input_tokens: int,
    reserved_output_tokens: int,
    budget_tokens: int,
    reserve_tokens: int = 1500,
    allow_reserve: bool = False,
) -> BudgetDecision:
    consumed = LLMUsage.model_validate(usage).total_tokens if usage else 0
    ceiling = budget_tokens if allow_reserve else max(0, budget_tokens - reserve_tokens)
    projected = consumed + estimated_input_tokens + reserved_output_tokens
    warning_70_tokens = math.ceil(budget_tokens * 0.70)
    warning_85_tokens = math.ceil(budget_tokens * 0.85)
    if projected > ceiling:
        status = "blocked"
    elif projected >= warning_85_tokens:
        status = "warning_85"
    elif projected >= warning_70_tokens:
        status = "warning_70"
    else:
        status = "allowed"
    return BudgetDecision(
        status=status,
        consumed_tokens=consumed,
        estimated_input_tokens=estimated_input_tokens,
        reserved_output_tokens=reserved_output_tokens,
        projected_tokens=projected,
        hard_limit_tokens=budget_tokens,
        reserve_tokens=reserve_tokens,
    )
```

Derive threshold tokens from 70% and 85% of non-default budgets while preserving exact 14,000 and 17,000 behavior for 20,000. Keep `budget_allows_call(usage, input_text, reserved_output_tokens, budget_tokens)` as a compatibility wrapper returning `decision.status != "blocked"`.

- [ ] **Step 6: Emit `llm.completed`, warning, and blocking events**

Before router and response calls, calculate `BudgetDecision`. Emit `budget.warning` once when a run first crosses each threshold. On block, emit `budget.blocked` with projected, limit, reserve, role, and model; do not invoke the provider. After each attempted call, emit `llm.completed` with `LLMCallUsage`, including actual/estimated/unavailable provenance and price snapshot id. Router uses `allow_reserve=False`; the final response fallback path uses `allow_reserve=True`.

- [ ] **Step 7: Run token, graph, and backward-compatibility tests**

Run: `python -m pytest tests/test_trace_contracts.py tests/test_graph_tracing.py tests/test_agent_gate.py -k 'token or budget or graph' -v`

Expected: provider metadata remains preferred; default 20,000 behavior passes; blocked calls never invoke fake providers; warnings are not duplicated.

- [ ] **Step 8: Commit usage and budget instrumentation**

```bash
git add scripts/netzoo_agent_core/pricing.py scripts/netzoo_agent_core/llm.py scripts/netzoo_agent_core/graph.py scripts/netzoo_agent_core/contracts.py tests/test_trace_contracts.py tests/test_graph_tracing.py
git commit -m "feat: trace LLM cost and enforce predictive budgets"
```

---

### Task 7: CLI lifecycle, retention, local inspection, and phase-one verification

**Files:**
- Modify: `scripts/netzoo_agent_core/cli.py:150-299, 420-668`
- Modify: `scripts/netzoo_agent_core/session.py:88-126`
- Modify: `AGENT_USAGE.md:450-525`
- Test: `tests/test_graph_tracing.py`
- Verify without modifying: `tests/test_agent_gate.py`

**Interfaces:**
- Consumes: real `TraceRecorder`, session payload `run_id`, CLI task lifecycle, trace retention days.
- Produces: mandatory task traces, `--trace-status RUN_ID`, `--trace-export RUN_ID PATH`, trace retention, and an end-to-end local audit package.

- [ ] **Step 1: Write failing CLI lifecycle and resume tests**

Add a one-shot CLI test with patched fake graph dependencies and redirected `TRACE_ROOT`. Assert the trace begins with `run.started`, includes graph events, and ends with `run.finished`. Add a named needs-input session test, resume it, and assert the second invocation appends `run.resumed` to the same UUID run directory rather than creating another directory.

- [ ] **Step 2: Run the new CLI tests and confirm lifecycle events are absent**

Run: `python -m pytest tests/test_graph_tracing.py -k 'cli or resume' -v`

Expected: FAIL because CLI does not construct or finalize a recorder.

- [ ] **Step 3: Reorder CLI startup and create mandatory traces**

Resolve `session_id` and any saved `run_id` before building the graph. Run `LocalTraceStore.preflight()`. For a fresh task, call `recorder.start_run`; for resume, verify the unsealed chain and append `run.resumed`. Pass the recorder to `build_graph` and include `run_id` in every invocation. On a terminal result call `finish_run`; on `needs_input` or `needs_confirmation` call `pause_run` and keep the trace unsealed. On `AgentTurnInterrupted`, append `run.interrupted`; on exceptions append `error.recorded` and keep the trace unsealed for resume.

- [ ] **Step 4: Add local trace status and export arguments**

Add mutually non-destructive CLI options:

```python
parser.add_argument("--trace-status", metavar="RUN_ID", help="Verify and summarize one local trace without calling an LLM.")
parser.add_argument("--trace-export", nargs=2, metavar=("RUN_ID", "ARCHIVE"), help="Export one verified local trace audit package without calling an LLM.")
parser.add_argument("--trace-retention-days", type=int, default=int(os.environ.get("NETZOO_TRACE_RETENTION_DAYS", "90")))
```

`--trace-status` prints run id, validity, event count, final sequence, final hash, status, token total, and actual/estimated/unavailable cost counts. `--trace-export` refuses an existing destination rather than overwriting it.

- [ ] **Step 5: Extend retention without touching active or pending runs**

`cleanup_runtime_storage` gains `trace_retention_days=90` and returns a `traces` count. Remove only sealed trace directories whose manifest `finished_at` is older than cutoff. Never remove an unsealed, pending, `trace_degraded`, or corrupt run. Validate the resolved child path is directly beneath `TRACE_ROOT` before recursive deletion; use an explicit run UUID path, never a glob-expanded deletion command.

- [ ] **Step 6: Document local operation and privacy boundaries**

Update `AGENT_USAGE.md` with exact paths, event types, hash verification, actual versus estimated cost, 14,000/17,000/20,000 behavior, 1,500-token reserve, status/export commands, 90-day sealed-trace retention, and the fact that trace reasoning is structured audit data rather than chain-of-thought.

- [ ] **Step 7: Run the complete Python test suite**

Run: `python -m pytest -q`

Expected: all tests pass. Existing dirty tests are not rewritten to make unrelated failures disappear; investigate any failure before changing production behavior.

- [ ] **Step 8: Run a deterministic local smoke trace**

Run with the existing fake/test model fixture through the end-to-end test, then run `python scripts/netzoo_agent.py --trace-status <fixture-run-id>` inside the test-controlled trace root. Expected summary includes `valid=true`, a positive event count, continuous final sequence, and matching final hash. Do not call a paid provider for this smoke test.

- [ ] **Step 9: Commit the phase-one integration**

```bash
git add scripts/netzoo_agent_core/cli.py scripts/netzoo_agent_core/session.py AGENT_USAGE.md tests/test_graph_tracing.py
git commit -m "feat: complete local NetZoo observability lifecycle"
```

## Phase-One Definition of Done

- A fresh or resumed Agent task produces one verified append-only JSONL run.
- Every graph node has start/finish or start/error events.
- Plans, gates, tools, evaluations, recoveries, LLM usage, cost provenance, and budget decisions are present as typed domain events.
- Secrets are redacted before the first local write.
- A cloud outage is irrelevant because phase one has no cloud dependency.
- The status command verifies the chain; export creates a non-overwriting audit package.
- Existing CLI/session behavior and the legacy facade remain compatible.
- The complete test suite passes without editing unrelated user changes.

## Follow-on Plans

After this plan passes its Definition of Done, create two separate implementation plans from the approved design spec:

1. `2026-08-03-netzoo-cloud-trace-collector.md`: FastAPI ingestion, PostgreSQL, object storage, idempotent sync, integrity checks, share-token administration, and SSE backend.
2. `2026-08-03-netzoo-replay-dashboard.md`: React/TypeScript L1–L3 interface, replay reducer, earliest-divergence projection, fragment-token exchange, responsive/security/visual tests, and Docker Compose deployment.
