"""Read saved activity without starting a worker or modifying its journal."""
from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import HTTPException

from .. import settings
from ..trace_contracts import ZERO_HASH, RunManifest, TraceEvent
from .history import _safe

MAX_MANIFEST_BYTES = 64 * 1024
MAX_EVENT_BYTES = 2 * 1024 * 1024
MAX_RUN_BYTES = 64 * 1024 * 1024


def _file(run_id: str, name: str) -> Path:
    try:
        canonical = str(UUID(run_id))
    except ValueError as error:
        raise HTTPException(400, "run id must be a UUID") from error
    root = Path(settings.TRACE_ROOT).resolve()
    run = root / canonical
    path = run / name
    if run.is_symlink() or path.is_symlink() or path.resolve().parent != run:
        raise HTTPException(404, "saved activity unavailable")
    return path


def _manifest(run_id: str) -> RunManifest:
    path = _file(run_id, "manifest.json")
    try:
        if not path.is_file():
            raise FileNotFoundError("manifest is not a regular file")
        with path.open("rb") as stream:
            raw = stream.read(MAX_MANIFEST_BYTES + 1)
        if len(raw) > MAX_MANIFEST_BYTES:
            raise ValueError("oversized manifest")
        manifest = RunManifest.model_validate_json(raw)
        if str(manifest.run_id) != str(UUID(run_id)):
            raise ValueError("mismatched run id")
        return manifest
    except (OSError, ValueError) as error:
        raise HTTPException(404, "saved activity metadata unavailable") from error


def list_runs(session_id: str, *, offset: int = 0, limit: int = 50) -> dict:
    _safe(session_id)
    manifests = []
    unavailable = 0
    root = Path(settings.TRACE_ROOT)
    if root.is_dir():
        for directory in root.iterdir():
            try:
                UUID(directory.name)
            except ValueError:
                continue
            try:
                manifest = _manifest(directory.name)
            except HTTPException:
                unavailable += 1
                continue
            if manifest.session_id == session_id:
                manifests.append(manifest)
    manifests.sort(key=lambda item: (item.created_at, str(item.run_id)), reverse=True)
    return {
        "runs": [item.model_dump(mode="json") for item in manifests[offset:offset + limit]],
        "total": len(manifests), "offset": offset,
        "has_more": offset + limit < len(manifests),
        "unavailable_metadata": unavailable,
    }


def read_events(session_id: str, run_id: str, *, after_sequence: int = 0,
                limit: int = 200, version: str = "") -> dict:
    _safe(session_id)
    manifest = _manifest(run_id)
    if manifest.session_id != session_id:
        raise HTTPException(404, "no such run in this session")
    snapshot = f"{manifest.final_sequence}:{manifest.final_hash}"
    if version and version != snapshot:
        raise HTTPException(409, "Saved activity changed. Reload this run to read a consistent snapshot.")
    if after_sequence > manifest.final_sequence:
        raise HTTPException(400, "event cursor exceeds the saved run")
    path = _file(run_id, "events.jsonl")
    events = []
    previous = ZERO_HASH
    sequence = 0
    note = ""
    try:
        if not path.is_file():
            raise FileNotFoundError("events are not a regular file")
        if path.stat().st_size > MAX_RUN_BYTES:
            raise HTTPException(413, "This run exceeds the 64 MiB activity preview limit. Read its local trace files directly.")
        with path.open("rb") as stream:
            while sequence < min(manifest.final_sequence, after_sequence + limit):
                raw = stream.readline(MAX_EVENT_BYTES + 1)
                if not raw or len(raw) > MAX_EVENT_BYTES:
                    note = "The saved trace is truncated or contains an oversized event. Only verified events are shown."
                    break
                try:
                    event = TraceEvent.model_validate_json(raw)
                    if (event.run_id != manifest.run_id or event.sequence != sequence + 1
                            or event.previous_hash != previous or not event.verify()):
                        raise ValueError("invalid chain")
                except ValueError:
                    note = "The saved trace failed integrity checks. Only the verified prefix is shown; the original files were preserved."
                    break
                sequence = event.sequence
                previous = event.event_hash
                if sequence > after_sequence:
                    events.append(event.model_dump(mode="json"))
            if not note and sequence == manifest.final_sequence:
                if previous != manifest.final_hash or stream.read(1):
                    note = "The saved trace and metadata disagree. This snapshot is incomplete."
    except OSError as error:
        raise HTTPException(404, "saved event file unavailable") from error
    return {
        "events": events, "run": manifest.model_dump(mode="json"), "version": snapshot,
        "next_sequence": sequence if not note and sequence < manifest.final_sequence else None,
        "incomplete": bool(note), "note": note,
    }
