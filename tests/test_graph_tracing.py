import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core import session  # noqa: E402
import netzoo_agent_core.graph.factory as graph_module  # noqa: E402
from netzoo_agent_core.contracts import (  # noqa: E402
    Episode,
    HumanMessage,
    LLMUsage,
    OutcomeHypothesis,
    RequestedOutcome,
    RouterDecision,
)
from netzoo_agent_core.graph import build_graph  # noqa: E402
from netzoo_agent_core.graph.policy_memory import retrieve_memory  # noqa: E402
from netzoo_agent_core.cli import export_local_trace, local_trace_status  # noqa: E402
from netzoo_agent_core.memory import (  # noqa: E402
    EpisodeStore,
    UserProfileStore,
    _write_json_atomic,
)
from netzoo_agent_core.session import (  # noqa: E402
    load_session,
    load_session_payload,
    save_session,
)
from netzoo_agent_core.trace_store import LocalTraceStore  # noqa: E402
from netzoo_agent_core.trace_contracts import LLMCallUsage  # noqa: E402
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
            outcome_hypotheses=[
                OutcomeHypothesis(
                    outcome=RequestedOutcome(
                        operation="infer",
                        artifact_type="regulatory_network",
                        entity_types=["tf", "gene"],
                        display_entities=["TF", "gene"],
                        regulator_types=["tf"],
                        target_types=["gene"],
                        granularity="aggregate",
                        unresolved_dimensions=[],
                    ),
                    confidence=0.99,
                    evidence=[],
                    assumptions=[],
                )
            ],
        )


class SequencedHypothesisRouter:
    def __init__(self):
        self.calls = 0

    def with_structured_output(self, *_args, **_kwargs):
        return self

    def invoke(self, _messages):
        self.calls += 1
        if self.calls == 1:
            return RouterDecision(
                action="no_tool",
                in_scope=True,
                intent_type="answer_question",
                confidence=0.9,
                reason="The scientific outcome was under-classified.",
                outcome_hypotheses=[
                    OutcomeHypothesis(
                        outcome=RequestedOutcome(
                            operation="unknown",
                            artifact_type="unknown",
                            granularity="not_applicable",
                            unresolved_dimensions=[],
                        ),
                        confidence=0.9,
                        evidence=[],
                        assumptions=[],
                    )
                ],
            )
        if self.calls == 2:
            return RouterDecision(
                action="no_tool",
                in_scope=True,
                intent_type="answer_question",
                confidence=0.9,
                reason="A sample-specific miRNA network is the supported hypothesis.",
                outcome_hypotheses=[
                    OutcomeHypothesis(
                        outcome=RequestedOutcome(
                            operation="infer",
                            artifact_type="regulatory_network",
                            entity_types=["mirna", "gene"],
                            display_entities=["miRNA", "gene"],
                            regulator_types=["mirna"],
                            target_types=["gene"],
                            granularity="sample_specific",
                            unresolved_dimensions=["confirm network interpretation"],
                        ),
                        confidence=0.9,
                        evidence=[],
                        assumptions=[
                            "network data means a regulatory-network result"
                        ],
                    )
                ],
            )
        raise AssertionError("semantic Router repair must run at most once")


class EmptyOutcomeRouter:
    def __init__(self):
        self.calls = 0

    def with_structured_output(self, *_args, **_kwargs):
        return self

    def invoke(self, _messages):
        self.calls += 1
        if self.calls > 2:
            raise AssertionError("semantic Router repair must run at most once")
        return RouterDecision(
            action="no_tool",
            in_scope=True,
            intent_type="answer_question",
            confidence=0.9,
            reason="No usable outcome hypothesis was produced.",
            outcome_hypotheses=[],
            clarification_question="What specific inputs do you have for the analysis?",
        )


class GuidanceResponseLLM:
    def __init__(self):
        self.calls = 0

    def invoke(self, _messages):
        self.calls += 1
        return legacy_agent.AIMessage(
            content=(
                "Use PUMA followed by LIONESS-PUMA for sample-specific miRNA "
                "regulatory networks. No files were inspected and no analysis ran."
            )
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


def test_session_serializes_llm_call_uuid_as_json_string(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(session, "SESSION_ROOT", tmp_path / "sessions")
    call = LLMCallUsage(
        role="router",
        model="test-model",
        input_tokens=3,
        output_tokens=2,
        total_tokens=5,
        usage_provenance="actual",
        status="success",
    )
    usage = LLMUsage(
        input_tokens=3,
        output_tokens=2,
        total_tokens=5,
        calls=[call],
    )

    save_session(
        "uuid-usage-session",
        [],
        {
            "plan": None,
            "tool_results": [],
            "token_usage": usage.model_dump(),
        },
    )

    payload = load_session_payload("uuid-usage-session")
    stored_call = payload["token_usage"]["calls"][0]
    assert stored_call["call_id"] == str(call.call_id)
    assert LLMUsage.model_validate(payload["token_usage"]).calls[0].call_id == call.call_id


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


def test_memory_retrieval_trace_explains_each_selected_episode_score(tmp_path: Path):
    episode_store = EpisodeStore(tmp_path / "episodes")
    episode = Episode(
        episode_id="mirna-success",
        profile_id="default",
        task_summary="sample-specific miRNA regulatory network",
        workflow="LIONESS-PUMA",
        action="run_lioness_puma",
        status="completed",
    )
    _write_json_atomic(
        episode_store.path_for("default", episode.episode_id),
        episode.model_dump(),
    )
    trace_store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(trace_store)
    run_id = recorder.start_run(session_id="memory-score", profile_id="default")
    context = SimpleNamespace(
        profile_id="default",
        profile_store=UserProfileStore(tmp_path / "profiles"),
        episode_store=episode_store,
        recorder=recorder,
    )

    update = retrieve_memory(
        context,
        {
            "messages": [
                HumanMessage(content="run puma sample-specific miRNA")
            ],
            "run_id": str(run_id),
        },
    )

    event = next(
        item
        for item in trace_store.read_events(run_id)
        if item.event_type == "memory.retrieved"
    )
    assert update["retrieved_episodes"][0]["episode_id"] == "mirna-success"
    assert event.payload["episodes"] == [
        {
            "episode_id": "mirna-success",
            "workflow": "LIONESS-PUMA",
            "final_score": 7,
            "overlap_tokens": ["mirna", "sample-specific"],
            "workflow_bonus": 3,
            "status_bonus": 2,
        }
    ]


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


@pytest.mark.skipif(
    graph_module.StateGraph is None,
    reason="LangGraph integration runs in the project container",
)
def test_graph_repairs_an_underclassified_outcome_once(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("NETZOO_ROUTER_MODEL_ALLOWLIST", "fake")
    monkeypatch.setenv("NETZOO_RESPONSE_MODEL_ALLOWLIST", "fake")
    router = SequencedHypothesisRouter()
    response_llm = GuidanceResponseLLM()
    models = iter([router, response_llm])
    monkeypatch.setattr(
        graph_module,
        "build_llm",
        lambda *_args, **_kwargs: next(models),
    )
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="repair-test", profile_id="default")
    app = build_graph(
        "fake",
        0.0,
        profile_store=UserProfileStore(tmp_path / "profiles"),
        episode_store=EpisodeStore(tmp_path / "episodes"),
        trace_recorder=recorder,
    )

    result = app.invoke(
        {
            "messages": [
                HumanMessage(
                    content="What tools can produce a sample-specific miRNA network?"
                )
            ],
            "run_id": str(run_id),
        }
    )
    events = store.read_events(run_id)

    assert router.calls == 2
    assert result["decision"]["action"] == "no_tool"
    assert result["decision"]["matched_actions"] == []
    assert result["decision"]["hypothesis_actions"] == ["run_lioness_puma"]
    assert response_llm.calls == 1
    assert [call["role"] for call in result["token_usage"]["calls"]] == [
        "router",
        "router_repair",
        "response",
    ]
    assert (
        sum(event.event_type == "routing.underclassified" for event in events) == 1
    )


@pytest.mark.skipif(
    graph_module.StateGraph is None,
    reason="LangGraph integration runs in the project container",
)
def test_graph_recovers_explicit_typed_outcome_after_two_empty_router_results(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("NETZOO_ROUTER_MODEL_ALLOWLIST", "fake")
    monkeypatch.setenv("NETZOO_RESPONSE_MODEL_ALLOWLIST", "fake")
    router = EmptyOutcomeRouter()
    response_llm = GuidanceResponseLLM()
    models = iter([router, response_llm])
    monkeypatch.setattr(
        graph_module,
        "build_llm",
        lambda *_args, **_kwargs: next(models),
    )
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="double-empty-test", profile_id="default")
    app = build_graph(
        "fake",
        0.0,
        router_model_name="fake",
        profile_store=UserProfileStore(tmp_path / "profiles"),
        episode_store=EpisodeStore(tmp_path / "episodes"),
        trace_recorder=recorder,
    )

    result = app.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "If I want to get a sample-specific miRNA regulatory network, "
                        "what tools do I need?"
                    )
                )
            ],
            "run_id": str(run_id),
        }
    )
    events = store.read_events(run_id)

    assert router.calls == 2
    assert result["decision"]["action"] == "no_tool"
    assert result["decision"]["capability_match_status"] == "exact"
    assert result["decision"]["matched_actions"] == ["run_lioness_puma"]
    assert result["decision"]["recommended_actions"] == [
        "run_puma",
        "run_lioness_puma",
    ]
    assert result["decision"]["clarification_question"] is None
    assert result["tool_results"] == []
    assert response_llm.calls == 1
    assert [call["role"] for call in result["token_usage"]["calls"]] == [
        "router",
        "router_repair",
        "response",
    ]
    assert any(
        event.event_type == "routing.deterministic_outcome_recovered"
        for event in events
    )


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
