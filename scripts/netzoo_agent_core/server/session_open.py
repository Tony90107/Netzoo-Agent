"""Start a session, or continue a saved one, the same way for every client.

The HTTP route and the MCP server both open sessions. One function decides
whether a request starts a new worker, attaches to one that is still running,
or replaces one that has stopped, so the two cannot drift apart.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from . import history
from ..session_meta import set_details, set_tags
from .supervisor import SessionSupervisor

__all__ = ["SessionRequest", "open_session"]


class SessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(default="", max_length=64)
    profile: str = Field(default="", max_length=64)
    model: str = Field(default="", max_length=200)
    resume: str = Field(default="", max_length=64)
    tags: list[str] = Field(default_factory=list, max_length=12)
    name: str = Field(default="", max_length=200)


async def open_session(supervisor: SessionSupervisor, request: SessionRequest) -> dict:
    # Resuming continues a saved session under its own id, as `--resume`
    # does in the terminal, so its name, notes, tags and output folder stay
    # one experiment. A worker still running it is attached to instead,
    # the way a reconnect is; one that has stopped is replaced.
    resumed = request.resume if not request.session_id and history.has_checkpoint(request.resume) else ""
    if resumed:
        live = next((item for item in supervisor.list_sessions() if item["session_id"] == resumed), None)
        if live and live["alive"] and not live["stopped"]:
            return {"session_id": resumed, "tags": history.session_details(resumed)["tags"], "attached": True}
        if live:
            await supervisor.close(resumed)
    session_id = request.session_id or resumed or uuid.uuid4().hex[:8]
    await supervisor.create(
        session_id,
        {
            key: value
            for key, value in request.model_dump().items()
            if value and key not in {"session_id", "tags", "name"}
        },
    )
    tags = set_tags(session_id, request.tags, sessions_root=history.SESSION_ROOT) if request.tags else []
    name = (set_details(session_id, name=request.name, sessions_root=history.SESSION_ROOT)["name"]
            if request.name.strip() else "")
    return {"session_id": session_id, "tags": tags, "name": name}
