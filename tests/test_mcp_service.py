"""The MCP conversation tools reach the same states as the window and the terminal.

Most tests here run the real ``SessionSupervisor``, the real ``WorkerDriver``
and the real ``ConversationMachine``; only the graph invocation is faked, the
same seam ``test_server_driver`` uses. The rest use a scripted worker where the
point is timing or what the worker is sent, not what the agent decides.
"""

from __future__ import annotations

import asyncio
import queue
import sys
import threading
import time
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

import pytest

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core import settings  # noqa: E402
from netzoo_agent_core.contracts import WorkflowPlan  # noqa: E402
from netzoo_agent_core.engine import ConversationMachine  # noqa: E402
from netzoo_agent_core.mcp_server.backend import BackendError, EmbeddedBackend  # noqa: E402
from netzoo_agent_core.mcp_server.service import NetzooService, ServiceError  # noqa: E402
from netzoo_agent_core.runtime import configure_runtime  # noqa: E402
from netzoo_agent_core.server import history  # noqa: E402
from netzoo_agent_core.server.channel import QueueChannel  # noqa: E402
from netzoo_agent_core.server.driver import WorkerDriver  # noqa: E402
from netzoo_agent_core.server.path_mapper import PathMapper  # noqa: E402
from netzoo_agent_core.server.protocol import Envelope, plan_hash  # noqa: E402
from netzoo_agent_core.server.supervisor import SessionSupervisor  # noqa: E402

from test_cli_lifecycle import (  # noqa: E402
    _fake_cli_runtime,
    _guidance_result,
    _workflow_result,
)

GOAL = "explain the difference between PANDA and PUMA"
RUN_TASK = "run the selected LIONESS-PUMA bundle"
HOST_ROOT = "/Users/me/LLM AGENT/netzoo_agent"


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "SESSION_ROOT", tmp_path)
    previous = {
        name: getattr(settings, name)
        for name in ("EXECUTE_TOOLS", "TEST_DATA_MODE", "PRESENTATION_MODE")
    }
    configure_runtime(EXECUTE_TOOLS=False, TEST_DATA_MODE=False, PRESENTATION_MODE="state_machine")
    yield
    configure_runtime(**previous)


class _ThreadWorker:
    def __init__(self, target, args):
        self._thread = threading.Thread(target=target, args=args, daemon=True)
        self.pid = None

    def start(self) -> None:
        self._thread.start()

    def is_alive(self) -> bool:
        return self._thread.is_alive()

    def join(self, timeout=None) -> None:
        self._thread.join(timeout)

    def terminate(self) -> None:
        return None


def _machine_worker(runtime):
    """A worker that runs the real driver and machine over a faked graph."""

    def target(request: dict, inbox, outbox) -> int:
        machine = ConversationMachine(SimpleNamespace(task=None, keep_session=False), runtime)
        driver = WorkerDriver(machine, QueueChannel(inbox, outbox), session_id=request["session_id"])
        return driver.run()

    return target


def _main_view(text: str = "What next?") -> dict:
    return {"prompt_kind": "main", "text": text, "mode": "Planning", "menu_enabled": True,
            "plan": None, "plan_hash": None, "next_prompt": {"kind": "initial", "question": text}}


def _scripted_worker(script, *, seen=None, requests=None):
    """Publish a view, then for each answer whatever ``script(text)`` yields.

    A yielded number is a pause; anything else is ``(type, payload)``.
    """

    def target(request: dict, inbox, outbox) -> int:
        channel = QueueChannel(inbox, outbox)
        session_id = request["session_id"]
        if requests is not None:
            requests.append(dict(request))

        def send(kind: str, payload: dict | None = None) -> None:
            channel.send(Envelope(type=kind, session_id=session_id, payload=payload or {}))

        send("ready", {"session_id": session_id})
        send("view", _main_view())
        while True:
            envelope = channel.receive()
            if envelope is None:
                continue
            if envelope.type == "cancel":
                send("stopped", {"exit_code": 0})
                return 0
            text = str(envelope.payload.get("text") or "")
            if seen is not None:
                seen.append(text)
            for step in script(text):
                if isinstance(step, (int, float)):
                    time.sleep(step)
                else:
                    send(*step)
            send("view", _main_view())

    return target


def _run(scenario, target, *, mapper=None, **options):
    """Run ``scenario(service, supervisor)`` against a threaded supervisor."""

    async def main():
        supervisor = SessionSupervisor(
            worker_target=target,
            process_factory=lambda t, a: _ThreadWorker(t, a),
            queue_factory=queue.Queue,
        )
        backend = EmbeddedBackend(supervisor, preflight=lambda: None)
        service = NetzooService(
            backend,
            mapper=mapper or PathMapper(container_root=PurePosixPath("/work"), host_root=None),
            start_seconds=10.0,
            **options,
        )
        await backend.start()
        try:
            return await scenario(service, supervisor)
        finally:
            await service.shutdown()
            # Let the pump threads deliver each worker's last envelope before the loop closes.
            await asyncio.sleep(0.05)

    return asyncio.run(main())


def _published_messages(supervisor, session_id: str) -> list[str]:
    return [
        envelope.payload["text"]
        for envelope in supervisor.get(session_id).history
        if envelope.type == "message"
    ]


# -- a conversation --------------------------------------------------------------


def test_asking_starts_a_session_and_returns_the_agents_reply():
    runtime = _fake_cli_runtime(invoke_error=[_guidance_result(GOAL)])

    async def scenario(service, supervisor):
        result = await service.ask(GOAL)
        return result, _published_messages(supervisor, result.session_id)

    result, published = _run(scenario, _machine_worker(runtime))
    assert result.status == "waiting_for_user"
    assert result.prompt_kind == "main"
    assert result.mode == "Planning"
    assert "PUMA" in result.reply
    assert result.reply == "\n\n".join(published)
    assert result.resumed is False
    assert runtime.invoke_graph_turn_func.call_args.args[1]["messages"][-1].content == GOAL
    assert history.session_details(result.session_id)["tags"] == ["mcp"]


def test_every_message_the_worker_publishes_is_returned_exactly_once():
    runtime = _fake_cli_runtime(invoke_error=[_guidance_result(GOAL), _guidance_result(GOAL)])

    async def scenario(service, supervisor):
        first = await service.ask(GOAL)
        idle = await service.wait(first.session_id)
        # "back" leaves the follow-up prompt, so the next message is a new task.
        back = await service.ask("back", session_id=first.session_id)
        second = await service.ask(GOAL, session_id=first.session_id)
        return [first, idle, back, second], _published_messages(supervisor, first.session_id)

    results, published = _run(scenario, _machine_worker(runtime))
    assert len(published) == 2
    assert [result.reply for result in results] == [published[0], "", "", published[1]]
    assert all(result.status == "waiting_for_user" for result in results)


def test_a_slash_command_is_not_a_message():
    runtime = _fake_cli_runtime(invoke_error=AssertionError("graph must not run"))

    async def scenario(service, _supervisor):
        for text in ("/execute", "  /test", "/planning"):
            with pytest.raises(ServiceError, match="netzoo_execute"):
                await service.ask(text)
        with pytest.raises(ServiceError, match="empty"):
            await service.ask("   ")

    _run(scenario, _machine_worker(runtime))
    assert runtime.invoke_graph_turn_func.call_count == 0


def test_exit_ends_the_session():
    runtime = _fake_cli_runtime(invoke_error=AssertionError("graph must not run"))

    async def scenario(service, _supervisor):
        return await service.ask("exit")

    assert _run(scenario, _machine_worker(runtime)).status == "stopped"


# -- execution -------------------------------------------------------------------


def _dry_run_runtime():
    runtime = _fake_cli_runtime(
        invoke_error=[
            _workflow_result(RUN_TASK, status="dry_run"),
            _workflow_result(RUN_TASK, status="success"),
        ]
    )
    expected = plan_hash(WorkflowPlan.model_validate(_workflow_result(RUN_TASK, status="dry_run")["plan"]))
    return runtime, expected


async def _preview(service):
    """Reach a previewed plan the way ``test_server_driver`` does: in test mode."""
    switched = await service.set_mode("test")
    preview = await service.ask(RUN_TASK, session_id=switched.session_id)
    return switched, preview


def test_a_previewed_plan_runs_only_through_execute_with_its_hash():
    runtime, expected = _dry_run_runtime()

    async def scenario(service, _supervisor):
        switched, preview = await _preview(service)
        stale = await service.execute(preview.session_id, "0" * 64)
        calls_after_stale = runtime.invoke_graph_turn_func.call_count
        ran = await service.execute(preview.session_id, expected)
        return switched, preview, stale, calls_after_stale, ran

    switched, preview, stale, calls_after_stale, ran = _run(
        scenario, _machine_worker(runtime), execute_enabled=True
    )
    assert switched.mode == "Test" and switched.notices
    assert preview.can_execute is True
    assert preview.plan_hash == expected
    assert preview.plan.workflow == "LIONESS-PUMA"

    assert [error.error_type for error in stale.errors] == ["StalePlanHash"]
    assert stale.plan_hash == expected and stale.can_execute is True
    assert calls_after_stale == 1

    assert ran.status == "waiting_for_user"
    assert not ran.errors
    assert runtime.invoke_graph_turn_func.call_count == 2
    assert not any("confirm below" in notice.casefold() for notice in ran.notices), (
        "the confirmation netzoo_execute already gave must not read as a question still open"
    )
    assert settings.EXECUTE_TOOLS is False


def test_execution_is_off_unless_the_server_was_started_with_it():
    runtime, expected = _dry_run_runtime()

    async def scenario(service, _supervisor):
        _switched, preview = await _preview(service)
        with pytest.raises(ServiceError, match="NETZOO_MCP_EXECUTE"):
            await service.execute(preview.session_id, expected)
        return preview

    preview = _run(scenario, _machine_worker(runtime))
    assert preview.can_execute is False and preview.execute_enabled is False
    assert preview.plan_hash == expected
    assert runtime.invoke_graph_turn_func.call_count == 1


def test_nothing_runs_without_a_preview():
    runtime = _fake_cli_runtime(invoke_error=[_guidance_result(GOAL)])

    async def scenario(service, _supervisor):
        opened = await service.ask(GOAL)
        return await service.execute(opened.session_id, "a" * 64)

    result = _run(scenario, _machine_worker(runtime), execute_enabled=True)
    assert [error.error_type for error in result.errors] == ["NoPreviewedPlan"]
    assert runtime.invoke_graph_turn_func.call_count == 1


# -- long turns ------------------------------------------------------------------


def _two_part_turn(_text):
    yield ("turn_started", {"task": "t", "execute_once": False})
    yield ("progress", {"text": "Running PANDA"})
    yield ("message", {"text": "Part one."})
    yield 0.8
    yield ("message", {"text": "Part two."})
    yield ("turn_finished", {})


def test_a_long_turn_is_returned_in_parts_without_repeating_anything():
    progress: list[str] = []

    async def note(line: str) -> None:
        progress.append(line)

    async def scenario(service, _supervisor):
        first = await service.ask("go", on_progress=note)
        busy = await service.ask("again", session_id=first.session_id)
        rest = await service.wait(first.session_id, wait_seconds=10)
        return first, busy, rest

    seen: list[str] = []
    first, busy, rest = _run(scenario, _scripted_worker(_two_part_turn, seen=seen), wait_seconds=0.3)
    assert first.status == "running"
    assert first.reply == "Part one."
    assert first.progress == ["Running PANDA"] and progress == ["Running PANDA"]

    assert busy.status == "running"
    assert [error.error_type for error in busy.errors] == ["TurnInProgress"]
    assert busy.reply == ""
    assert seen == ["go"], "a message sent during a running turn must not reach the worker"

    assert rest.status == "waiting_for_user"
    assert rest.reply == "Part two."
    assert rest.progress == []


def test_cancel_with_nothing_running_says_so():
    async def scenario(service, _supervisor):
        opened = await service.ask("go")
        return await service.cancel(opened.session_id)

    result = _run(scenario, _scripted_worker(lambda _text: [("message", {"text": "ok"})]))
    assert [error.error_type for error in result.errors] == ["NothingRunning"]


# -- sessions --------------------------------------------------------------------


def test_a_session_that_was_never_saved_cannot_be_continued():
    async def scenario(service, _supervisor):
        with pytest.raises(BackendError, match="no saved session"):
            await service.ask("hello", session_id="nope1234")
        with pytest.raises(BackendError):
            await service.ask("hello", session_id="../../etc/passwd")
        with pytest.raises(ServiceError, match="not running here"):
            await service.wait("nope1234")

    _run(scenario, _scripted_worker(lambda _text: []))


def test_a_saved_session_is_continued_under_its_own_id(tmp_path):
    (tmp_path / "abc12345.json").write_text("{}", encoding="utf-8")
    requests: list[dict] = []

    async def scenario(service, _supervisor):
        first = await service.ask("and now?", session_id="abc12345")
        return first, await service.ask("and then?", session_id="abc12345")

    result, later = _run(scenario, _scripted_worker(lambda _text: [("message", {"text": "ok"})], requests=requests))
    assert result.session_id == "abc12345"
    assert result.resumed is True, "the first result after a reopening has to say so"
    assert later.resumed is False
    assert requests == [{"resume": "abc12345", "session_id": "abc12345"}]
    assert history.session_details("abc12345")["tags"] == [], "continuing a session must not retag it"


def test_a_worker_that_cannot_start_is_reported():
    def broken(request: dict, inbox, outbox) -> int:
        channel = QueueChannel(inbox, outbox)
        channel.send(Envelope(type="error", payload={"error_type": "SystemExit", "message": "bad model"}))
        channel.send(Envelope(type="stopped", payload={"exit_code": 1}))
        return 1

    async def scenario(service, _supervisor):
        with pytest.raises(ServiceError, match="bad model"):
            await service.ask("hello")

    _run(scenario, broken)


def test_a_missing_api_key_is_reported_before_a_worker_starts():
    async def main():
        backend = EmbeddedBackend(
            SessionSupervisor(worker_target=lambda *_: 0), preflight=lambda: "Missing OPENROUTER_API_KEY."
        )
        service = NetzooService(backend)
        with pytest.raises(BackendError, match="OPENROUTER_API_KEY"):
            await service.ask("hello")

    asyncio.run(main())


# -- paths -----------------------------------------------------------------------


def _mapped() -> PathMapper:
    return PathMapper(container_root=PurePosixPath("/work"), host_root=PurePosixPath(HOST_ROOT))


def test_the_host_project_folder_is_rewritten_before_the_agent_sees_it():
    seen: list[str] = []

    async def scenario(service, _supervisor):
        await service.ask(f"Run PANDA on {HOST_ROOT}/data/toy/expression.tsv and {HOST_ROOT}/data/toy/motif.tsv.")

    _run(scenario, _scripted_worker(lambda _text: [], seen=seen), mapper=_mapped())
    assert seen == ["Run PANDA on /work/data/toy/expression.tsv and /work/data/toy/motif.tsv."]


@pytest.mark.parametrize(
    "text, expected",
    [
        (f"{HOST_ROOT}/data/e.tsv", "/work/data/e.tsv"),
        (f"look in {HOST_ROOT}", "look in /work"),
        (f"'{HOST_ROOT}'", "'/work'"),
        (f"{HOST_ROOT}_backup/data/e.tsv", f"{HOST_ROOT}_backup/data/e.tsv"),
        ("/Users/someone/else/e.tsv", "/Users/someone/else/e.tsv"),
        ("no paths here", "no paths here"),
    ],
)
def test_only_the_project_prefix_is_rewritten(text, expected):
    service = NetzooService(EmbeddedBackend(SessionSupervisor(worker_target=lambda *_: 0)), mapper=_mapped())
    assert service.to_container_text(text) == expected


def test_without_a_host_root_text_is_left_alone():
    service = NetzooService(
        EmbeddedBackend(SessionSupervisor(worker_target=lambda *_: 0)),
        mapper=PathMapper(container_root=PurePosixPath("/work"), host_root=None),
    )
    assert service.to_container_text(f"{HOST_ROOT}/data/e.tsv") == f"{HOST_ROOT}/data/e.tsv"
    assert service.to_host("outputs/x.tsv") == "/work/outputs/x.tsv"
