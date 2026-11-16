"""A stream of envelopes becomes one result, and loses nothing on the way.

``TurnCollector`` is the adapter between what a worker publishes and what an
MCP tool returns. These tests feed it fixed sequences, so each rule is checked
without a worker, a supervisor or a client.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.mcp_server.turn import PROGRESS_LIMIT, TurnCollector  # noqa: E402
from netzoo_agent_core.server.protocol import Envelope  # noqa: E402


def _e(kind: str, **payload) -> Envelope:
    return Envelope(type=kind, session_id="s1", payload=payload)


def _view(**overrides) -> Envelope:
    payload = {
        "prompt_kind": "main",
        "text": "[Planning] What would you like to do?",
        "menu_enabled": True,
        "mode": "Planning",
        "plan": None,
        "plan_hash": None,
        "next_prompt": {"kind": "initial", "question": "What would you like to do?"},
        "target_field": None,
        "choosing_bundle": False,
        "preflight_correction": False,
        "card": None,
    }
    payload.update(overrides)
    return _e("view", **payload)


def _collect(*envelopes: Envelope, **options) -> TurnCollector:
    collector = TurnCollector("s1", **options)
    for envelope in envelopes:
        collector.feed(envelope)
    return collector


def test_a_turn_ends_at_the_next_question_not_at_turn_finished():
    collector = TurnCollector("s1")
    for envelope in (
        _e("turn_started", task="first", execute_once=False),
        _e("message", text="First reply."),
        _e("turn_finished"),
        # The machine queued a second turn; there is still no question.
        _e("turn_started", task="second", execute_once=False),
        _e("message", text="Second reply."),
        _e("turn_finished"),
    ):
        assert collector.feed(envelope) is False
    assert collector.feed(_view()) is True

    result = collector.result()
    assert result.status == "waiting_for_user"
    assert result.reply == "First reply.\n\nSecond reply."
    assert result.question == "[Planning] What would you like to do?"
    assert result.mode == "Planning"


def test_reply_text_is_passed_through_unchanged():
    text = "  PANDA needs:\n  - expression\n\n  It does **not** infer per-sample networks.  "
    result = _collect(_e("message", text=text), _view()).result()
    assert result.reply == text


def test_notices_progress_and_usage_are_kept_apart_from_the_reply():
    result = _collect(
        _e("notice", text="Mode: Test"),
        _e("notice", text="   "),
        _e("progress", text="Reading the request"),
        _e("usage", total_tokens=120, budget_tokens=30000, calls=[{"model": "m"}]),
        _e("usage", total_tokens=310, budget_tokens=30000, calls=[{"model": "m"}, {"model": "m"}]),
        _e("message", text="Done."),
        _view(),
    ).result()
    assert result.notices == ["Mode: Test"]
    assert result.progress == ["Reading the request"]
    assert result.usage == {"total_tokens": 310, "budget_tokens": 30000}
    assert result.reply == "Done."


def test_trace_events_are_not_collected():
    result = _collect(
        _e("trace", event_type="node.started", payload={"text": "secret reasoning"}),
        _e("message", text="Answer."),
        _view(),
    ).result()
    assert "secret reasoning" not in result.model_dump_json()


def test_only_the_last_progress_lines_are_kept():
    collector = TurnCollector("s1")
    for index in range(PROGRESS_LIMIT + 15):
        collector.feed(_e("progress", text=f"line {index}"))
    progress = collector.result().progress
    assert len(progress) == PROGRESS_LIMIT
    assert progress[-1] == f"line {PROGRESS_LIMIT + 14}"


def test_a_running_result_hands_over_what_it_has_exactly_once():
    collector = TurnCollector("s1", mode="Planning")
    collector.feed(_e("message", text="Part one."))
    collector.feed(_e("progress", text="Running PANDA"))

    running = collector.result()
    assert running.status == "running"
    assert running.reply == "Part one."
    assert running.progress == ["Running PANDA"]
    assert running.question is None
    assert running.mode == "Planning"

    collector.feed(_e("message", text="Part two."))
    collector.feed(_view())
    finished = collector.result()
    assert finished.status == "waiting_for_user"
    assert finished.reply == "Part two."
    assert finished.progress == []


def test_a_refused_answer_is_reported_with_the_question_that_is_still_open():
    result = _collect(
        _e("error", error_type="StalePlanHash", message="not the plan this session holds"),
        _view(prompt_kind="execution_confirmation"),
    ).result()
    assert result.status == "waiting_for_user"
    assert result.prompt_kind == "execution_confirmation"
    assert [error.error_type for error in result.errors] == ["StalePlanHash"]


def test_a_worker_failure_ends_the_turn_as_an_error():
    result = _collect(
        _e("error", error_type="RuntimeError", message="bootstrap failed"),
        _e("stopped", exit_code=1),
    ).result()
    assert result.status == "error"
    assert result.errors[0].message == "bootstrap failed"


def test_a_clean_stop_is_not_an_error():
    result = _collect(_e("notice", text="Goodbye."), _e("stopped", exit_code=0)).result()
    assert result.status == "stopped"
    assert result.notices == ["Goodbye."]


def test_an_answer_refused_before_the_worker_ends_the_collection():
    collector = _collect(
        _e("error", error_type="StalePromptSeq", message="older prompt"),
    )
    assert collector.done
    assert collector.result().status == "error"


def test_a_session_that_goes_away_ends_the_turn():
    collector = _collect(_e("message", text="Half."))
    collector.close()
    result = collector.result()
    assert result.status == "stopped"
    assert result.reply == "Half."


def test_feeding_a_finished_turn_is_a_bug():
    collector = _collect(_view())
    with pytest.raises(RuntimeError):
        collector.feed(_e("message", text="late"))


# -- the open question ---------------------------------------------------------

_PLAN = {
    "workflow": "PANDA",
    "objective": "Infer an aggregate regulatory network",
    "decision": {},
    "status": "ready",
    "question": None,
    "missing_inputs": [],
    "evidence": [
        {"field": "expression_file", "status": "provided", "value": "/work/data/e.tsv", "reason": "stated"},
    ],
    "steps": [{"action": "run_panda", "purpose": "Run PANDA", "arguments": {"with_header": False}}],
    "input_bundle_options": [],
}


def _previewed_view(**overrides) -> Envelope:
    return _view(
        plan=_PLAN,
        plan_hash="a" * 64,
        next_prompt={"kind": "dry_run", "question": "Run it?"},
        **overrides,
    )


def test_a_previewed_plan_can_be_run_only_when_the_server_allows_it():
    off = _collect(_previewed_view()).result()
    assert off.can_execute is False and off.execute_enabled is False
    assert off.plan_hash == "a" * 64

    on = _collect(_previewed_view(), execute_enabled=True).result()
    assert on.can_execute is True and on.execute_enabled is True
    assert on.plan.workflow == "PANDA"
    assert on.plan.steps[0].action == "run_panda"
    assert on.plan.evidence[0].value == "/work/data/e.tsv"


@pytest.mark.parametrize(
    "overrides",
    [
        {"next_prompt": {"kind": "completed", "question": "Anything else?"}},
        {"prompt_kind": "clarification"},
        {"plan_hash": None},
    ],
)
def test_a_plan_that_was_not_previewed_cannot_be_run(overrides):
    view = _previewed_view()
    view.payload.update(overrides)
    assert _collect(view, execute_enabled=True).result().can_execute is False


def test_card_options_say_which_tool_submits_them():
    card = {
        "kind": "plan_ready",
        "choices": {
            "header": "Next",
            "question": "What next?",
            "options": [
                {"key": "a", "label": "PANDA", "answer": "Use PANDA", "recommended": True,
                 "resolution": "plan_workflow"},
                {"key": "b", "label": "Run it", "answer": "/execute", "resolution": "command"},
                {"key": "c", "label": "Test mode", "answer": "/test", "resolution": "command"},
                {"key": "d", "label": "Start over", "answer": "new", "resolution": "command"},
            ],
        },
        "next_steps": [
            {"key": "e", "label": "Open outputs", "resolution": "open_outputs",
             "paths": ["outputs/s1/panda.tsv"]},
        ],
        "unavailable": [
            {"key": "f", "label": "ALPACA", "available": False, "reason": "not installed here",
             "resolution": "none"},
        ],
    }
    result = _collect(
        _view(card=card), to_host=lambda path: f"/Users/me/netzoo/{path}"
    ).result()
    assert [(option.label, option.via) for option in result.options] == [
        ("PANDA", "netzoo_ask"),
        ("Run it", "netzoo_execute"),
        ("Test mode", "netzoo_set_mode"),
        ("Start over", "netzoo_ask"),
        ("Open outputs", "netzoo_list_outputs"),
        ("ALPACA", "none"),
    ]
    assert result.options[0].recommended is True
    assert result.options[-1].reason == "not installed here"
    assert [(ref.path, ref.host_path) for ref in result.outputs] == [
        ("outputs/s1/panda.tsv", "/Users/me/netzoo/outputs/s1/panda.tsv")
    ]


def test_text_carried_from_an_earlier_step_comes_first():
    collector = TurnCollector("s1")
    collector.carry(messages=["Before."], notices=["Confirm below to execute it once."])
    collector.feed(_e("message", text="After."))
    collector.feed(_view())
    result = collector.result()
    assert result.reply == "Before.\n\nAfter."
    assert result.notices == ["Confirm below to execute it once."]
