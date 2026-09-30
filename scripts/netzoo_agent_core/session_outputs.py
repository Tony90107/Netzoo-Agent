"""Where a session's outputs go when the request names no output path.

Without this every session wrote its defaults into ``outputs/demo`` under the
same file names, so a later run silently replaced an earlier session's
results: four recorded LIONESS-PUMA sessions all ended with the same
``outputs/demo/puma-aggregate.tsv``. A session now owns
``outputs/sessions/<session id>/``.

The value is scoped to one graph turn by the conversation machine, through a
context variable rather than a process-wide setting, so a planner called
outside a session (every test, every evaluation harness) keeps the historical
default. An explicit output path in the request and a confirmed profile
preference both still win.
"""

from __future__ import annotations

import contextvars
import re
from contextlib import contextmanager

__all__ = ["SESSION_OUTPUT_ROOT", "session_output_dir", "session_output_scope", "session_output_path"]

SESSION_OUTPUT_ROOT = "outputs/sessions"
_CURRENT: contextvars.ContextVar[str | None] = contextvars.ContextVar("netzoo_session_output_dir", default=None)


def session_output_path(session_id: str) -> str | None:
    """`outputs/sessions/<id>` for a plain session id, or None for anything else."""
    if not session_id or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", session_id) or session_id.strip(".") == "":
        return None
    return f"{SESSION_OUTPUT_ROOT}/{session_id}"


def session_output_dir() -> str | None:
    return _CURRENT.get()


@contextmanager
def session_output_scope(session_id: str | None):
    token = _CURRENT.set(session_output_path(session_id or ""))
    try:
        yield
    finally:
        _CURRENT.reset(token)
