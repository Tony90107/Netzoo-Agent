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
    try:
        runtime.configure_runtime(PRESENTATION_MODE="timeline")
        assert settings.PRESENTATION_MODE == "timeline"
    finally:
        runtime.configure_runtime(PRESENTATION_MODE="compact")


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


def test_run_cli_uses_state_machine_by_default(monkeypatch):
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
        timeline=False,
        transient_trace=False,
        tool_timeout=30.0,
    )

    assert run_cli(args) == 0
    assert captured["PRESENTATION_MODE"] == "state_machine"


def _enable_timeline(monkeypatch) -> None:
    monkeypatch.setattr(presentation, "TRACE_ENABLED", True)
    monkeypatch.setattr(presentation, "PRESENTATION_MODE", "timeline")


def _enable_state_machine(monkeypatch) -> None:
    monkeypatch.setattr(presentation, "TRACE_ENABLED", True)
    monkeypatch.setattr(presentation, "PRESENTATION_MODE", "state_machine")
    monkeypatch.setattr(presentation, "_PROGRESS_STATE", None)
    monkeypatch.setattr(presentation, "_PROGRESS_RENDERED_LINES", 0)
    monkeypatch.setattr(presentation, "_PROGRESS_LAST_TEXT", None)
    monkeypatch.setattr(presentation, "_COMMITTED_ACTIVITY_KEYS", set())


def test_progress_state_marks_only_one_stage_active():
    state = presentation.ProgressState.initial()
    state.activate("match", "Matching registered workflows")

    assert presentation._render_progress_state(state) == "● Matching registered workflows…"


def test_progress_state_marks_clarification_as_attention():
    state = presentation.ProgressState.initial()
    state.complete("understand")
    state.complete("match")
    state.attention("next_step", "Clarification required")

    assert "? Clarification needed\n  Clarification required" == presentation._render_progress_state(state)


def test_progress_state_can_show_clarification_without_repeating_the_question():
    state = presentation.ProgressState.initial()
    state.complete("understand")
    state.complete("match")
    state.attention("next_step")

    assert presentation._render_progress_state(state) == "? Clarification needed"


def test_public_trace_events_update_task_level_stages(monkeypatch, capsys):
    _enable_state_machine(monkeypatch)

    presentation._trace("intent", "Interpreting the request and capability boundaries")
    presentation._trace(
        "reasoning",
        "Checking registered workflow capabilities",
        "Matching registered workflows",
    )
    presentation._trace(
        "reasoning", "Choosing the next safe step", "Clarification required"
    )

    output = capsys.readouterr().out
    assert "● Classifying requested outcome…" in output
    assert "● Matching registered workflows…" in output
    assert "? Clarification needed\n  Clarification required" in output


def test_state_machine_redraws_on_tty(monkeypatch, capsys):
    _enable_state_machine(monkeypatch)
    monkeypatch.setattr(presentation.sys.stdout, "isatty", lambda: True)

    presentation._trace("intent", "Interpreting the request and capability boundaries")
    presentation._trace("reasoning", "Checking registered workflow capabilities")

    assert "\033[1A" in capsys.readouterr().out


def test_state_machine_uses_permanent_lines_on_non_tty(monkeypatch, capsys):
    _enable_state_machine(monkeypatch)
    monkeypatch.setattr(presentation.sys.stdout, "isatty", lambda: False)

    presentation._trace("intent", "Interpreting the request and capability boundaries")

    output = capsys.readouterr().out
    assert "\033[" not in output
    assert "● Classifying requested outcome…" in output


def test_state_machine_finalization_keeps_visible_output_and_resets_for_next_turn(
    monkeypatch, capsys
):
    _enable_state_machine(monkeypatch)
    monkeypatch.setattr(presentation.sys.stdout, "isatty", lambda: False)

    presentation._trace("intent", "Interpreting the request and capability boundaries")
    presentation._clear_transient_trace()

    assert "● Classifying requested outcome…" in capsys.readouterr().out
    assert presentation._PROGRESS_STATE is None


def test_tool_activity_is_permanent_and_fact_grounded(monkeypatch, capsys):
    _enable_state_machine(monkeypatch)
    monkeypatch.setattr(presentation.sys.stdout, "isatty", lambda: False)

    presentation._trace(
        "tool",
        "Executor [1/1]: run_lioness_puma",
        {
            "kind": "tool_activity",
            "purpose": "Infer selected network",
            "inputs": ["expression_file", "motif_file", "ppi_file", "mirna_file"],
        },
    )
    presentation._trace(
        "tool", "run_lioness_puma → success", "Generated 80 networks"
    )

    output = capsys.readouterr().out
    assert "Tool: run_lioness_puma" in output
    assert "Inputs: expression_file, motif_file, ppi_file, mirna_file" in output
    assert "Result: Generated 80 networks" in output
    assert "✓ Run LIONESS-PUMA" in output


def test_state_machine_suppresses_unmapped_graph_events(monkeypatch, capsys):
    _enable_state_machine(monkeypatch)
    monkeypatch.setattr(presentation.sys.stdout, "isatty", lambda: False)

    presentation._trace("plan", "Planner: NO-TOOL / respond_only", "private plan")

    assert capsys.readouterr().out == ""


def test_state_machine_shows_verified_decision_facts_without_a_tool(monkeypatch, capsys):
    _enable_state_machine(monkeypatch)
    monkeypatch.setattr(presentation.sys.stdout, "isatty", lambda: False)

    presentation._trace(
        "intent",
        "Classified as no_tool",
        {
            "kind": "classification",
            "outcome": "miRNA regulatory network",
            "workflows": ["PUMA", "LIONESS-PUMA"],
        },
    )
    presentation._trace(
        "reasoning",
        "Choosing the next safe step",
        {
            "kind": "next_step",
            "status": "clarification_required",
            "question": "Should the result be aggregate or sample-specific?",
            "tool_status": "No local tool has run yet.",
        },
    )

    output = capsys.readouterr().out
    assert "✓ Matched workflows — PUMA, LIONESS-PUMA" in output
    assert "? Clarification needed" in output
    assert "Should the result be aggregate or sample-specific?" not in output
    assert "Select aggregate or sample-specific" not in output


def test_state_machine_shows_router_then_registry_activity(monkeypatch, capsys):
    _enable_state_machine(monkeypatch)
    monkeypatch.setattr(presentation.sys.stdout, "isatty", lambda: False)

    presentation._trace(
        "router",
        "Router classification started",
        {"kind": "router_activity", "status": "started"},
    )
    presentation._trace(
        "reasoning",
        "Checking registered workflow capabilities",
        {"kind": "registry_activity", "status": "started"},
    )

    output = capsys.readouterr().out
    assert "● Classifying requested outcome…" in output
    assert "● Matching registered workflows…" in output


def test_state_machine_presents_initial_semantic_interpretation_as_classification(
    monkeypatch, capsys
):
    _enable_state_machine(monkeypatch)
    monkeypatch.setattr(presentation.sys.stdout, "isatty", lambda: False)

    presentation._trace(
        "router",
        "Semantic interpretation started",
        {
            "kind": "router_activity",
            "operation": "semantic_interpreter",
            "status": "started",
        },
    )
    presentation._trace(
        "router",
        "Semantic interpretation completed",
        {
            "kind": "router_activity",
            "operation": "semantic_interpreter",
            "status": "completed",
            "duration_ms": 1250,
        },
    )

    output = capsys.readouterr().out
    assert "● Classifying requested outcome…" in output
    assert "✓ Interpreted requested outcome (1.25s)" in output
    assert "Refined outcome classification" not in output


def test_state_machine_keeps_deduplicated_router_repair_and_match_history(monkeypatch, capsys):
    _enable_state_machine(monkeypatch)
    monkeypatch.setattr(presentation.sys.stdout, "isatty", lambda: False)
    completed = {"kind": "router_activity", "operation": "router_repair", "status": "completed", "duration_ms": 6603}
    presentation._trace("router", "Router classification completed", completed)
    presentation._trace("router", "Router classification completed", completed)
    presentation._trace("intent", "Classified as no_tool", {"kind": "classification", "outcome": "miRNA regulatory network", "workflows": ["PUMA", "LIONESS-PUMA"]})

    output = capsys.readouterr().out
    assert output.count("✓ Refined outcome classification (6.60s)") == 1
    assert "✓ Matched workflows — PUMA, LIONESS-PUMA" in output


def test_single_stream_hides_legacy_stage_labels(monkeypatch, capsys):
    _enable_state_machine(monkeypatch)
    monkeypatch.setattr(presentation.sys.stdout, "isatty", lambda: False)
    presentation._trace("router", "Router classification started", {"kind": "router_activity", "operation": "router", "status": "started"})
    output = capsys.readouterr().out
    assert "● Classifying requested outcome…" in output
    assert "Understand request" not in output


def test_state_machine_truncates_live_lines_to_terminal_width(monkeypatch):
    state = presentation.ProgressState.initial()
    state.activate("match", "A detail that cannot fit on a narrow terminal row")
    monkeypatch.setattr(presentation, "_terminal_columns", lambda: 32)

    lines = presentation._render_progress_state(state).splitlines()

    assert len(lines) == 1
    assert all(len(line) <= 32 for line in lines)


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


def test_timeline_renders_public_reasoning_stages(monkeypatch, capsys):
    _enable_timeline(monkeypatch)

    presentation._trace(
        "reasoning",
        "Checking registered workflow capabilities",
        "Comparing the goal with registered workflows.",
    )
    presentation._trace(
        "reasoning",
        "Choosing the next safe step",
        "Answering from registered information without tools.",
    )

    output = capsys.readouterr().out
    assert "[Checking available workflows]" in output
    assert "[Choosing next step]" in output
    assert "Comparing the goal with registered workflows." in output
    assert "Answering from registered information without tools." in output


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
