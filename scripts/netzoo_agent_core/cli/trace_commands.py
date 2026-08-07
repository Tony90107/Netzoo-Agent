"""Administrative local-trace commands."""

from __future__ import annotations

from pathlib import Path

from ..contracts import TRACE_ROOT
from ..trace_store import LocalTraceStore

__all__ = ["export_local_trace", "local_trace_status"]

def local_trace_status(run_id: str, *, trace_root: Path = TRACE_ROOT) -> dict:
    """Verify and summarize one local trace without an LLM or provider key."""
    verification = LocalTraceStore(trace_root).verify_run(run_id)
    return {"run_id": run_id, **verification.model_dump(mode="json")}

def export_local_trace(
    run_id: str,
    destination: Path,
    *,
    trace_root: Path = TRACE_ROOT,
) -> Path:
    """Export one verified local audit package without overwriting a file."""
    return LocalTraceStore(trace_root).export_run(run_id, Path(destination))
