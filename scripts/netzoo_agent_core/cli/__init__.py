"""Command-line parsing and interactive NetZoo application."""

from . import (
    arguments,
    bootstrap,
    clarification,
    commands,
    conversation,
    follow_up,
    loop,
    trace_commands,
)
from ..graph import build_graph
from .arguments import parse_args
from .main import main
from .trace_commands import export_local_trace, local_trace_status

_CLI_IMPLEMENTATION_MODULES = (
    arguments,
    bootstrap,
    clarification,
    commands,
    conversation,
    follow_up,
    loop,
    trace_commands,
)

__all__ = [
    "parse_args",
    "main",
    "export_local_trace",
    "local_trace_status",
]
