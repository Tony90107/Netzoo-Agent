"""What the agent has been asked before, and what it is running under.

Reading only. Sessions are summarised from the checkpoints the CLI already
writes, so the two drivers see the same history, and the settings view
reports the configuration rather than offering to change it: the model
allowlists and the token budget are what stop a stray request reaching an
expensive model, and a window that could edit them would be a window that
could remove that stop.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from .. import settings as runtime_settings
from ..settings import SESSION_ROOT

__all__ = ["SessionSummary", "describe_settings", "list_sessions"]

#: Summaries are cheap but there are hundreds of checkpoints; show the recent.
DEFAULT_LIMIT = 60

#: Statuses a session can be resumed from, per `latest_pending_session_id`.
RESUMABLE = {"needs_input", "needs_confirmation"}


@dataclass(frozen=True, slots=True)
class SessionSummary:
    session_id: str
    profile_id: str
    updated_at: float
    auto_generated: bool
    workflow: str
    status: str
    resumable: bool
    title: str
    total_tokens: int


def _first_request(payload: dict) -> str:
    """The user's own words, which is how a person recognises a session."""
    for message in payload.get("messages") or []:
        if not isinstance(message, dict):
            continue
        if message.get("type") in {"human", "HumanMessage"} or message.get(
            "role"
        ) == "user":
            content = str(message.get("content") or "").strip()
            if content:
                return content.splitlines()[0][:160]
    return ""


def _summarise(path: Path) -> SessionSummary | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        # A half-written or hand-edited checkpoint is skipped, not fatal: the
        # history list must never be the reason the window fails to open.
        return None
    plan = payload.get("plan") or {}
    status = str(plan.get("status") or "unknown")
    usage = payload.get("token_usage") or {}
    return SessionSummary(
        session_id=str(payload.get("session_id") or path.stem),
        profile_id=str(payload.get("profile_id") or "default"),
        updated_at=path.stat().st_mtime,
        auto_generated=bool(payload.get("auto_generated")),
        workflow=str(plan.get("workflow") or ""),
        status=status,
        resumable=status in RESUMABLE,
        title=_first_request(payload),
        total_tokens=int(usage.get("total_tokens") or 0),
    )


def list_sessions(limit: int = DEFAULT_LIMIT, profile_id: str = "") -> list[SessionSummary]:
    """Newest first. Resumable sessions are the ones worth coming back to."""
    if not SESSION_ROOT.exists():
        return []
    paths = sorted(
        SESSION_ROOT.glob("*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    summaries: list[SessionSummary] = []
    for path in paths:
        summary = _summarise(path)
        if summary is None:
            continue
        if profile_id and summary.profile_id != profile_id:
            continue
        summaries.append(summary)
        if len(summaries) >= limit:
            break
    return summaries


def _model(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip() or "(unset)"


def describe_settings() -> dict:
    """The configuration this daemon is actually running under.

    Reported, not editable. Anything here that could be changed from the
    window would be a control the agent's own limits do not have.
    """
    return {
        "models": {
            "response": _model("OPENROUTER_MODEL"),
            "router": _model("OPENROUTER_ROUTER_MODEL"),
            "semantic": _model("OPENROUTER_SEMANTIC_MODEL"),
        },
        "allowlists": {
            "response": _model("NETZOO_RESPONSE_MODEL_ALLOWLIST"),
            "router": _model("NETZOO_ROUTER_MODEL_ALLOWLIST"),
        },
        "limits": {
            "task_token_budget": int(
                os.environ.get("NETZOO_MAX_TASK_TOKENS")
                or runtime_settings.DEFAULT_TASK_TOKEN_BUDGET
            ),
            "tool_timeout_seconds": float(runtime_settings.TOOL_TIMEOUT_SECONDS),
            "llm_timeout_seconds": float(
                os.environ.get("NETZOO_LLM_TIMEOUT_SECONDS")
                or runtime_settings.DEFAULT_LLM_TIMEOUT_SECONDS
            ),
        },
        "paths": {
            "project_root": str(runtime_settings.PROJECT_ROOT),
            "host_project_root": os.environ.get("NETZOO_HOST_PROJECT_ROOT", ""),
            "traces": str(runtime_settings.TRACE_ROOT),
            "sessions": str(SESSION_ROOT),
        },
        "api_key_present": bool(os.environ.get("OPENROUTER_API_KEY")),
    }
