"""Typed contracts for explicit multi-stage workflow handoffs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field
from workflow_registry import ArtifactType, Granularity, RecommendedAction


class WorkflowHandoff(BaseModel):
    """A registry-validated producer-to-consumer workflow boundary."""

    producer_action: RecommendedAction
    producer_workflow: str = Field(min_length=1, max_length=80)
    source_artifact_type: ArtifactType
    source_granularity: Granularity
    produced_artifacts: list[ArtifactType] = Field(default_factory=list, max_length=8)
    source_artifact_paths: list[str] = Field(default_factory=list, max_length=100)
    artifact_paths: dict[str, list[str]] = Field(default_factory=dict, max_length=8)
    sample_ids: list[str] = Field(default_factory=list, max_length=10_000)
    gene_ids: list[str] = Field(default_factory=list, max_length=100_000)
    consumer_action: RecommendedAction | None = None
    consumer_workflow: str | None = Field(default=None, max_length=80)
    consumer_input_field: str | None = Field(default=None, max_length=80)
    required_prior_inputs: list[str] = Field(default_factory=list, max_length=20)
    status: Literal[
        "not_requested",
        "validated",
        "blocked_no_consumer",
        "blocked_incompatible",
    ]
    reason: str = Field(min_length=1, max_length=1_000)


__all__ = ["WorkflowHandoff"]
