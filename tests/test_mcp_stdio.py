"""Over stdio, the client must read JSON-RPC and nothing else.

This starts the real entry point as a child process and speaks the protocol to
it by hand, so every line the server writes to stdout is seen as it is, before
any client library has a chance to skip one it cannot parse.
"""

from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
from pathlib import Path

import pytest

pytest.importorskip("mcp")

SERVER = Path(__file__).with_name("mcp_stdio_server.py")
TIMEOUT = 30.0


class _Server:
    def __init__(self, session_root: Path):
        self.process = subprocess.Popen(
            [sys.executable, str(SERVER)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**__import__("os").environ, "NETZOO_TEST_SESSION_ROOT": str(session_root)},
        )
        self.lines: list[str] = []
        self._queue: queue.Queue = queue.Queue()
        self._stderr: list[str] = []
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def _read_stdout(self) -> None:
        for line in self.process.stdout:
            self.lines.append(line)
            self._queue.put(line)
        self._queue.put(None)

    def _read_stderr(self) -> None:
        for line in self.process.stderr:
            self._stderr.append(line)

    def send(self, payload: dict) -> None:
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()

    def response(self, request_id: int) -> dict:
        """The response to one request; anything unparsable on the way fails the test."""
        while True:
            line = self._queue.get(timeout=TIMEOUT)
            assert line is not None, f"server closed stdout before answering {request_id}: {self.stderr}"
            message = json.loads(line)
            if message.get("id") == request_id:
                return message

    def close(self) -> int:
        self.process.stdin.close()
        return self.process.wait(timeout=TIMEOUT)

    @property
    def stderr(self) -> str:
        return "".join(self._stderr)


def test_stdout_carries_only_the_protocol_whatever_else_prints(tmp_path):
    server = _Server(tmp_path)
    try:
        server.send(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "0"},
                },
            }
        )
        initialized = server.response(1)
        assert initialized["result"]["serverInfo"]["name"] == "netzoo"
        assert "Pass on what the user said" in initialized["result"]["instructions"]

        server.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        server.send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = [tool["name"] for tool in server.response(2)["result"]["tools"]]
        assert "netzoo_ask" in names and "netzoo_execute" not in names

        server.send(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "netzoo_ask", "arguments": {"message": "hello"}},
            }
        )
        called = server.response(3)["result"]
        assert called["_meta"]["netzoo/turn"]["reply"] == "heard: hello"
        assert called["_meta"]["netzoo/turn"]["status"] == "waiting_for_user"
        assert "heard: hello" in called["content"][0]["text"]
        assert "structuredContent" not in called

        assert server.close() == 0, server.stderr
    finally:
        if server.process.poll() is None:
            server.process.kill()

    assert server.lines, "the server wrote nothing"
    for line in server.lines:
        assert json.loads(line)["jsonrpc"] == "2.0", f"not protocol: {line!r}"
    for noise in (
        "NOISE print while the service is built",
        "NOISE worker print",
        "NOISE worker descriptor write",
        "NOISE child process print",
        "NOISE worker print during a turn",
    ):
        assert noise in server.stderr, f"{noise!r} was lost instead of going to stderr"
