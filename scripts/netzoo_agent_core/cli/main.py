"""Small command-line entrypoint."""

from __future__ import annotations

from .arguments import parse_args
from .loop import run_cli

__all__ = ["main"]


def main() -> int:
    return run_cli(parse_args())
