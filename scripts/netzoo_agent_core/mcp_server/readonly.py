"""Tools that only read: the workflow catalog, saved sessions, output files.

None of these calls a model or starts a worker. Each returns what the desktop
window already shows through the daemon's REST routes, read by the same
functions, so the limits and path checks are the ones already in force.
Descriptions come from the workflow specifications; nothing here is written
about a method that its specification does not say.
"""

from __future__ import annotations

from datetime import datetime, timezone

import yaml

from ..server import files, history
from ..settings import PROJECT_ROOT

__all__ = [
    "ReadError",
    "get_transcript",
    "list_outputs",
    "list_sessions",
    "list_workflows",
    "preview_output",
]

PREVIEW_ROWS = 40
PREVIEW_COLUMNS = 30
PREVIEW_TEXT = 12_000
TRANSCRIPT_MESSAGES = 30


class ReadError(RuntimeError):
    """A read that was refused or found nothing; the message is for the model."""


def list_workflows() -> list[dict]:
    """Each registered workflow, as its specification file describes it."""
    rows = []
    for path in sorted((PROJECT_ROOT / "workflows").glob("*.yaml")):
        try:
            spec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue
        capability = spec.get("output_capability") or {}
        rows.append(
            {
                "workflow": str(spec.get("workflow") or path.stem),
                "action": str(spec.get("action") or ""),
                "description": str(spec.get("description") or ""),
                "required_inputs": list(spec.get("required_inputs") or []),
                "optional_inputs": list(spec.get("optional_inputs") or []),
                "produces": str(capability.get("artifact_type") or ""),
                "granularities": list(capability.get("granularities") or []),
            }
        )
    return rows


def _when(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(timespec="seconds")


def list_sessions(limit: int = 20, query: str = "") -> list[dict]:
    limit = min(max(int(limit), 1), 60)
    return [
        {
            "session_id": item.session_id,
            "name": item.name,
            "first_request": item.title,
            "workflow": item.workflow,
            "status": item.status,
            "resumable": item.resumable,
            "tags": list(item.tags),
            "outputs": list(item.outputs),
            "updated_at": _when(item.updated_at),
        }
        for item in history.list_sessions(limit=limit, query=query)
    ]


def get_transcript(session_id: str, last: int = TRANSCRIPT_MESSAGES) -> dict:
    try:
        transcript = history.read_transcript(session_id)
    except ValueError as error:
        raise ReadError(str(error)) from error
    if transcript is None:
        raise ReadError(f"There is no saved session {session_id!r}.")
    last = min(max(int(last), 1), 200)
    messages = [
        {"role": message["role"], "content": message["content"]}
        for message in transcript.messages[-last:]
    ]
    return {
        "session_id": transcript.session_id,
        "name": transcript.name,
        "status": transcript.status,
        "workflow": transcript.workflow,
        "resumable": transcript.resumable,
        "outputs": list(transcript.outputs),
        "messages": messages,
        "messages_omitted": max(len(transcript.messages) - len(messages), 0),
        # save_session compacts long runs: this is what the agent kept.
        "compacted": transcript.truncated,
    }


def _refused(error: Exception) -> ReadError:
    if isinstance(error, FileNotFoundError):
        return ReadError("That output does not exist. List the folder again.")
    return ReadError(str(error))


def list_outputs(path: str = "", offset: int = 0, limit: int = 100, *, to_host=None) -> dict:
    try:
        listing = files.list_directory(path, offset=max(int(offset), 0), limit=min(max(int(limit), 1), 200))
    except (files.OutsideRoot, files.PreviewInvalid, FileNotFoundError, NotADirectoryError) as error:
        raise _refused(error) from error
    return {
        "path": listing.path,
        "host_path": to_host(listing.path) if to_host else listing.path,
        "total": listing.total,
        "offset": listing.offset,
        "has_more": listing.has_more,
        "entries": [
            {"name": entry.name, "path": entry.path, "kind": entry.kind, "size_bytes": entry.size_bytes}
            for entry in listing.entries
        ],
    }


def preview_output(path: str, offset: int = 0, *, to_host=None) -> dict:
    """The start of one output file, cut down to what fits in a reply."""
    try:
        preview = files.preview(path, offset=max(int(offset), 0))
    except (files.OutsideRoot, files.PreviewInvalid, files.FileChanged, FileNotFoundError) as error:
        raise _refused(error) from error
    rows = [row[:PREVIEW_COLUMNS] for row in preview.rows[:PREVIEW_ROWS]]
    return {
        "path": preview.path,
        "host_path": to_host(preview.path) if to_host else preview.path,
        "kind": preview.kind,
        "size_bytes": preview.size_bytes,
        "columns": preview.columns[:PREVIEW_COLUMNS],
        "total_columns": preview.total_columns or len(preview.columns),
        "rows": rows,
        "rows_shown": len(rows),
        "text": preview.text[:PREVIEW_TEXT],
        "arrays": preview.arrays,
        "note": preview.note,
        # More of the file exists than is shown here, whichever limit cut it.
        "truncated": bool(
            preview.truncated
            or len(preview.rows) > PREVIEW_ROWS
            or len(preview.columns) > PREVIEW_COLUMNS
            or len(preview.text) > PREVIEW_TEXT
        ),
    }
