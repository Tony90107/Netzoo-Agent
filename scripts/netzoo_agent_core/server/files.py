"""Reading what a run produced, without loading it.

PANDA's toy output is 3.1MB and a real one is far larger, so nothing here
reads a whole file to show the top of it: a table is streamed line by line and
an ``.npz`` is described from its header. A viewer that had to load the array
would be a viewer that cannot open the results it exists for.

Every path arriving from the window is project-relative and is resolved
against one allowed root. The window never names an absolute path, and a path
that resolves outside that root is refused rather than clamped.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ..settings import PROJECT_ROOT

__all__ = [
    "FILE_ROOT",
    "DirectoryListing",
    "Entry",
    "FilePreview",
    "OutsideRoot",
    "list_directory",
    "preview",
]

#: The one subtree the window may browse. Inputs are the agent's business.
FILE_ROOT = "outputs"

#: A table preview never returns more than this many rows.
MAX_ROWS = 200
#: A text preview never returns more than this many characters.
MAX_TEXT = 200_000

TABLE_SUFFIXES = {".tsv", ".csv", ".txt"}
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".log"}


class OutsideRoot(ValueError):
    """A request named something outside the browsable root."""


@dataclass(frozen=True, slots=True)
class Entry:
    name: str
    path: str
    """Project-relative, which is what both sides of the boundary agree on."""
    kind: Literal["directory", "file"]
    size_bytes: int
    modified_at: float


@dataclass(frozen=True, slots=True)
class DirectoryListing:
    path: str
    entries: list[Entry]


@dataclass(frozen=True, slots=True)
class FilePreview:
    path: str
    kind: Literal["table", "text", "arrays", "binary"]
    size_bytes: int
    truncated: bool
    columns: list[str]
    rows: list[list[str]]
    text: str
    arrays: list[dict]
    note: str


def _root() -> Path:
    return (PROJECT_ROOT / FILE_ROOT).resolve()


def _resolve(relative: str) -> Path:
    """Resolve a project-relative path, refusing anything outside the root.

    Project-relative is the one spelling both sides agree on: it is what a
    plan carries, what a listing returns, and what comes back in a request.
    """
    root = _root()
    cleaned = relative.strip().lstrip("/")
    candidate = (PROJECT_ROOT / (cleaned or FILE_ROOT)).resolve()
    # `resolve()` follows symlinks, so a link pointing out of the tree is
    # caught here rather than being trusted on the strength of its name.
    if candidate != root and not candidate.is_relative_to(root):
        raise OutsideRoot(f"{relative!r} is outside {FILE_ROOT}/")
    return candidate


def _relative(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def list_directory(relative: str = "") -> DirectoryListing:
    target = _resolve(relative)
    if not target.is_dir():
        raise OutsideRoot(f"{relative!r} is not a directory")
    entries: list[Entry] = []
    for child in sorted(
        target.iterdir(), key=lambda item: (item.is_file(), item.name.lower())
    ):
        if child.name.startswith("."):
            continue
        stat = child.stat()
        entries.append(
            Entry(
                name=child.name,
                path=_relative(child),
                kind="directory" if child.is_dir() else "file",
                size_bytes=stat.st_size if child.is_file() else 0,
                modified_at=stat.st_mtime,
            )
        )
    return DirectoryListing(path=_relative(target), entries=entries)


def _realigned_header(header: list[str], body: list[list[str]]) -> list[str]:
    """Re-split a header that used a different separator from its rows.

    Some NetZoo outputs write a space-separated header above tab-separated
    rows, which reads as one enormous column. Re-splitting is done only when
    it yields exactly the column count the data has, so a header that is
    legitimately one field is never mangled to make a table look tidier.
    """
    if len(header) != 1 or not body:
        return header
    width = len(body[0])
    if width < 2:
        return header
    candidate = header[0].split()
    return candidate if len(candidate) == width else header


def _table_preview(target: Path, size: int) -> FilePreview:
    delimiter = "," if target.suffix.lower() == ".csv" else "\t"
    rows: list[list[str]] = []
    truncated = False
    with target.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        for index, row in enumerate(reader):
            if index >= MAX_ROWS + 1:
                truncated = True
                break
            rows.append(row)
    header = rows[0] if rows else []
    body = rows[1:] if len(rows) > 1 else []
    header = _realigned_header(header, body)
    return FilePreview(
        path=_relative(target),
        kind="table",
        size_bytes=size,
        truncated=truncated,
        columns=header,
        rows=body,
        text="",
        arrays=[],
        note=f"first {len(body)} rows" if truncated else "",
    )


def _array_preview(target: Path, size: int) -> FilePreview:
    """Describe an ``.npz`` from its header; never materialise the arrays."""
    try:
        import numpy
    except ImportError:  # pragma: no cover - numpy ships in the image
        return FilePreview(
            path=_relative(target), kind="binary", size_bytes=size, truncated=False,
            columns=[], rows=[], text="", arrays=[],
            note="numpy is unavailable in this environment",
        )
    arrays: list[dict] = []
    with numpy.load(target, allow_pickle=False) as archive:
        for name in archive.files:
            # `zip.NpzFile` exposes each member's header without reading it.
            member = archive.zip.getinfo(f"{name}.npy")
            with archive.zip.open(member) as handle:
                version = numpy.lib.format.read_magic(handle)
                shape, fortran, dtype = numpy.lib.format._read_array_header(
                    handle, version
                )
            arrays.append(
                {
                    "name": name,
                    "shape": list(shape),
                    "dtype": str(dtype),
                    "fortran_order": bool(fortran),
                }
            )
    return FilePreview(
        path=_relative(target), kind="arrays", size_bytes=size, truncated=False,
        columns=[], rows=[], text="", arrays=arrays,
        note="shapes read from the archive header; no array was loaded",
    )


def _text_preview(target: Path, size: int) -> FilePreview:
    with target.open("r", encoding="utf-8", errors="replace") as handle:
        text = handle.read(MAX_TEXT + 1)
    truncated = len(text) > MAX_TEXT
    return FilePreview(
        path=_relative(target), kind="text", size_bytes=size, truncated=truncated,
        columns=[], rows=[], text=text[:MAX_TEXT], arrays=[],
        note=f"first {MAX_TEXT:,} characters" if truncated else "",
    )


def preview(relative: str) -> FilePreview:
    target = _resolve(relative)
    if not target.is_file():
        raise OutsideRoot(f"{relative!r} is not a file")
    size = target.stat().st_size
    suffix = target.suffix.lower()
    if suffix == ".npz":
        return _array_preview(target, size)
    if suffix in TABLE_SUFFIXES:
        return _table_preview(target, size)
    if suffix in TEXT_SUFFIXES:
        return _text_preview(target, size)
    return FilePreview(
        path=_relative(target), kind="binary", size_bytes=size, truncated=False,
        columns=[], rows=[], text="", arrays=[],
        note=f"no viewer for {suffix or 'this file type'}",
    )
