"""Run the daemon: ``python -m netzoo_agent_core.server``."""

from __future__ import annotations

import argparse
import sys

from .app import create_app, resolve_token
from .session_worker import worker_environment_error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Local NetZoo agent daemon for the desktop UI."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    arguments = parser.parse_args(argv)

    if (problem := worker_environment_error()) is not None:
        print(problem, file=sys.stderr)
        return 2

    token, generated = resolve_token()
    if generated:
        # The desktop shell normally supplies the token. Printing the
        # generated one keeps `websocat` and manual testing possible without
        # weakening the default.
        print(f"NETZOO_DESKTOP_TOKEN={token}", flush=True)

    import uvicorn

    uvicorn.run(
        create_app(token=token),
        host=arguments.host,
        port=arguments.port,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
