"""Supervisor, HTTP surface, and the isolation the process model exists for.

The interesting test here is the last one.  Fourteen names in
``runtime.MUTABLE_RUNTIME_NAMES`` are process-wide, ``EXECUTE_TOOLS`` and
``TEST_DATA_MODE`` among them.  One process per session is the whole reason
approving execution in one window cannot hand execution authority to another,
so that claim is tested with real processes rather than assumed.
"""

from __future__ import annotations

import asyncio
import queue
import sys
import threading
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.server.app import create_app  # noqa: E402
from netzoo_agent_core.server.channel import QueueChannel  # noqa: E402
from netzoo_agent_core.server.protocol import Envelope  # noqa: E402
from netzoo_agent_core.server.supervisor import SessionSupervisor  # noqa: E402

TOKEN = "test-token"
DESKTOP_ORIGIN_FOR_TEST = "tauri://localhost"
TIMEOUT = 15.0


# ---------------------------------------------------------------------------
# Worker targets.  Module level so ``multiprocessing`` with the spawn start
# method can import them in the child.
# ---------------------------------------------------------------------------


def echo_worker(request: dict, inbox, outbox) -> int:
    """A worker that speaks the protocol but runs no agent."""
    channel = QueueChannel(inbox, outbox)
    session_id = str(request.get("session_id", ""))
    channel.send(Envelope(type="ready", session_id=session_id))
    while True:
        envelope = channel.receive()
        if envelope is None:
            continue
        if envelope.type == "cancel":
            channel.send(
                Envelope(
                    type="stopped", session_id=session_id, payload={"exit_code": 0}
                )
            )
            return 0
        channel.send(
            Envelope(
                type="notice",
                session_id=session_id,
                payload={"text": f"echo:{envelope.payload.get('text', '')}"},
            )
        )


def runtime_probe_worker(request: dict, inbox, outbox) -> int:
    """Report and mutate this process's copy of the global runtime flags."""
    from netzoo_agent_core import settings
    from netzoo_agent_core.runtime import configure_runtime

    channel = QueueChannel(inbox, outbox)
    session_id = str(request.get("session_id", ""))

    def report(kind: str) -> None:
        channel.send(
            Envelope(
                type=kind,
                session_id=session_id,
                payload={
                    "execute_tools": settings.EXECUTE_TOOLS,
                    "test_data_mode": settings.TEST_DATA_MODE,
                },
            )
        )

    report("ready")
    while True:
        envelope = channel.receive()
        if envelope is None:
            continue
        if envelope.type == "cancel":
            channel.send(
                Envelope(
                    type="stopped", session_id=session_id, payload={"exit_code": 0}
                )
            )
            return 0
        command = envelope.payload.get("text", "")
        if command == "enable":
            configure_runtime(EXECUTE_TOOLS=True, TEST_DATA_MODE=True)
        report("notice")


# ---------------------------------------------------------------------------
# A thread-backed stand-in for a worker process, so the HTTP and fan-out tests
# stay fast and do not depend on the spawn start method.
# ---------------------------------------------------------------------------


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


def _threaded_supervisor(target=echo_worker) -> SessionSupervisor:
    return SessionSupervisor(
        worker_target=target,
        process_factory=lambda t, a: _ThreadWorker(t, a),
        queue_factory=queue.Queue,
    )


@pytest.fixture
def client():
    from starlette.testclient import TestClient

    app = create_app(token=TOKEN, supervisor=_threaded_supervisor())
    with TestClient(app) as test_client:
        yield test_client


def _auth() -> dict:
    return {"Authorization": f"Bearer {TOKEN}"}


def _open_session(client, session_id: str = "s1") -> str:
    response = client.post(
        "/v1/sessions", json={"session_id": session_id}, headers=_auth()
    )
    assert response.status_code == 201
    return response.json()["session_id"]


# ---------------------------------------------------------------------------
# HTTP surface
# ---------------------------------------------------------------------------


def test_health_needs_no_token_but_everything_else_does(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/v1/sessions").status_code == 401
    assert client.post("/v1/sessions", json={}).status_code == 401
    assert client.get("/v1/sessions", headers=_auth()).status_code == 200


def test_a_wrong_token_is_rejected(client):
    response = client.get("/v1/sessions", headers={"Authorization": "Bearer nope"})
    assert response.status_code == 401


def test_creating_the_same_session_twice_is_a_conflict(client):
    _open_session(client, "dup")
    assert client.post(
        "/v1/sessions", json={"session_id": "dup"}, headers=_auth()
    ).status_code == 409


def test_sessions_are_listed_and_can_be_closed(client):
    _open_session(client, "listed")
    listed = client.get("/v1/sessions", headers=_auth()).json()["sessions"]
    assert [entry["session_id"] for entry in listed] == ["listed"]
    assert client.delete("/v1/sessions/listed", headers=_auth()).status_code == 204
    assert client.get("/v1/sessions", headers=_auth()).json()["sessions"] == []


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------


def _receive(socket, *types: str) -> Envelope:
    while True:
        envelope = Envelope.from_json(socket.receive_text())
        if not types or envelope.type in types:
            return envelope


def test_a_websocket_round_trip_reaches_the_worker(client):
    _open_session(client, "ws")
    with client.websocket_connect("/ws/session/ws", headers=_auth()) as socket:
        assert _receive(socket, "ready").session_id == "ws"
        socket.send_text(
            Envelope(type="answer", payload={"text": "hello"}).to_json()
        )
        assert _receive(socket, "notice").payload["text"] == "echo:hello"


def test_the_daemon_numbers_events_so_a_client_can_resume(client):
    _open_session(client, "seq")
    with client.websocket_connect("/ws/session/seq", headers=_auth()) as socket:
        _receive(socket, "ready")
        for word in ("one", "two"):
            socket.send_text(
                Envelope(type="answer", payload={"text": word}).to_json()
            )
            _receive(socket, "notice")
    with client.websocket_connect("/ws/session/seq?since=2", headers=_auth()) as socket:
        replayed = Envelope.from_json(socket.receive_text())
        assert replayed.seq == 3
        assert replayed.payload["text"] == "echo:two"


def test_a_websocket_without_a_token_is_closed(client):
    _open_session(client, "noauth")
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/session/noauth") as socket:
            socket.receive_text()


def test_a_websocket_for_an_unknown_session_is_closed(client):
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/session/missing", headers=_auth()) as socket:
            socket.receive_text()


def test_a_malformed_client_message_is_reported_not_forwarded(client):
    _open_session(client, "bad")
    with client.websocket_connect("/ws/session/bad", headers=_auth()) as socket:
        _receive(socket, "ready")
        socket.send_text(Envelope(type="not_a_command").to_json())
        error = _receive(socket, "error")
        assert error.payload["error_type"] == "InvalidMessage"
        socket.send_text(Envelope(type="ping").to_json())
        assert _receive(socket, "pong").type == "pong"


# ---------------------------------------------------------------------------
# The reason for the process model
# ---------------------------------------------------------------------------


async def _two_real_sessions() -> tuple[dict, dict]:
    supervisor = SessionSupervisor(worker_target=runtime_probe_worker)
    await supervisor.start()
    try:
        await supervisor.create("alpha", {})
        await supervisor.create("beta", {})
        alpha, _ = supervisor.subscribe("alpha")
        beta, _ = supervisor.subscribe("beta")

        assert (await asyncio.wait_for(alpha.get(), TIMEOUT)).type == "ready"
        assert (await asyncio.wait_for(beta.get(), TIMEOUT)).type == "ready"

        supervisor.send("alpha", Envelope(type="answer", payload={"text": "enable"}))
        alpha_state = await asyncio.wait_for(alpha.get(), TIMEOUT)

        supervisor.send("beta", Envelope(type="answer", payload={"text": "report"}))
        beta_state = await asyncio.wait_for(beta.get(), TIMEOUT)
        return alpha_state.payload, beta_state.payload
    finally:
        await supervisor.shutdown()


def test_execution_authority_does_not_leak_between_sessions():
    alpha, beta = asyncio.run(_two_real_sessions())

    assert alpha["execute_tools"] is True
    assert alpha["test_data_mode"] is True
    # Same daemon, same moment, untouched.
    assert beta["execute_tools"] is False
    assert beta["test_data_mode"] is False


# ---------------------------------------------------------------------------
# Cross-origin access
# ---------------------------------------------------------------------------


def test_the_desktop_window_is_allowed_to_call_the_daemon(client):
    """A Tauri window is a browser, so its requests are cross-origin.

    Without this the shell can start the container over IPC and then be unable
    to talk to it, which looks to the user like the daemon never came up.
    """
    from netzoo_agent_core.server.app import DESKTOP_ORIGINS

    for origin in DESKTOP_ORIGINS:
        response = client.get("/health", headers={"Origin": origin})
        assert response.headers.get("access-control-allow-origin") == origin


def test_an_unknown_origin_gets_no_cors_grant(client):
    response = client.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers


def test_cors_never_allows_credentials(client):
    """Loopback plus a bearer token is the boundary; ambient credentials are not."""
    response = client.get("/health", headers={"Origin": DESKTOP_ORIGIN_FOR_TEST})
    assert "access-control-allow-credentials" not in response.headers


def test_a_browser_authenticates_over_the_subprotocol(client):
    """Browsers cannot set Authorization on a WebSocket."""
    from netzoo_agent_core.server.app import WS_TOKEN_SUBPROTOCOL

    _open_session(client, "subproto")
    with client.websocket_connect(
        "/ws/session/subproto",
        subprotocols=[WS_TOKEN_SUBPROTOCOL, TOKEN],
    ) as socket:
        assert _receive(socket, "ready").session_id == "subproto"


def test_a_token_in_the_query_string_no_longer_authenticates(client):
    """It used to, and uvicorn wrote it straight into the access log."""
    _open_session(client, "queryauth")
    with pytest.raises(Exception):
        with client.websocket_connect(
            f"/ws/session/queryauth?token={TOKEN}"
        ) as socket:
            socket.receive_text()


def test_a_wrong_token_in_the_subprotocol_is_rejected(client):
    from netzoo_agent_core.server.app import WS_TOKEN_SUBPROTOCOL

    _open_session(client, "badsub")
    with pytest.raises(Exception):
        with client.websocket_connect(
            "/ws/session/badsub", subprotocols=[WS_TOKEN_SUBPROTOCOL, "nope"]
        ) as socket:
            socket.receive_text()


# ---------------------------------------------------------------------------
# Browsing what a run produced
# ---------------------------------------------------------------------------


def test_the_outputs_tree_is_browsable(client):
    body = client.get("/v1/files", headers=_auth()).json()
    assert body["path"] == "outputs"
    assert all(entry["path"].startswith("outputs") for entry in body["entries"])


def test_browsing_needs_a_token(client):
    assert client.get("/v1/files").status_code == 401
    assert client.get("/v1/files/preview?path=outputs").status_code == 401


def test_a_path_outside_outputs_is_refused_over_http(client):
    for requested in ("../.env", "scripts/netzoo_agent.py", "/etc/passwd"):
        response = client.get(
            "/v1/files/preview", params={"path": requested}, headers=_auth()
        )
        assert response.status_code == 403, requested


def test_a_listing_reports_the_path_a_person_can_find(client, monkeypatch):
    """Without a host root the daemon must not invent one."""
    body = client.get("/v1/files", headers=_auth()).json()
    assert body["host_path"].endswith("outputs")
