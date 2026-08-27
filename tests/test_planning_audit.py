from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.planning_audit import write_planning_audit
from netzoo_agent_core.trace_store import LocalTraceStore
from netzoo_agent_core.tracing import TraceRecorder


def _result() -> dict:
    return {
        "decision": {"action": "no_tool", "confidence": 0.95},
        "plan": {
            "workflow": "NO-TOOL",
            "status": "respond_only",
            "missing_inputs": [],
        },
    }


def _start_trace(tmp_path: Path):
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="test-session", profile_id="default")
    recorder.append(run_id, "policy.loaded", "apply_project_policy", {"policy_version": 2})
    recorder.append(run_id, "memory.retrieved", "retrieve_memory", {"episode_count": 2})
    recorder.append(run_id, "node.started", "classify", {"current_step": 0})
    recorder.append(
        run_id,
        "llm.completed",
        "classify",
        {
            "role": "intent_router",
            "model": "fake-model",
            "status": "success",
            "input_tokens": 100,
            "output_tokens": 20,
            "total_tokens": 120,
            "cache_read_tokens": 10,
            "duration_ms": 25,
            "cost_micro_usd": 12,
        },
    )
    recorder.append(
        run_id,
        "decision.recorded",
        "classify",
        {"action": "no_tool", "reason": "guidance"},
    )
    recorder.append(
        run_id,
        "plan.created",
        "plan",
        {"workflow": "NO-TOOL", "status": "respond_only"},
    )
    recorder.append(run_id, "node.finished", "respond", {"duration_ms": 40})
    return store, recorder, run_id


def test_planning_audit_renders_order_tokens_and_boundaries(tmp_path: Path):
    store, recorder, run_id = _start_trace(tmp_path)
    recorder.finish_run(run_id, "completed", {"token_usage": {}})

    path = write_planning_audit(
        str(run_id),
        store,
        task="Explain the workflow. OPENROUTER_API_KEY=sk-or-v1-secret-value",
        result=_result(),
        root=tmp_path / "planning_audits",
    )

    assert path is not None
    report = Path(path).read_text(encoding="utf-8")
    assert "# NetZoo planning audit" in report
    assert "apply_project_policy → retrieve_memory → classify → plan → respond" in report
    assert "intent_router" in report
    assert "100" in report and "20" in report and "120" in report
    assert "Total observed tokens: `120`" in report
    assert "No executor/tool event was observed" in report
    assert "[REDACTED]" in report
    assert "sk-or-v1-secret-value" not in report
    assert Path(path).stat().st_mode & 0o777 == 0o600
    assert Path(path).parent.stat().st_mode & 0o777 == 0o700


def test_planning_audit_marks_unexpected_tool_activity(tmp_path: Path):
    store, recorder, run_id = _start_trace(tmp_path)
    recorder.append(run_id, "tool.started", "execute_tool", {"action": "run_panda"})
    recorder.finish_run(run_id, "completed", {})

    path = write_planning_audit(
        str(run_id),
        store,
        task="Plan the task",
        result=_result(),
        root=tmp_path / "planning_audits",
    )

    assert path is not None
    report = Path(path).read_text(encoding="utf-8")
    assert "Executor/tool events observed: `1`" in report
    assert "Executor/tool activity was observed" in report
