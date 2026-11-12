"""Tags on output files: the ones NetZoo sets from a run's record, and the ones a person adds.

The two never collide by construction:

* Auto tags use reserved field keys (`method:`, `result:`, `scale:`, `mode:`). They are written when a run writes
  the file, replaced when a later run writes it again, and never edited by hand, so they always describe the run
  that produced what is on disk.
* User tags are any label (`baseline`) or field (`dataset:pasilla`) except those keys. A user tag cannot reuse a
  reserved key, so it can never contradict or impersonate a recorded fact, and one equal to an auto tag is
  dropped as already there. User tags survive a rewrite of the file: they are the person's, not the run's.

Both live in one project file keyed by the output's project-relative path (`outputs/...`).
"""

from __future__ import annotations

import fcntl
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path

from .session_meta import MAX_TAGS, normalize_tags, tag_field
from .settings import PROJECT_ROOT


__all__ = ["RESERVED_KEYS", "ReservedTag", "record_auto_tags", "set_user_tags", "store_path", "tags_for"]

RESERVED_KEYS = ("method", "result", "scale", "mode")
_MAX_FILES = 20_000


class ReservedTag(ValueError):
    """A user tag used a key NetZoo sets from the run record."""


def store_path() -> Path:
    override = os.environ.get("NETZOO_OUTPUT_TAGS_PATH")
    return Path(override) if override else PROJECT_ROOT / ".netzoo" / "output_tags.json"


def relative_output(path: str) -> str:
    """The project-relative spelling (`outputs/...`) every caller agrees on; "" for a path outside outputs/."""
    text = str(path).strip()
    for prefix in (str(PROJECT_ROOT) + "/", "/work/"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    text = text.lstrip("./")
    parts = text.split("/")
    return text if parts[0] == "outputs" and len(parts) > 1 and ".." not in parts else ""


@contextmanager
def _locked():
    path = store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path.with_suffix(".lock"), "a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield path
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    files = data.get("files") if isinstance(data, dict) else None
    return files if isinstance(files, dict) else {}


def _save(path: Path, files: dict) -> None:
    if len(files) > _MAX_FILES:  # oldest auto records go first; a person's own tags are kept
        ranked = sorted(files, key=lambda key: (bool(files[key].get("user")), files[key].get("recorded_at", 0)))
        for key in ranked[: len(files) - _MAX_FILES]:
            files.pop(key)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"version": 1, "files": files}, indent=1, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


def _reserved(tag: str) -> bool:
    field = tag_field(tag)
    return bool(field and field[0] in RESERVED_KEYS)


def record_auto_tags(files: list[dict], *, session_id: str = "", run_id: str = "") -> int:
    """Replace the auto tags of each written file that exists; returns how many were recorded."""
    found = []
    for item in files:
        relative = relative_output(item.get("path", ""))
        if not relative or not item.get("written") or not (PROJECT_ROOT / relative).is_file():
            continue
        tags = [tag for tag in normalize_tags(item.get("tags") or []) if _reserved(tag)]
        if tags:
            found.append((relative, tags))
    if not found:
        return 0
    with _locked() as path:
        stored = _load(path)
        for relative, tags in found:
            entry = stored.get(relative) or {}
            entry.update({"auto": tags, "session_id": session_id, "run_id": run_id, "recorded_at": time.time()})
            entry["user"] = [tag for tag in entry.get("user") or [] if tag.casefold() not in {t.casefold() for t in tags}]
            stored[relative] = entry
        _save(path, stored)
    return len(found)


def set_user_tags(path: str, tags) -> dict:
    """Replace a file's user tags. A reserved key is refused with the reason; one equal to an auto tag is dropped."""
    relative = relative_output(path)
    if not relative:
        raise ValueError("tags can only be set on a file under outputs/")
    if not (PROJECT_ROOT / relative).is_file():
        raise FileNotFoundError(relative)
    wanted = normalize_tags(tags)
    refused = [tag for tag in wanted if _reserved(tag)]
    if refused:
        keys = ", ".join(sorted({tag_field(tag)[0] + ":" for tag in refused}))
        raise ReservedTag(
            f"{keys} is set by NetZoo from the run record and cannot be typed. "
            "Use another name, for example note: or dataset:.")
    with _locked() as store:
        stored = _load(store)
        entry = stored.get(relative) or {"auto": []}
        auto = {tag.casefold() for tag in entry.get("auto") or []}
        entry["user"] = [tag for tag in wanted if tag.casefold() not in auto][:MAX_TAGS]
        entry["user_updated_at"] = time.time()
        stored[relative] = entry
        _save(store, stored)
    return {"path": relative, "auto": list(entry.get("auto") or []), "user": entry["user"]}


def tags_for(paths: list[str]) -> dict[str, dict]:
    """`{path: {"auto": [...], "user": [...]}}` for the paths that have any."""
    stored = _load(store_path())
    found = {}
    for path in paths:
        relative = relative_output(path)
        entry = stored.get(relative) if relative else None
        if entry and (entry.get("auto") or entry.get("user")):
            found[path] = {"auto": list(entry.get("auto") or []), "user": list(entry.get("user") or [])}
    return found
