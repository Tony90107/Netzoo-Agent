import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core import session  # noqa: E402
import netzoo_agent_core.graph.factory as graph_module  # noqa: E402
from netzoo_agent_core.contracts import HumanMessage, RouterDecision  # noqa: E402
from netzoo_agent_core.graph import build_graph  # noqa: E402
from netzoo_agent_core.cli import export_local_trace, local_trace_status  # noqa: E402
from netzoo_agent_core.memory import EpisodeStore, UserProfileStore  # noqa: E402
from netzoo_agent_core.session import (  # noqa: E402
    load_session,
    load_session_payload,
    save_session,
)
from netzoo_agent_core.trace_store import LocalTraceStore  # noqa: E402
from netzoo_agent_core.tracing import TraceRecorder  # noqa: E402
import netzoo_agent as legacy_agent  # noqa: E402


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


@pytest.mark.skipif(
    graph_module.StateGraph is None,
    reason="LangGraph integration runs in the project container",
)
def test_graph_records_ordered_plan_tool_and_evaluation_events(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("NETZOO_ROUTER_MODEL_ALLOWLIST", "fake")
    monkeypatch.setenv("NETZOO_RESPONSE_MODEL_ALLOWLIST", "fake")
    monkeypatch.setattr(
        graph_module,
        "build_llm",
        lambda *_args, **_kwargs: DeterministicRouterLLM(),
    )
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="trace-test", profile_id="default")
    app = build_graph(
        "fake",
        0.0,
        profile_store=UserProfileStore(tmp_path / "profiles"),
        episode_store=EpisodeStore(tmp_path / "episodes"),
        trace_recorder=recorder,
    )

    result = app.invoke(
        {
            "messages": [HumanMessage(content="Run a PANDA demo")],
            "run_id": str(run_id),
        }
    )
    events = store.read_events(run_id)
    event_types = [event.event_type for event in events]

    assert "policy.loaded" in event_types
    assert "decision.recorded" in event_types
    assert "plan.created" in event_types
    assert "plan.approved" in event_types
    assert "tool.started" in event_types
    assert "tool.completed" in event_types
    assert "evaluation.recorded" in event_types
    assert event_types.index("plan.created") < event_types.index("tool.started")
    assert result["run_id"] == str(run_id)
    assert store.verify_run(run_id).valid is True


def test_local_trace_status_and_export_need_no_model_provider(tmp_path: Path):
    root = tmp_path / "traces"
    recorder = TraceRecorder(LocalTraceStore(root))
    run_id = recorder.start_run(session_id="status", profile_id="default")
    recorder.finish_run(run_id, "completed", {"result": "ok"})
    archive = tmp_path / "trace.tar.gz"

    status = local_trace_status(str(run_id), trace_root=root)
    exported = export_local_trace(str(run_id), archive, trace_root=root)

    assert status["valid"] is True
    assert status["status"] == "completed"
    assert status["event_count"] == 2
    assert exported == archive
