"""Short-term resumable session persistence and runtime retention."""

from __future__ import annotations

import json
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID


from .contracts import (
    AIMessage,
    DEFAULT_RETENTION_DAYS,
    DEFAULT_SESSION_HARD_RETENTION_DAYS,
    HumanMessage,
    SESSION_ROOT,
    TRACE_ROOT,
    TOOL_LOG_ROOT,
)
from .trace_contracts import RunManifest

from .memory import (
    _harden_private_tree,
    _write_json_atomic,
)

__all__ = [
    "_safe_session_id",
    "_session_path",
    "_is_auto_session_id",
    "latest_pending_session_id",
    "resolve_resume_id",
    "cleanup_runtime_storage",
    "cleanup_trace_storage",
    "delete_session",
    "compact_conversation",
    "save_session",
    "load_session",
    "load_session_payload",
]


def _safe_session_id(session_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", session_id).strip(".-")
    if not cleaned:
        raise ValueError("session id must contain a letter or number")
    return cleaned[:80]


def _session_path(session_id: str) -> Path:
    return SESSION_ROOT / f"{_safe_session_id(session_id)}.json"


def _is_auto_session_id(session_id: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{8}", session_id))


def latest_pending_session_id(profile_id: str | None = None) -> str | None:
    """Return the newest resumable clarification without requiring the user to know its id."""
    if not SESSION_ROOT.exists():
        return None
    pending: list[tuple[int, str]] = []
    for path in SESSION_ROOT.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if (payload.get("plan") or {}).get("status") != "needs_input":
                if (payload.get("plan") or {}).get("status") != "needs_confirmation":
                    continue
            if profile_id and payload.get("profile_id", "default") != profile_id:
                continue
            pending.append(
                (path.stat().st_mtime_ns, str(payload.get("session_id") or path.stem))
            )
        except (OSError, ValueError, TypeError):
            continue
    if not pending:
        return None
    pending.sort(reverse=True)
    return pending[0][1]


def resolve_resume_id(requested_resume: str | None, profile_id: str) -> str | None:
    """Resolve an explicit resume request; fresh interactive starts do not auto-resume."""
    if requested_resume == "latest":
        resume_id = latest_pending_session_id(profile_id)
        if not resume_id:
            raise SystemExit("No pending session is available to resume.")
        return resume_id
    return requested_resume


def cleanup_runtime_storage(
    retention_days: int = DEFAULT_RETENTION_DAYS,
    hard_retention_days: int = DEFAULT_SESSION_HARD_RETENTION_DAYS,
) -> dict[str, int]:
    """Prune routine data, with a hard expiry for every session kind."""
    cutoff = time.time() - max(retention_days, 1) * 86_400
    hard_cutoff = time.time() - max(hard_retention_days, retention_days, 1) * 86_400
    removed = {"sessions": 0, "logs": 0}
    if SESSION_ROOT.exists():
        _harden_private_tree(SESSION_ROOT)
        for path in SESSION_ROOT.glob("*.json"):
            modified_at = path.stat().st_mtime
            if modified_at < hard_cutoff:
                path.unlink()
                removed["sessions"] += 1
                continue
            if modified_at >= cutoff or not _is_auto_session_id(path.stem):
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                if (payload.get("plan") or {}).get("status") in {
                    "needs_input",
                    "needs_confirmation",
                }:
                    continue
                path.unlink()
                removed["sessions"] += 1
            except (OSError, ValueError, TypeError):
                continue
    if TOOL_LOG_ROOT.exists():
        _harden_private_tree(TOOL_LOG_ROOT)
        for path in TOOL_LOG_ROOT.glob("*.log"):
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink()
                    removed["logs"] += 1
            except OSError:
                continue
    return removed


def cleanup_trace_storage(
    retention_days: int = 90,
    *,
    trace_root: Path = TRACE_ROOT,
) -> int:
    """Remove only sealed trace runs older than the configured retention."""
    root = Path(trace_root).resolve()
    if not root.exists():
        return 0
    cutoff = datetime.now(timezone.utc).timestamp() - max(retention_days, 1) * 86_400
    removed = 0
    for candidate in root.iterdir():
        if not candidate.is_dir():
            continue
        try:
            UUID(candidate.name)
        except ValueError:
            continue
        resolved = candidate.resolve()
        if resolved.parent != root:
            continue
        try:
            manifest = RunManifest.model_validate_json(
                (resolved / "manifest.json").read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            continue
        if not manifest.sealed or manifest.finished_at is None:
            continue
        if manifest.finished_at.timestamp() >= cutoff:
            continue
        shutil.rmtree(resolved)
        removed += 1
    return removed


def delete_session(session_id: str) -> bool:
    path = _session_path(session_id)
    if not path.exists():
        return False
    path.unlink()
    return True


def compact_conversation(
    messages: list,
    *,
    max_messages: int = 12,
    max_chars: int = 16_000,
) -> list:
    """Bound persisted short-term history while preserving the newest turns."""
    kept = []
    used_chars = 0
    for message in reversed(messages):
        content = str(getattr(message, "content", ""))
        if kept and (
            len(kept) >= max_messages or used_chars + len(content) > max_chars
        ):
            break
        kept.append(message)
        used_chars += len(content)
    return list(reversed(kept))


def save_session(
    session_id: str,
    messages: list,
    state: dict,
    profile_id: str = "default",
) -> Path:
    """Persist enough state to resume a CLI clarification after container exit."""
    path = _session_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized_messages = []
    for message in messages:
        role = "assistant" if getattr(message, "type", "") == "ai" else "user"
        serialized_messages.append({"role": role, "content": str(message.content)})
    created_at = time.time()
    if path.exists():
        try:
            created_at = json.loads(path.read_text(encoding="utf-8")).get(
                "created_at", created_at
            )
        except (OSError, ValueError, TypeError):
            pass
    payload = {
        "version": 1,
        "session_id": session_id,
        "profile_id": profile_id,
        "auto_generated": _is_auto_session_id(session_id),
        "created_at": created_at,
        "updated_at": time.time(),
        "messages": serialized_messages,
        "plan": state.get("plan"),
        "evaluation": state.get("evaluation"),
        "tool_results": state.get("tool_results", []),
        "token_usage": state.get("token_usage"),
        "run_id": state.get("run_id"),
    }
    _write_json_atomic(path, payload)
    return path


def load_session(
    session_id: str,
    *,
    include_usage: bool = False,
) -> tuple[list, dict | None] | tuple[list, dict | None, dict | None]:
    payload = load_session_payload(session_id)
    messages = []
    for item in payload.get("messages", []):
        cls = AIMessage if item.get("role") == "assistant" else HumanMessage
        messages.append(cls(content=item.get("content", "")))
    plan = payload.get("plan")
    if include_usage:
        return messages, plan, payload.get("token_usage")
    return messages, plan


def load_session_payload(session_id: str) -> dict:
    """Load the complete versioned checkpoint for CLI lifecycle decisions."""
    path = _session_path(session_id)
    if not path.exists():
        raise FileNotFoundError(f"Session not found: {session_id} ({path})")
    return json.loads(path.read_text(encoding="utf-8"))
