import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core import session  # noqa: E402
from netzoo_agent_core.session import (  # noqa: E402
    load_session,
    load_session_payload,
    save_session,
)
from netzoo_agent_core.trace_store import LocalTraceStore  # noqa: E402
from netzoo_agent_core.tracing import TraceRecorder  # noqa: E402
import netzoo_agent as legacy_agent  # noqa: E402


def test_session_retains_the_trace_run_id_without_changing_legacy_load_shape(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(session, "SESSION_ROOT", tmp_path / "sessions")
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="named-session", profile_id="default")

    save_session(
        "named-session",
        [],
        {"run_id": str(run_id), "plan": None, "tool_results": []},
    )

    payload = load_session_payload("named-session")
    legacy = load_session("named-session", include_usage=True)
    assert payload["run_id"] == str(run_id)
    assert len(legacy) == 3


def test_instrumented_node_records_boundaries_without_serializing_state(tmp_path: Path):
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="demo", profile_id="default")

    def classify(state):
        assert state["secret_state"] == "do-not-copy"
        return {"decision": {"action": "run_panda"}}

    result = recorder.instrument_node("classify", classify)(
        {"run_id": str(run_id), "current_step": 0, "secret_state": "do-not-copy"}
    )
    events = store.read_events(run_id)

    assert result == {"decision": {"action": "run_panda"}}
    assert [event.event_type for event in events] == [
        "run.started",
        "node.started",
        "node.finished",
    ]
    assert events[-1].payload["update_keys"] == ["decision"]
    assert "do-not-copy" not in (store.run_path(run_id) / "events.jsonl").read_text()


def test_instrumented_node_records_error_and_reraises(tmp_path: Path):
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="demo", profile_id="default")

    def fail(_state):
        raise ValueError("invalid bearer-secret")

    with pytest.raises(ValueError, match="invalid bearer-secret"):
        recorder.instrument_node("evaluate", fail)({"run_id": str(run_id)})

    events = store.read_events(run_id)
    assert events[-1].event_type == "error.recorded"
    assert events[-1].payload["error_type"] == "ValueError"


def test_trace_interfaces_are_available_from_stable_and_legacy_facades():
    from netzoo_agent_core import LocalTraceStore as StableStore
    from netzoo_agent_core import TraceRecorder as StableRecorder

    assert StableStore is LocalTraceStore
    assert StableRecorder is TraceRecorder
    assert legacy_agent.LocalTraceStore is LocalTraceStore
    assert legacy_agent.TraceRecorder is TraceRecorder
