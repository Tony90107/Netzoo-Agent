"""Long-term profile and episode contracts."""

from __future__ import annotations

import time
from typing import Literal

from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    profile_id: str
    version: int = 1
    preferences: dict[str, str | bool | list[str]] = Field(default_factory=dict)
    sources: dict[str, str] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

class Episode(BaseModel):
    episode_id: str
    profile_id: str
    created_at: float = Field(default_factory=time.time)
    task_summary: str
    raw_task_excerpt: str | None = None
    workflow: str
    action: str | None = None
    intent_type: str | None = None
    status: Literal["completed", "dry_run", "failed"]
    inputs: dict[str, str] = Field(default_factory=dict)
    input_roles: list[str] = Field(default_factory=list)
    output_roles: list[str] = Field(default_factory=list)
    parameters: list[str] = Field(default_factory=list)
    validation_steps: list[str] = Field(default_factory=list)
    execution_steps: list[str] = Field(default_factory=list)
    validation_status: Literal["passed", "failed", "not_applicable"] = "not_applicable"
    execution_mode: Literal["executed", "dry_run"] = "executed"
    memory_tags: list[str] = Field(default_factory=list)
    domain_metadata: dict[str, str] = Field(default_factory=dict)
    artifacts: list[str] = Field(default_factory=list)
    metrics: dict[str, int | float | str | bool] = Field(default_factory=dict)
    error_signature: str | None = None
    recovery_actions: list[str] = Field(default_factory=list)
    log_files: list[str] = Field(default_factory=list)
    policy_hash: str | None = None

__all__ = ['UserProfile', 'Episode']
