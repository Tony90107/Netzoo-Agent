"""Typed contracts for bounded, read-only workspace resource discovery."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field
from workflow_registry import RecommendedAction


class WorkspaceDiscoveryScope(BaseModel):
    workspace_root: str = Field(min_length=1, max_length=4_000)
    resource_subpath: str | None = Field(default=None, max_length=4_000)
    resource_actions: list[RecommendedAction] = Field(default_factory=list)


class ValidatedResourceBundle(BaseModel):
    directory: str
    compatible_actions: list[RecommendedAction] = Field(min_length=1)
    inputs: dict[str, str] = Field(min_length=1)
    validation_reasons: list[str] = Field(min_length=1)


class PartialResourceCandidate(BaseModel):
    directory: str
    action: RecommendedAction
    matched_inputs: dict[str, str] = Field(default_factory=dict)
    missing_inputs: list[str] = Field(min_length=1)


class WorkspaceResourceInventory(BaseModel):
    schema: Literal["workspace_resource_inventory"] = "workspace_resource_inventory"
    scope_root: str
    visited_file_count: int = Field(ge=0)
    truncated: bool = False
    validated_bundles: list[ValidatedResourceBundle] = Field(default_factory=list)
    partial_candidates: list[PartialResourceCandidate] = Field(default_factory=list)
    rejected_summary: dict[str, int] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list, max_length=20)


__all__ = [
    "WorkspaceDiscoveryScope",
    "ValidatedResourceBundle",
    "PartialResourceCandidate",
    "WorkspaceResourceInventory",
]
