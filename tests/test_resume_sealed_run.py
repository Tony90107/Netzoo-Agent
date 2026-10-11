"""Continuing a finished one-shot session with --resume (Log 404 harness, 2026-10-11).

`netzoo_agent.py --session S --task ...` seals the run's trace when the turn ends, and the
next `--resume S --task ...` crashed with "cannot append to a sealed trace run"; with that fixed,
the finished turn's token usage was carried into the new turn and blocked its routing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.cli.bootstrap import resumed_run_id  # noqa: E402
from netzoo_agent_core.trace_store import LocalTraceStore  # noqa: E402
from netzoo_agent_core.tracing import TraceRecorder  # noqa: E402


def _store(tmp_path):
    store = LocalTraceStore(tmp_path / "traces")
    return store, TraceRecorder(store)


def test_a_sealed_run_is_continued_in_a_new_run_that_names_it(tmp_path):
    store, recorder = _store(tmp_path)
    first = recorder.start_run(session_id="s", profile_id="default")
    store.finish_run(first, "completed", {"result": "ok"})

    run_id, paused = resumed_run_id(store, recorder, str(first), session_id="s", profile_id="default")

    assert not paused  # a new turn, with a new token budget
    assert run_id != str(first) and not store.verify_run(run_id).sealed
    resumed = [event for event in store.read_events(run_id) if event.event_type == "run.resumed"]
    assert resumed[0].payload["previous_run_id"] == str(first)


def test_a_paused_run_continues_in_place(tmp_path):
    store, recorder = _store(tmp_path)
    first = recorder.start_run(session_id="s", profile_id="default")
    store.pause_run(first, {"reason": "needs_input"})

    assert resumed_run_id(store, recorder, str(first), session_id="s", profile_id="default") == (str(first), True)


def test_a_session_without_a_run_starts_one(tmp_path):
    store, recorder = _store(tmp_path)
    run_id, paused = resumed_run_id(store, recorder, None, session_id="s", profile_id="default")
    assert run_id and not paused
