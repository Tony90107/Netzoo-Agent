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
import codecs
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

from ..settings import PROJECT_ROOT

__all__ = [
    "FILE_ROOT",
    "DirectoryListing",
    "Entry",
    "FilePreview",
    "FileChanged",
    "PreviewInvalid",
    "OutsideRoot",
    "list_directory",
    "preview",
]

#: The one subtree the window may browse. Inputs are the agent's business.
FILE_ROOT = "outputs"

#: A table preview never returns more than this many rows.
MAX_ROWS = 200
#: A text preview reads at most this many bytes, preserving UTF-8 boundaries.
MAX_TEXT = 200_000
MAX_RECORD_BYTES = 2_000_000
MAX_PAGE_BYTES = 4_000_000
MAX_COLUMNS = 50

TABLE_SUFFIXES = {".tsv", ".csv", ".txt"}
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".log"}


class OutsideRoot(ValueError):
    """A request named something outside the browsable root."""


class PreviewInvalid(ValueError):
    """The requested cursor or record cannot be previewed safely."""


class FileChanged(ValueError):
    """A file changed between preview pages; refresh before continuing."""


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
    total: int
    offset: int
    limit: int
    has_more: bool


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
    offset: int = 0
    next_offset: int | None = None
    version: str = ""
    total_columns: int = 0


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


def list_directory(
    relative: str = "", *, offset: int = 0, limit: int = 100
) -> DirectoryListing:
    """Return one bounded page of the outputs tree.

    Directory names are sorted before paging so loading another buffer keeps a
    stable order. File metadata is only read for entries in the requested page.
    """
    target = _resolve(relative)
    if offset < 0 or not 1 <= limit <= 200:
        raise PreviewInvalid("Invalid directory page.")
    if target == _root() and not target.exists():
        return DirectoryListing(FILE_ROOT, [], 0, offset, limit, False)
    if not target.is_dir():
        raise OutsideRoot(f"{relative!r} is not a directory")
    visible = sorted(
        (child for child in target.iterdir() if not child.name.startswith(".")
         and child.resolve().is_relative_to(_root()) and child.exists()),
        key=lambda item: (item.is_file(), item.name.lower(), item.name),
    )
    total = len(visible)
    page = visible[offset : offset + limit]
    entries: list[Entry] = []
    for child in page:
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
    return DirectoryListing(
        path=_relative(target),
        entries=entries,
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + len(entries) < total,
    )


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


def _table_preview(target: Path, size: int, offset: int = 0) -> FilePreview:
    delimiter = "," if target.suffix.lower() == ".csv" else "\t"
    rows: list[list[str]] = []
    cursor = 0
    with target.open("rb") as handle:
        # csv.reader may consume multiple physical lines for one quoted record.
        # Bound every record, then keep a byte cursor at a complete record boundary.
        record_start = 0

        def bounded_lines():
            while True:
                line = handle.readline(MAX_RECORD_BYTES + 1)
                if not line:
                    return
                if handle.tell() - record_start > MAX_RECORD_BYTES:
                    raise PreviewInvalid(
                        "A table record exceeds the 2 MB preview limit. "
                        "Open this file in a dedicated data viewer."
                    )
                yield line.decode("utf-8", errors="replace")

        reader = csv.reader(bounded_lines(), delimiter=delimiter)
        try:
            header = next(reader, [])
            header_end = handle.tell()
            if offset and offset < header_end:
                raise PreviewInvalid("Invalid table cursor. Refresh this file to restart the preview.")
            handle.seek(offset or header_end)
            reader = csv.reader(bounded_lines(), delimiter=delimiter)
            page_start = handle.tell()
            cursor = page_start
            for _ in range(MAX_ROWS):
                record_start = handle.tell()
                row = next(reader, None)
                if row is None:
                    break
                if rows and handle.tell() - page_start > MAX_PAGE_BYTES:
                    cursor = record_start
                    break
                rows.append(row)
                cursor = handle.tell()
        except csv.Error as error:
            raise PreviewInvalid(f"This table cannot be previewed: {error}") from error
    header = _realigned_header(header, rows)
    width = max([len(header), *(len(row) for row in rows)], default=0)
    more = cursor < size
    truncated = more or width > MAX_COLUMNS
    note = (f"first {len(rows)} rows" if offset == 0 else f"{len(rows)} rows in this page") if truncated else ""
    if width > MAX_COLUMNS:
        note += f"; first {MAX_COLUMNS} of {width} columns"
    return FilePreview(
        path=_relative(target),
        kind="table",
        size_bytes=size,
        truncated=truncated,
        columns=header[:MAX_COLUMNS],
        rows=[row[:MAX_COLUMNS] for row in rows],
        text="",
        arrays=[],
        note=note,
        offset=offset, next_offset=cursor if more else None, total_columns=width,
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


def _text_preview(target: Path, size: int, offset: int = 0) -> FilePreview:
    with target.open("rb") as handle:
        handle.seek(offset)
        buffer = handle.read(MAX_TEXT)
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    text = decoder.decode(buffer, final=offset + len(buffer) >= size)
    pending, _ = decoder.getstate()
    cursor = offset + len(buffer) - len(pending)
    truncated = cursor < size
    return FilePreview(
        path=_relative(target), kind="text", size_bytes=size, truncated=truncated,
        columns=[], rows=[], text=text, arrays=[],
        note=f"up to {MAX_TEXT:,} bytes per page" if truncated else "",
        offset=offset, next_offset=cursor if truncated else None,
    )


def preview(relative: str, *, offset: int = 0, version: str = "") -> FilePreview:
    target = _resolve(relative)
    if not target.exists():
        raise FileNotFoundError(relative)
    if not target.is_file():
        raise OutsideRoot(f"{relative!r} is not a file")
    stat = target.stat()
    size = stat.st_size
    current_version = f"{size}:{stat.st_mtime_ns}:{stat.st_ino}"
    if version and version != current_version:
        raise FileChanged("This file changed since the previous preview. Refresh it before reading another page.")
    if offset < 0 or offset > size:
        raise PreviewInvalid("The preview cursor is outside this file. Refresh the preview.")
    suffix = target.suffix.lower()
    if suffix == ".npz":
        result = _array_preview(target, size)
    elif suffix in TABLE_SUFFIXES:
        result = _table_preview(target, size, offset)
    elif suffix in TEXT_SUFFIXES:
        result = _text_preview(target, size, offset)
    else:
        result = FilePreview(
            path=_relative(target), kind="binary", size_bytes=size, truncated=False,
            columns=[], rows=[], text="", arrays=[],
            note=f"no viewer for {suffix or 'this file type'}",
        )
    after = target.stat()
    if current_version != f"{after.st_size}:{after.st_mtime_ns}:{after.st_ino}":
        raise FileChanged("This file changed while it was being read. Refresh the preview.")
    return replace(result, version=current_version)
