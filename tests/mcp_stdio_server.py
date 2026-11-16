"""A server process for ``test_mcp_stdio``: the real stdio entry point over a noisy worker.

Everything that could put a stray byte on stdout does so here: a ``print``
while the service is built, a ``print`` from the worker, a raw write to file
descriptor 1, and a child process that inherits it. The test then checks that
the client's end of the pipe saw JSON-RPC and nothing else.
"""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
from pathlib import Path, PurePosixPath

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.mcp_server.__main__ import run  # noqa: E402


def _noisy_worker(request: dict, inbox, outbox) -> int:
    from netzoo_agent_core.server.channel import QueueChannel
    from netzoo_agent_core.server.protocol import Envelope

    channel = QueueChannel(inbox, outbox)
    session_id = request["session_id"]

    def send(kind: str, payload: dict | None = None) -> None:
        channel.send(Envelope(type=kind, session_id=session_id, payload=payload or {}))

    def view() -> None:
        send("view", {"prompt_kind": "main", "text": "What next?", "mode": "Planning", "menu_enabled": True,
                      "plan": None, "plan_hash": None, "next_prompt": {"kind": "initial", "question": "What next?"}})

    print("NOISE worker print")
    os.write(1, b"NOISE worker descriptor write\n")
    subprocess.run([sys.executable, "-c", "print('NOISE child process print')"], check=True)
    send("ready", {"session_id": session_id})
    view()
    while True:
        envelope = channel.receive()
        if envelope is None:
            continue
        if envelope.type == "cancel":
            send("stopped", {"exit_code": 0})
            return 0
        print("NOISE worker print during a turn")
        send("message", {"text": f"heard: {envelope.payload.get('text', '')}"})
        view()


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


def _make_service():
    from netzoo_agent_core.mcp_server.backend import EmbeddedBackend
    from netzoo_agent_core.mcp_server.service import NetzooService
    from netzoo_agent_core.server import history
    from netzoo_agent_core.server.path_mapper import PathMapper
    from netzoo_agent_core.server.supervisor import SessionSupervisor

    print("NOISE print while the service is built")
    history.SESSION_ROOT = Path(os.environ["NETZOO_TEST_SESSION_ROOT"])
    supervisor = SessionSupervisor(
        worker_target=_noisy_worker,
        process_factory=lambda t, a: _ThreadWorker(t, a),
        queue_factory=queue.Queue,
    )
    return NetzooService(
        EmbeddedBackend(supervisor, preflight=lambda: None),
        mapper=PathMapper(container_root=PurePosixPath("/work"), host_root=None),
    )


if __name__ == "__main__":
    raise SystemExit(run(_make_service))
