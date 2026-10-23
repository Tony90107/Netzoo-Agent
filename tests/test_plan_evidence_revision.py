"""Harness repair P4 (ROUND-P4.md, spec 9, A17): a confirmed preview runs only on the files the preview showed.

The execute gate fingerprints the step's input files. After a confirmed dry-run preview, a file whose content changed
(even at the same size and mtime), a file that is gone, or a file the preview never showed stops the run, and the
reason names it. Without a preview there is nothing to compare. The guarantee ends at the gate (TOCTOU, ROUND-P4.md).
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import AIMessage, HumanMessage, TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.contracts.planning import WorkflowStep  # noqa: E402
from netzoo_agent_core.contracts.results import EvaluationResult, ToolExecutionResult  # noqa: E402
from netzoo_agent_core.data.artifact_revision import preview_check  # noqa: E402
from netzoo_agent_core.graph import execution as graph_execution  # noqa: E402

CONTEXT = SimpleNamespace(recorder=MagicMock(), project_policy=SimpleNamespace(policy_hash="p", workflows={}))


@pytest.fixture()
def files(tmp_path):
    expression, design = tmp_path / "expr.tsv", tmp_path / "design.tsv"
    expression.write_text("gene\ts1\ts2\ts3\nA\t1\t2\t3\n")
    design.write_text("sample\tgroup\ns1\ta\ns2\tb\ns3\ta\n")
    return expression, design


def _decision(expression, design) -> TaskDecision:
    return TaskDecision(action="run_cobra", in_scope=True, should_execute=True, confidence=0.9, reason="r",
                        expression_file=str(expression), design_file=str(design), output_dir="cobra_out")


def _previewed(decision) -> dict:
    found, refusal = preview_check("run_cobra", decision, CONTEXT.project_policy, None)
    assert refusal is None and len(found) == 2
    return found


def _gate(decision, previewed):
    return preview_check("run_cobra", decision, CONTEXT.project_policy, previewed)


def test_the_files_the_preview_showed_run(files, monkeypatch):
    decision = _decision(*files)
    found, refusal = _gate(decision, _previewed(decision))
    assert refusal is None and sorted(found) == sorted(str(path.resolve()) for path in files)


def test_a_file_changed_after_the_preview_stops_the_run_even_at_the_same_size_and_mtime(files, monkeypatch):
    decision = _decision(*files)
    previewed = _previewed(decision)
    stat = files[0].stat()
    files[0].write_text(files[0].read_text().replace("1", "9", 1))
    os.utime(files[0], ns=(stat.st_atime_ns, stat.st_mtime_ns))
    _, refusal = _gate(decision, previewed)
    assert f"the input file {files[0].resolve()} changed after the preview (sha256 " in refusal
    assert refusal.endswith("no analysis was started. Ask for the preview again to check the current files, then "
                            "confirm the new one.")


def test_a_gone_file_and_a_file_the_preview_never_showed_stop_the_run(files, monkeypatch, tmp_path):
    decision = _decision(*files)
    previewed = _previewed(decision)
    other = tmp_path / "other_design.tsv"
    other.write_text(files[1].read_text())
    _, refusal = _gate(_decision(files[0], other), previewed)
    assert f"the plan now uses {other.resolve()}, which the preview did not show" in refusal
    files[1].unlink()
    _, refusal = _gate(decision, previewed)
    assert f"the input file {files[1]} (design_file) is no longer there" in refusal


def test_without_a_preview_nothing_is_compared(files):
    decision = _decision(*files)
    files[0].write_text("changed")
    assert _gate(decision, None)[1] is None


def _execute(state, monkeypatch, *, execute=True):
    calls = []
    monkeypatch.setattr(graph_execution, "EXECUTE_TOOLS", execute)
    with patch.object(graph_execution, "_unapproved_run", return_value=None), \
            patch.object(graph_execution, "execute_selected_tool", side_effect=lambda d: calls.append(d) or "ok"), \
            patch.object(graph_execution, "record_event"), \
            patch.object(graph_execution, "structure_tool_result",
                         side_effect=lambda action, decision, raw, **kwargs: SimpleNamespace(
                             status="failed" if raw.startswith("Error") else "success", summary=raw,
                             model_dump=lambda **_: {"status": "failed" if raw.startswith("Error") else "success",
                                                     "raw": raw})):
        update = graph_execution.execute_tool(CONTEXT, {**state, "current_step": 0})
    return calls, update


def test_the_execute_gate_never_reaches_the_executor_with_a_changed_file(files, monkeypatch):
    decision = _decision(*files)
    plan = WorkflowPlan(workflow="COBRA", objective="o", decision=decision.model_dump(), status="ready",
                        steps=[WorkflowStep(action="run_cobra", purpose="p")])
    state = {"plan": plan.model_dump(), "messages": [HumanMessage(content="Run COBRA.")],
             "previewed_inputs": _previewed(decision)}
    calls, update = _execute(state, monkeypatch)
    assert len(calls) == 1 and sorted(update["input_revisions"]) == sorted(state["previewed_inputs"])
    files[1].write_text("sample\tgroup\ns1\tb\ns2\ta\ns3\ta\n")
    calls, update = _execute(state, monkeypatch)
    assert calls == [] and "changed after the preview" in update["tool_result"]["raw"]
    calls, _update = _execute(state, monkeypatch, execute=False)  # a dry run compares nothing
    assert len(calls) == 1


def test_the_machine_keeps_the_previews_files_and_sends_them_with_the_confirmed_run(files, tmp_path, monkeypatch):
    from netzoo_agent_core import session as session_module
    from netzoo_agent_core.engine.machine import ConversationMachine

    monkeypatch.setattr(session_module, "SESSION_ROOT", tmp_path / "sessions")
    decision = _decision(*files)
    previewed = _previewed(decision)
    plan = WorkflowPlan(workflow="COBRA", objective="o", decision=decision.model_dump(), status="ready",
                        steps=[WorkflowStep(action="run_cobra", purpose="p")])
    invocations = []

    def graph(_app, invocation):
        invocations.append(invocation)
        dry_run = ToolExecutionResult(action="run_cobra", status="dry_run", summary="command preview")
        return {"messages": [*invocation["messages"], AIMessage(content="preview")], "decision": plan.decision,
                "plan": plan.model_dump(), "tool_results": [dry_run.model_dump()], "token_usage": None,
                "evaluation": EvaluationResult(status="completed", reason="dry run").model_dump(),
                "input_revisions": previewed}

    bootstrap = importlib.import_module("netzoo_agent_core.cli.bootstrap")
    recorder = Mock()
    recorder.start_run.return_value = "run"
    runtime = bootstrap.CliRuntime(
        memory=SimpleNamespace(profile_id="p", profile_store=Mock(), episode_store=Mock()), project_policy=Mock(),
        session_id="0a1b2c3d", resume_id=None, conversation=[], pending_plan=None, active_usage=None, run_id=None,
        recorder=recorder, trace_store=Mock(), ensure_trace_sync=lambda _run_id: None, app=object(),
        input_func=Mock(), invoke_graph_turn_func=graph, reply_resolver=Mock())
    machine = ConversationMachine(SimpleNamespace(task="Run COBRA on my files.", keep_session=True), runtime)
    machine.next_action()
    machine.run_turn()
    assert machine.state.preview is not None and machine.state.preview.input_revisions == previewed
    assert invocations[0]["previewed_inputs"] is None
    machine.state.execution_confirmation_task = machine.state.preview.task
    machine._submit_execution_confirmation("y")
    machine.run_turn()
    assert invocations[1]["previewed_inputs"] == previewed
