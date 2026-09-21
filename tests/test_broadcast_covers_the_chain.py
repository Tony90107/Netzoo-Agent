"""Whatever the hash chain accepts, the UI is told about.

The timeline's whole claim is that it shows the run. A first version wrapped
the recorder rather than the store, so `pause_run` and `finish_run` -- which
append through the store directly -- were never published, and a paused run
reached the window one event short of its own trace file. That is the failure
this pins: not "some events arrive", but "the same events, in the same order".
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.server.broadcast_recorder import (  # noqa: E402
    BroadcastTraceStore,
    broadcast_recorder_factory,
)
from netzoo_agent_core.trace_store import LocalTraceStore  # noqa: E402
from netzoo_agent_core.tracing import TraceRecorder  # noqa: E402


def _chain(root: Path, run_id) -> list[dict]:
    path = next(Path(root).glob(f"{run_id}/events.jsonl"))
    return [json.loads(line) for line in path.read_text().splitlines()]


def _recorder(tmp_path: Path) -> tuple[TraceRecorder, list[dict], Path]:
    published: list[dict] = []
    root = tmp_path / "traces"
    store = LocalTraceStore(root)
    store.preflight()
    recorder = broadcast_recorder_factory(published.append)(store)
    return recorder, published, root


def test_a_paused_run_publishes_every_event_the_chain_holds(tmp_path):
    recorder, published, root = _recorder(tmp_path)

    run_id = recorder.start_run(session_id="s", profile_id="p")
    recorder.append(run_id, "node.started", "classify", {})
    recorder.append(run_id, "llm.completed", "classify", {"total_tokens": 12})
    recorder.append(run_id, "node.finished", "classify", {"duration_ms": 5})
    recorder.pause_run(run_id, {"reason": "needs_input"})

    chain = _chain(root, run_id)
    assert [event["event_type"] for event in published] == [
        event["event_type"] for event in chain
    ]
    assert "run.paused" in [event["event_type"] for event in published]


def test_a_finished_run_publishes_its_terminal_event(tmp_path):
    recorder, published, root = _recorder(tmp_path)

    run_id = recorder.start_run(session_id="s", profile_id="p")
    recorder.finish_run(run_id, "completed", {"evaluation_status": "passed"})

    chain = _chain(root, run_id)
    assert len(published) == len(chain)
    assert published[-1]["event_type"] == "run.finished"


def test_events_are_published_in_chain_order(tmp_path):
    recorder, published, root = _recorder(tmp_path)

    run_id = recorder.start_run(session_id="s", profile_id="p")
    for index in range(8):
        recorder.append(run_id, "node.started", f"n{index}", {})
    recorder.finish_run(run_id, "completed", {})

    assert [event["sequence"] for event in published] == [
        event["sequence"] for event in _chain(root, run_id)
    ]


def test_a_broken_ui_connection_does_not_break_the_run(tmp_path):
    """Observability must never change the outcome of a turn."""
    root = tmp_path / "traces"
    LocalTraceStore(root).preflight()

    def explode(_event: dict) -> None:
        raise RuntimeError("the window went away")

    recorder = TraceRecorder(BroadcastTraceStore(root, explode))
    run_id = recorder.start_run(session_id="s", profile_id="p")
    recorder.append(run_id, "node.started", "classify", {})
    recorder.finish_run(run_id, "completed", {})

    # The chain is intact even though every publish raised.
    assert len(_chain(root, run_id)) == 3


def test_publishing_happens_after_the_event_is_durable(tmp_path):
    """A timeline may never show something the trace file does not have."""
    root = tmp_path / "traces"
    store_root = root
    LocalTraceStore(store_root).preflight()
    seen_on_disk: list[int] = []

    def record_chain_length(_event: dict) -> None:
        path = store_root.glob("*/events.jsonl")
        seen_on_disk.append(sum(len(p.read_text().splitlines()) for p in path))

    recorder = TraceRecorder(BroadcastTraceStore(store_root, record_chain_length))
    run_id = recorder.start_run(session_id="s", profile_id="p")
    recorder.append(run_id, "node.started", "classify", {})

    # At each publish the event being published was already on disk, so the
    # count never lags the number of events published so far.
    assert seen_on_disk == [1, 2]
    assert run_id is not None
