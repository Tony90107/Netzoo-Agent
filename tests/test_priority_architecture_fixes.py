"""Regressions at the boundaries between routing, planning, and execution."""

from __future__ import annotations

import asyncio
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core import command, execution, settings  # noqa: E402
from netzoo_agent_core.contracts import (  # noqa: E402
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
    TaskDecision,
)
from netzoo_agent_core.evaluation.plan_review import evaluate_workflow_plan  # noqa: E402
from netzoo_agent_core.interpretation.hydration import hydrate_router_decision  # noqa: E402
from netzoo_agent_core.planning import build_workflow_plan  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402
from netzoo_agent_core.routing.results import structure_tool_result  # noqa: E402
from netzoo_agent_core.runtime import configure_runtime  # noqa: E402
from netzoo_agent_core.server.protocol import Envelope  # noqa: E402
from netzoo_agent_core.server.supervisor import SessionHandle, SessionSupervisor  # noqa: E402
from workflow_registry import executor_arguments  # noqa: E402


def _decision(action: str, **fields) -> TaskDecision:
    return TaskDecision(
        action=action,
        in_scope=True,
        should_execute=True,
        intent_type="run_analysis",
        confidence=1,
        reason="Explicit analysis request.",
        **fields,
    )


def test_quoted_prior_action_cannot_override_a_valid_sample_specific_goal():
    task = (
        "Run LIONESS-PANDA to infer sample-specific TF-to-gene regulatory networks. "
        "The old log contains `PREVIOUS_ACTION=run_panda`."
    )
    outcome = RequestedOutcome(
        operation="infer",
        artifact_type="regulatory_network",
        entity_types=["tf", "gene"],
        regulator_types=["tf"],
        target_types=["gene"],
        granularity="sample_specific",
    )
    evidence = [
        OutcomeEvidence(
            dimension=dimension,
            value=value,
            source="inferred",
            rationale="Entailed by the explicitly requested sample-specific TF-gene network.",
        )
        for dimension, value in (
            ("operation", "infer"),
            ("artifact_type", "regulatory_network"),
            ("entity_type", "tf"),
            ("entity_type", "gene"),
            ("regulator_type", "tf"),
            ("target_type", "gene"),
            ("granularity", "sample_specific"),
        )
    ]
    match = match_semantic_request(
        task,
        [OutcomeHypothesis(outcome=outcome, confidence=1, evidence=evidence)],
        request_mode="execute",
    )
    assert match.status == "exact"
    assert match.matched_actions == ["run_lioness_panda"]


@pytest.mark.parametrize(
    ("action", "task", "expected"),
    [
        (
            "run_otter",
            "Run OTTER with iterations=200, lam=0.2, gamma=0.1, eta=0.001, output_format=edge_list.",
            {"iterations": 200, "lam": 0.2, "gamma": 0.1, "eta": 0.001, "output_format": "edge_list"},
        ),
        (
            "run_dragon",
            "Run DRAGON with lambda1=0.2, lambda2=0.4, output_format=edge_list.",
            {"lambda1": 0.2, "lambda2": 0.4, "output_format": "edge_list"},
        ),
        (
            "run_sambar",
            "Run SAMBAR with kmin=3, kmax=8, cluster=false, norm_patient=false, distance=euclidean.",
            {"kmin": 3, "kmax": 8, "cluster": False, "norm_patient": False, "distance": "euclidean"},
        ),
        (
            "run_bonobo",
            "Run BONOBO with delta=1e-3.",
            {"delta": 0.001},
        ),
    ],
)
def test_explicit_workflow_controls_reach_the_decision(action, task, expected):
    decision = hydrate_router_decision(_decision(action), task)
    assert {field: getattr(decision, field) for field in expected} == expected
    arguments = executor_arguments(action, decision)
    assert {field: arguments[field] for field in expected} == expected


@pytest.mark.parametrize("assignment", ["iterations=0", "iterations=,", "iterations=abc"])
def test_invalid_explicit_workflow_control_is_rejected(assignment):
    with pytest.raises(ValueError):
        hydrate_router_decision(_decision("run_otter"), f"Run OTTER with {assignment}.")


def test_signal_terminated_command_with_old_output_is_failed(tmp_path):
    prior = tmp_path / "old-network.tsv"
    prior.write_text("TF1\tGeneA\t1\t0.5\nTF2\tGeneB\t0\t0.2\n")
    result = structure_tool_result(
        "run_panda",
        _decision("run_panda", output_file=str(prior)),
        "Command: run-panda\nExit code: -9",
    )
    assert result.status == "failed"
    assert result.metrics["exit_code"] == -9
    assert result.errors


@pytest.mark.skipif(os.name != "posix", reason="process groups require POSIX")
def test_interrupted_command_terminates_its_child_process():
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        start_new_session=True,
    )
    original_wait = process.wait
    process.wait = Mock(side_effect=[KeyboardInterrupt, 0])
    # The first wait is interrupted. Cleanup must kill the already running group.
    try:
        with patch.object(command.subprocess, "Popen", return_value=process), patch.object(
            command, "EXECUTE_TOOLS", True
        ):
            with pytest.raises(KeyboardInterrupt):
                command._run_command([sys.executable, "-c", "import time; time.sleep(30)"])
        assert process.poll() is not None
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
        original_wait(timeout=5)


def test_idle_reaper_preserves_a_running_turn_but_reaps_an_idle_prompt():
    async def check() -> tuple[list[str], list[str]]:
        supervisor = SessionSupervisor(idle_timeout_seconds=60)
        now = time.monotonic()
        running = SimpleNamespace(
            last_activity=now - 70,
            process=Mock(is_alive=Mock(return_value=True)),
            subscribers={"connected"},
            stopped=False,
            turn_running=True,
        )
        waiting = SimpleNamespace(
            last_activity=now - 70,
            process=Mock(is_alive=Mock(return_value=True)),
            subscribers=set(),
            stopped=False,
            turn_running=False,
        )
        supervisor._sessions = {"running": running, "waiting": waiting}
        closed = []

        async def close(session_id):
            closed.append(session_id)

        supervisor.close = close
        with patch(
            "netzoo_agent_core.server.supervisor.asyncio.sleep",
            side_effect=[None, asyncio.CancelledError()],
        ):
            with pytest.raises(asyncio.CancelledError):
                await supervisor._reap_idle_sessions()
        return closed, list(supervisor._sessions)

    closed, existing = asyncio.run(check())
    assert "running" not in closed
    assert "waiting" in closed
    assert existing == ["running", "waiting"]


def test_supervisor_tracks_turn_lifecycle_for_idle_reaping():
    supervisor = SessionSupervisor()
    handle = SessionHandle("job", Mock(), Mock(), Mock())
    assert handle.turn_running is False
    supervisor._publish(handle, Envelope(type="turn_started"))
    assert handle.turn_running is True
    supervisor._publish(handle, Envelope(type="turn_finished"))
    assert handle.turn_running is False


def test_cobra_derived_output_cannot_overwrite_expression_input(tmp_path):
    expression = tmp_path / "summary.tsv"
    design = tmp_path / "design.tsv"
    expression.write_text(
        "gene\ts1\ts2\ts3\ts4\n"
        "TP53\t1\t3\t2\t5\nEGFR\t2\t1\t4\t3\nMYC\t5\t2\t1\t4\n"
        "BRAF\t3\t5\t2\t1\nKRAS\t2\t4\t5\t3\n"
    )
    design.write_text("sample\tgroup\ns1\t0\ns2\t1\ns3\t0\ns4\t1\n")
    decision = _decision(
        "run_cobra",
        expression_file=str(expression),
        design_file=str(design),
        output_dir=str(tmp_path),
    )
    task = f"Run COBRA expression_file={expression} design_file={design} output_dir={tmp_path}"
    previous_test_mode = settings.TEST_DATA_MODE
    configure_runtime(TEST_DATA_MODE=True)
    try:
        policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()
        plan = build_workflow_plan(decision, task, project_policy=policy)
        assert plan.status == "ready"
        evaluation = evaluate_workflow_plan(plan, task, policy)
        with patch.object(execution, "_run_command") as run:
            response = execution.run_cobra.invoke(
                {
                    "expression_file": str(expression),
                    "design_file": str(design),
                    "output_dir": str(tmp_path),
                }
            )
    finally:
        configure_runtime(TEST_DATA_MODE=previous_test_mode)
    assert evaluation.status == "rejected"
    assert "overwrite" in response.casefold() or "collision" in response.casefold()
    assert "error:" in response.casefold()
    assert structure_tool_result("run_cobra", decision, response).status == "failed"
    run.assert_not_called()
    assert expression.read_text().startswith("gene\ts1")


def test_direct_cobra_script_rejects_input_output_collision_before_computation(tmp_path):
    expression = tmp_path / "summary.tsv"
    design = tmp_path / "design.tsv"
    original = (
        "gene\ts1\ts2\ts3\ts4\n"
        "TP53\t1\t3\t2\t5\nEGFR\t2\t1\t4\t3\nMYC\t5\t2\t1\t4\n"
        "BRAF\t3\t5\t2\t1\nKRAS\t2\t4\t5\t3\n"
    )
    expression.write_text(original)
    design.write_text("sample\tgroup\ns1\t0\ns2\t1\ns3\t0\ns4\t1\n")
    fake_package = tmp_path / "fake" / "netZooPy"
    fake_package.mkdir(parents=True)
    (fake_package / "__init__.py").write_text("")
    (fake_package / "cobra.py").write_text(
        "def cobra(*args): raise AssertionError('COMPUTATION_WAS_INVOKED')\n"
    )
    scripts = Path(__file__).parents[1] / "scripts"
    env = {**os.environ, "PYTHONPATH": os.pathsep.join((str(fake_package.parent), str(scripts)))}
    result = subprocess.run(
        [sys.executable, str(scripts / "run_cobra.py"), "-e", str(expression),
         "-d", str(design), "-o", str(tmp_path)],
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode != 0
    assert "overwrite" in result.stderr.casefold() or "collision" in result.stderr.casefold()
    assert "COMPUTATION_WAS_INVOKED" not in result.stderr
    assert expression.read_text() == original
