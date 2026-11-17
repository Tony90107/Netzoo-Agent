"""A short title for a session, the way a chat sidebar names a conversation by what it is for.

The sidebar used to show the person's first request verbatim, cut at 160 characters, which reads as
a wall of file paths. After a session's first request is recorded, one small call to the router model
condenses that request into a few words. It is a label, not a fact the agent acts on:

* It is written from the person's request only, never from the agent's reply, and the prompt forbids
  naming a method, data type or file the request does not state.
* A name the person gives the session always wins (`name`), and the full request stays visible under it.
* Any failure (no key, timeout, an empty or overlong answer) leaves no title, and the sidebar keeps
  showing the request as before. It is tried once per session per process; a title lost to a
  concurrent write is simply tried again on the next turn.
"""

from __future__ import annotations

import os
import re
import threading
from pathlib import Path

__all__ = ["MAX_TITLE_CHARS", "clean_title", "ensure_auto_title", "start_auto_title"]

MAX_TITLE_CHARS = 60
_TIMEOUT_SECONDS = 15.0
_MAX_ATTEMPTS = 3
_attempts: dict[str, int] = {}
_done: set[str] = set()
_attempted_lock = threading.Lock()

_PROMPT = (
    "You name chat sessions for a sidebar. Read the user's request to a gene-regulatory-network analysis "
    "assistant and reply with a title of 3 to 7 words, in English, in sentence case, that says what the "
    "user wants to do. Use only what the request states: do not add a method, data type, organism, file "
    "or setting the request does not name. No quotes, no trailing period, no explanation."
)


def clean_title(raw: str) -> str:
    """The model's answer as a sidebar label, or "" when it is not usable as one."""
    text = str(raw or "").strip().splitlines()[0].strip() if str(raw or "").strip() else ""
    text = re.sub(r"^(?:title\s*:\s*)", "", text, flags=re.IGNORECASE)
    text = text.strip(" \t\"'`“”‘’*#").rstrip(".").strip()
    if not text or len(text) > MAX_TITLE_CHARS or len(text.split()) > 10:
        return ""
    return text


def _ask_model(request: str, model: str) -> tuple[str, int]:
    from .llm import build_llm, validate_router_model

    llm = build_llm(validate_router_model(model), 0.0, max_output_tokens=24, timeout_seconds=_TIMEOUT_SECONDS)
    message = llm.invoke([("system", _PROMPT), ("user", request[:2000])])
    usage = (getattr(message, "usage_metadata", None) or {}).get("total_tokens") or 0
    return str(getattr(message, "content", "") or ""), int(usage)


def ensure_auto_title(session_id: str, model: str, *, sessions_root: Path | None = None, ask=_ask_model) -> str:
    """Write `auto_title` once the first request is known; returns the session's title, or "" when it has none."""
    from .session_meta import load_meta, set_auto_title

    meta = load_meta(session_id, sessions_root=sessions_root)
    if meta.get("auto_title"):
        return str(meta["auto_title"])
    request = str(meta.get("first_request") or "").strip()
    if not request or not model:
        return ""
    try:
        raw, tokens = ask(request, model)
    except Exception:  # noqa: BLE001 - a missing title must never break a turn
        return ""
    title = clean_title(raw)
    if not title:
        return ""
    set_auto_title(session_id, title, tokens=tokens, sessions_root=sessions_root)
    return title


def start_auto_title(session_id: str, models: dict | str, sessions_root: Path | None = None) -> None:
    """Name the session in the background with its router model, so the reply is never held up by it."""
    model = models if isinstance(models, str) else str((models or {}).get("router") or "")
    if not session_id or not model or os.environ.get("NETZOO_AUTO_TITLE", "on").strip().lower() == "off":
        return
    with _attempted_lock:
        # One call in flight per session, and a bounded number of tries for one with no key or no network.
        if session_id in _done or _attempts.get(session_id, 0) >= _MAX_ATTEMPTS:
            return
        _done.add(session_id)
        _attempts[session_id] = _attempts.get(session_id, 0) + 1

    def run() -> None:
        title = ""
        try:
            title = ensure_auto_title(session_id, model, sessions_root=sessions_root)
        except Exception:  # noqa: BLE001
            title = ""
        if not title:
            # No request yet, or the call failed: a later turn may try again.
            with _attempted_lock:
                _done.discard(session_id)

    threading.Thread(target=run, name=f"netzoo-title-{session_id[:8]}", daemon=True).start()
