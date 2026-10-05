"""The bounded text every model call and router reads for one request.

A request longer than the router budget used to keep only its last 6,000
characters, so an opening instruction ("Do not execute anything", "Run PANDA
with expression_file=...") vanished from routing while the planner and plan
evaluator read the full message (diagnostics F3). The window keeps the opening
and the closing of the request and says, in the text, how much was left out.
Deterministic readers that need the whole request read the full message
through `RequestRequirements`, never this window.
"""

from __future__ import annotations

from .settings import ROUTER_CONTEXT_MAX_CHARS

__all__ = ["HEAD_CHARS", "omission_marker", "routing_window", "routing_window_parts"]

#: Characters kept from the start of an over-long request; the rest of the
#: budget goes to its end, where the question usually is.
HEAD_CHARS = 2_000


def omission_marker(omitted: int) -> str:
    return f"\n[... {omitted} characters of this request omitted ...]\n"


def routing_window_parts(text: str, limit: int = ROUTER_CONTEXT_MAX_CHARS) -> tuple[str, int]:
    """Return the routing window of *text* and how many characters it left out."""
    if len(text) <= limit:
        return text, 0
    head = text[:HEAD_CHARS]
    # The marker's own length depends on the count it reports; size the tail
    # against the widest count so the window never exceeds the limit.
    tail_chars = limit - HEAD_CHARS - len(omission_marker(len(text)))
    omitted = len(text) - HEAD_CHARS - tail_chars
    return head + omission_marker(omitted) + text[len(text) - tail_chars:], omitted


def routing_window(text: str, limit: int = ROUTER_CONTEXT_MAX_CHARS) -> str:
    """Return *text* unchanged when it fits, else its head and tail with a marker."""
    return routing_window_parts(text, limit)[0]
