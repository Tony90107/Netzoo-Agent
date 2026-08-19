"""Contained workspace-subpath extraction for read-only resource discovery."""

from __future__ import annotations

import re
from pathlib import Path

from ..settings import PROJECT_ROOT


_FILESYSTEM_SUFFIXES = frozenset({".tsv", ".tab", ".txt", ".csv", ".npy"})


def _is_filesystem_token(value: str) -> bool:
    token = value.casefold()
    return bool(
        "/" in token
        or "\\" in token
        or token.startswith((".", "~"))
        or any(token.endswith(suffix) for suffix in _FILESYSTEM_SUFFIXES)
    )


def extract_workspace_subpath(
    task: str,
    workspace_root: Path = PROJECT_ROOT,
) -> str | None:
    """Extract one explicit filesystem token only when it stays in workspace."""
    root = workspace_root.expanduser().resolve()
    candidates = re.findall(r"['\"]([^'\"]+)['\"]|([^\s，,。；;]+)", task)
    for quoted, plain in candidates:
        token = (quoted or plain).strip().rstrip(".。:：")
        if not token or "://" in token or not _is_filesystem_token(token):
            continue
        path = Path(token).expanduser()
        candidate = path.resolve() if path.is_absolute() else (root / path).resolve()
        if not candidate.is_relative_to(root):
            continue
        if candidate.is_file():
            candidate = candidate.parent
        rendered = candidate.relative_to(root).as_posix()
        return rendered or "."
    return None


__all__ = ["extract_workspace_subpath"]
