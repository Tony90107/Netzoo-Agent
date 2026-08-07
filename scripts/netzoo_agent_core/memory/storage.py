"""Private local-memory filesystem primitives."""

from __future__ import annotations

import fcntl
import json
import os
import re
import uuid
from contextlib import contextmanager
from pathlib import Path

__all__: list[str] = []


def _safe_memory_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip(".-")
    if not cleaned:
        raise ValueError("Memory id must contain a letter or number.")
    return cleaned[:80]


def _safe_json_text(value: str) -> str:
    """Replace invalid Unicode surrogates before writing UTF-8 JSON files."""
    return value.encode("utf-8", errors="replace").decode("utf-8")


def _sanitize_json_payload(value):
    if isinstance(value, str):
        return _safe_json_text(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, dict):
        return {
            _safe_json_text(str(key)): _sanitize_json_payload(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_sanitize_json_payload(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_json_payload(item) for item in value]
    return value


def _ensure_private_directory(path: Path) -> None:
    """Create a local state directory and make it owner-only."""
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)


def _harden_private_tree(root: Path) -> None:
    """Repair permissions on existing local state without following symlinks."""
    if not root.exists() or root.is_symlink():
        return
    root.chmod(0o700)
    for path in root.rglob("*"):
        if path.is_symlink():
            continue
        path.chmod(0o700 if path.is_dir() else 0o600)


@contextmanager
def _exclusive_file_lock(path: Path):
    """Serialize local load-modify-write sequences across processes."""
    _ensure_private_directory(path.parent)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    os.chmod(path, 0o600)
    with os.fdopen(descriptor, "a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _write_private_text(path: Path, text: str) -> None:
    """Write a new owner-only UTF-8 text file."""
    _ensure_private_directory(path.parent)
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", errors="replace") as handle:
        handle.write(_safe_json_text(text))
        handle.flush()
        os.fsync(handle.fileno())


def _write_json_atomic(path: Path, payload: dict) -> None:
    """Atomically replace JSON using collision-free, owner-only files."""
    _ensure_private_directory(path.parent)
    temporary = path.parent / f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    serialized = json.dumps(
        _sanitize_json_payload(payload),
        ensure_ascii=False,
        indent=2,
    )
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", errors="replace") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
        path.chmod(0o600)
    finally:
        temporary.unlink(missing_ok=True)
