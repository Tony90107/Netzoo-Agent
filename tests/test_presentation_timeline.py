from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core import runtime, settings  # noqa: E402
from netzoo_agent_core.cli.loop import run_cli  # noqa: E402
import netzoo_agent_core.presentation as presentation  # noqa: E402


def test_presentation_mode_is_mutable(monkeypatch):
    monkeypatch.setattr(settings, "PRESENTATION_MODE", "compact")

    runtime.configure_runtime(PRESENTATION_MODE="timeline")

    assert settings.PRESENTATION_MODE == "timeline"


def test_run_cli_selects_timeline_without_transient_output(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "netzoo_agent_core.cli.loop.configure_runtime",
        lambda **values: captured.update(values),
    )
    monkeypatch.setattr(
        "netzoo_agent_core.cli.loop.handle_preflight_command",
        lambda _args: 0,
    )
    args = SimpleNamespace(
        execute=False,
        quiet=False,
        verbose=False,
        timeline=True,
        transient_trace=False,
        tool_timeout=30.0,
    )

    assert run_cli(args) == 0
    assert captured["PRESENTATION_MODE"] == "timeline"
    assert captured["TRANSIENT_TRACE"] is False


def _enable_timeline(monkeypatch) -> None:
    monkeypatch.setattr(presentation, "TRACE_ENABLED", True)
    monkeypatch.setattr(presentation, "PRESENTATION_MODE", "timeline")


def test_timeline_renders_permanent_tool_start(monkeypatch, capsys):
    _enable_timeline(monkeypatch)

    presentation._trace(
        "tool", "Executor [1/2]: inspect_inputs", "Check supplied files"
    )

    output = capsys.readouterr().out
    assert "[Tool] Validating inputs" in output
    assert "Tool: inspect_inputs" in output
    assert "Purpose: Check supplied files" in output
    assert "\033[2K" not in output


def test_timeline_renders_tool_completion(monkeypatch, capsys):
    _enable_timeline(monkeypatch)

    presentation._trace(
        "tool", "inspect_inputs → success", "All identifiers matched"
    )

    output = capsys.readouterr().out
    assert "[Tool result] Input validation passed" in output
    assert "Tool: inspect_inputs" in output
    assert "Result: All identifiers matched" in output


def test_timeline_renders_intent_plan_review_input_evaluation_and_recovery(
    monkeypatch, capsys
):
    _enable_timeline(monkeypatch)

    presentation._trace("intent", "Classified as run_panda", "Confidence 0.90")
    presentation._trace("plan", "Planner: PANDA / ready", "unbounded plan detail")
    presentation._trace("review", "Plan evaluation approved (100/100)", "raw rubric")
    presentation._trace("input", "The Planner requires additional input", "Choose input")
    presentation._trace("evaluate", "Evaluator: completed", "All steps succeeded")
    presentation._trace("recover", "Planner recovery plan (attempt 1/1)", "raw plan")

    output = capsys.readouterr().out
    assert "[Understanding request]" in output
    assert "[Preparing plan]" in output
    assert "Workflow: PANDA · Status: ready" in output
    assert "[Plan review]" in output
    assert "[Input required]" in output
    assert "[Evaluating result]" in output
    assert "[Recovery]" in output
    assert "unbounded plan detail" not in output
    assert "raw rubric" not in output
    assert "raw plan" not in output


def test_timeline_rewrites_no_tool_router_state_as_public_summary(monkeypatch, capsys):
    _enable_timeline(monkeypatch)

    presentation._trace(
        "intent", "Classified as no_tool", "Confidence 0.90 | concept question"
    )

    output = capsys.readouterr().out
    assert "no_tool" not in output
    assert "do not need to inspect files or run tools" in output


def test_timeline_suppresses_setup_completion_and_unknown_events(monkeypatch, capsys):
    _enable_timeline(monkeypatch)

    for stage, message in (
        ("policy", "Project policy loaded: version=1, hash=abc"),
        ("memory", "Memory retrieval: profile=default, episodes=0"),
        ("done", "Session: abc123"),
        ("done", "LLM tokens: input=1, output=2, total=3, budget=10"),
        ("unknown", "State dump: secret"),
    ):
        presentation._trace(stage, message, "raw private payload")

    assert capsys.readouterr().out == ""
