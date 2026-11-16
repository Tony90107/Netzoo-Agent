"""Keep the turns context compaction drops in the session's transcript.

`session.compact_conversation` bounds the checkpoint to the newest turns: the
agent's working context. The agent never read old turns as text (routing reads
the latest message; the open task lives in TaskState), so nothing it works from
changes here. What changes is the transcript a person reads back: it stays
whole, the way Claude keeps the full transcript while compacting what the model
works from, and the person is told once that compaction has started.
"""

from __future__ import annotations

from .view import Event

__all__ = ["archive_compacted", "compact_and_archive"]


def compact_and_archive(runtime, session_id: str, messages: list) -> tuple[list, list[Event]]:
    """The compacted conversation, and the notice to show when this started compaction."""
    from ..session import compact_conversation

    kept = compact_conversation(messages)
    return kept, archive_compacted(runtime, session_id, messages, kept)


def archive_compacted(runtime, session_id: str, messages: list, kept: list) -> list[Event]:
    dropped = list(messages[: max(len(messages) - len(kept), 0)])
    # Only a runtime built by bootstrap_runtime keeps a sidecar (as _remember_turn).
    if not dropped or not getattr(runtime, "session_models", None):
        return []
    try:
        from .. import session as session_store
        from ..session_meta import archive_messages, read_archive

        first = not read_archive(session_id, sessions_root=session_store.SESSION_ROOT)["messages"]
        archive_messages(
            session_id,
            [{"role": "assistant" if getattr(message, "type", "") == "ai" else "user",
              "content": str(getattr(message, "content", ""))} for message in dropped],
            sessions_root=session_store.SESSION_ROOT,
        )
    except Exception:  # noqa: BLE001 - bookkeeping must not break a turn
        return []
    if not first:
        return []
    return [Event(
        "notice",
        "This conversation is long, so the agent now works from the open task and the latest "
        f"{len(kept)} messages. Earlier turns are kept in this session's transcript: open the "
        "session from the session list to read all of it.",
    )]
