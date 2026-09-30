"""What a person attaches to a session, beside what the agent checkpoints.

The checkpoint (`session.py`) is the agent's resumable state and is rewritten
every turn. A session's name, notes and tags, the models it runs under and the
brief forms of its replies belong to the person and the window instead, so they
live in a small sidecar that the checkpoint never touches:
`.netzoo/session_meta/<id>.json`. None of it is ever shown to the agent.
It sits beside, not inside, the sessions directory, because everything in
that directory is read as a checkpoint.

One session is one experiment: it records the models it started with and
keeps them when resumed (while they are still allow-listed), and its default
outputs go to its own folder (`session_outputs`).
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import unicodedata
from pathlib import Path

from .memory import _write_json_atomic
from .settings import SESSION_ROOT

__all__ = [
    "MAX_NAME_CHARS",
    "MAX_NOTES_CHARS",
    "MAX_TAGS",
    "card_for",
    "delete_meta",
    "is_kept",
    "load_meta",
    "meta_root",
    "normalize_name",
    "normalize_notes",
    "normalize_tags",
    "remember_turn",
    "set_details",
    "set_tags",
    "tag_field",
]

MAX_TAGS = 12
MAX_TAG_CHARS = 48
MAX_NAME_CHARS = 80
MAX_NOTES_CHARS = 4000
MAX_CARDS = 40
_WORDS = re.compile(r"^[\w][\w .+/-]*$")


def meta_root(sessions_root: Path | None = None) -> Path:
    """Beside the given sessions directory; callers pass the store they write to."""
    return Path(sessions_root or SESSION_ROOT).parent / "session_meta"


def _safe_id(session_id: str) -> str:
    # The same rule as session._safe_session_id, kept here so this module does
    # not import the checkpoint store that imports it.
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", session_id).strip(".-")
    if not cleaned:
        raise ValueError("session id must contain a letter or number")
    return cleaned[:80]


def _path(session_id: str, sessions_root: Path | None = None) -> Path:
    return meta_root(sessions_root) / f"{_safe_id(session_id)}.json"


def load_meta(session_id: str, *, sessions_root: Path | None = None) -> dict:
    try:
        payload = json.loads(_path(session_id, sessions_root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    payload.setdefault("version", 1)
    payload.setdefault("session_id", session_id)
    payload["name"] = normalize_name(payload.get("name"))
    payload["notes"] = normalize_notes(payload.get("notes"))
    payload["tags"] = normalize_tags(payload.get("tags") or [])
    payload.setdefault("models", {})
    payload.setdefault("cards", {})
    return payload


def _save(session_id: str, payload: dict, sessions_root: Path | None = None) -> None:
    path = _path(session_id, sessions_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass
    payload["updated_at"] = time.time()
    _write_json_atomic(path, payload)


def _tag(raw) -> str:
    """One tag in its stored form, or "" when it is not a valid tag.

    A plain tag is a label (`pilot`). A field tag is `key:value`
    (`dataset:batch-2`): its key is stored in lower case so the same field
    lines up across sessions, and its value keeps the case it was typed in.
    """
    text = " ".join(str(raw).split())
    if ":" not in text:
        tag = text[:MAX_TAG_CHARS].strip()
        return tag if _WORDS.match(tag) else ""
    key, _, value = (part.strip() for part in text.partition(":"))
    key = key.lower()
    value = value[:max(0, MAX_TAG_CHARS - len(key) - 1)].strip()
    return f"{key}:{value}" if _WORDS.match(key) and _WORDS.match(value) else ""


def tag_field(tag: str) -> tuple[str, str] | None:
    """`(key, value)` of a field tag; None for a plain one."""
    key, colon, value = tag.partition(":")
    return (key, value) if colon else None


def normalize_tags(tags) -> list[str]:
    """Trimmed, de-duplicated (case-insensitively), bounded tags; invalid ones dropped.

    A field holds one value per session: a later `dataset:batch-3` replaces
    an earlier `dataset:batch-2` where it stood.
    """
    kept: list[str] = []
    for raw in tags if isinstance(tags, (list, tuple)) else []:
        tag = _tag(raw)
        if not tag or tag.casefold() in {item.casefold() for item in kept}:
            continue
        field = tag_field(tag)
        same = next((index for index, item in enumerate(kept)
                     if field and (tag_field(item) or ("", ""))[0] == field[0]), None)
        if same is not None:
            kept[same] = tag
            continue
        if len(kept) == MAX_TAGS:
            continue
        kept.append(tag)
    return kept


def set_tags(session_id: str, tags, *, sessions_root: Path | None = None) -> list[str]:
    payload = load_meta(session_id, sessions_root=sessions_root)
    payload["tags"] = normalize_tags(tags)
    _save(session_id, payload, sessions_root)
    return payload["tags"]


def normalize_name(value) -> str:
    """One line, as a person names an experiment; "" clears it."""
    return " ".join(str(value or "").split())[:MAX_NAME_CHARS].strip()


def normalize_notes(value) -> str:
    """Free text with its line breaks; control characters and trailing blanks removed."""
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(c for c in text if c in "\n\t" or not unicodedata.category(c).startswith("C"))
    return "\n".join(line.rstrip() for line in text.split("\n")).strip()[:MAX_NOTES_CHARS].rstrip()


def set_details(session_id: str, *, name=None, notes=None,
                sessions_root: Path | None = None) -> dict:
    """Replace the name, the notes, or both; a field left as None is kept."""
    payload = load_meta(session_id, sessions_root=sessions_root)
    if name is not None:
        payload["name"] = normalize_name(name)
    if notes is not None:
        payload["notes"] = normalize_notes(notes)
    _save(session_id, payload, sessions_root)
    return {"name": payload["name"], "notes": payload["notes"]}


def is_kept(meta: dict) -> bool:
    """A session someone named, annotated or tagged is an experiment meant to be kept."""
    return bool(meta.get("tags") or meta.get("name") or meta.get("notes"))


def _content_key(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:24]


def remember_turn(session_id: str, *, models: dict | None = None, content: str | None = None,
                  card: dict | None = None, output_dir: str | None = None, tokens: int = 0,
                  sessions_root: Path | None = None) -> None:
    """Record what a finished turn adds; nothing is written when it adds nothing.

    Models are recorded once, when the session first runs, so a later resume
    under a different default cannot silently rewrite which model produced it.
    """
    models = {key: value for key, value in (models or {}).items() if value}
    if not models and not card and not output_dir and not tokens:
        return
    payload = load_meta(session_id, sessions_root=sessions_root)
    if tokens > 0:
        # A session's whole cost; the checkpoint only keeps its latest run's.
        payload["tokens_total"] = int(payload.get("tokens_total") or 0) + int(tokens)
    if models and not payload["models"]:
        payload["models"] = models
        payload.setdefault("created_at", time.time())
    elif models and payload["models"] != models:
        payload["resumed_with_models"] = models
    if output_dir:
        payload["output_dir"] = output_dir
    if card and content:
        cards = dict(payload["cards"])
        cards[_content_key(content)] = card
        payload["cards"] = dict(list(cards.items())[-MAX_CARDS:])
    _save(session_id, payload, sessions_root)


def card_for(meta: dict, content: str) -> dict | None:
    """The brief form recorded for one assistant message, if any."""
    return (meta.get("cards") or {}).get(_content_key(content))


def delete_meta(session_id: str, *, sessions_root: Path | None = None) -> bool:
    try:
        _path(session_id, sessions_root).unlink()
        return True
    except OSError:
        return False
