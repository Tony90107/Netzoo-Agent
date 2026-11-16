"""Run NetZoo as a local MCP server: ``python -m netzoo_agent_core.mcp_server``.

It speaks MCP over stdio, which is how a desktop client starts a local server:
the client launches this process and owns both ends of the pipe, so there is
no port to protect and no token to pass. A network transport is not offered,
because it would need its own authentication before it could be allowed to
start analyses.
"""

from __future__ import annotations

import argparse
import os
from io import TextIOWrapper

from .stdio_guard import protect_stdout

_ON = frozenset({"1", "on", "true", "yes"})


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().casefold() in _ON


def _seconds(name: str, default: float) -> float:
    try:
        return max(float(os.environ.get(name, "") or default), 1.0)
    except ValueError:
        return default


async def _serve(server, protocol_fd: int) -> None:
    import anyio
    from mcp.server.stdio import stdio_server

    stdout = anyio.wrap_file(TextIOWrapper(os.fdopen(protocol_fd, "wb"), encoding="utf-8"))
    async with stdio_server(stdout=stdout) as (read_stream, write_stream):
        lowlevel = server._mcp_server  # the server FastMCP.run_stdio_async drives
        await lowlevel.run(read_stream, write_stream, lowlevel.create_initialization_options())


def run(make_service) -> int:
    """Serve the service ``make_service()`` returns over this process's stdio."""
    # First, before anything is imported or built that could print.
    protocol_fd = protect_stdout()

    import anyio

    from .tools import build_server

    anyio.run(_serve, build_server(make_service()), protocol_fd)
    return 0


def _default_service():
    from .backend import EmbeddedBackend
    from .service import NetzooService

    return NetzooService(
        EmbeddedBackend(),
        execute_enabled=_flag("NETZOO_MCP_EXECUTE"),
        wait_seconds=_seconds("NETZOO_MCP_WAIT_SECONDS", 45.0),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NetZoo agent as a local MCP server.")
    parser.add_argument("--transport", choices=["stdio"], default="stdio")
    parser.parse_args(argv)
    return run(_default_service)


if __name__ == "__main__":
    raise SystemExit(main())
