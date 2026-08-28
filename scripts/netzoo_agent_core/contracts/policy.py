"""Project and workflow policy contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from workflow_registry import (
    ArtifactType,
    EntityType,
    Granularity,
    RecommendedAction,
)

class AgentsPolicyHeader(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: Literal[2]
    project: str = Field(min_length=1, max_length=120)
    workflow_spec_dir: str = Field(min_length=1, max_length=200)
    conventions: list[str] = Field(default_factory=list, max_length=20)

class WorkflowOutputCapabilitySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: Literal["infer", "analyze"]
    artifact_type: ArtifactType
    entity_types: list[EntityType] = Field(max_length=8)
    granularities: list[Granularity] = Field(max_length=3)
    regulator_types: list[Literal["tf", "mirna"]] = Field(
        default_factory=list, max_length=2
    )
    target_types: list[Literal["gene"]] = Field(default_factory=list, max_length=1)
    guidance_predecessors: list[RecommendedAction] = Field(
        default_factory=list, max_length=2
    )
    input_artifacts: list[ArtifactType] = Field(default_factory=list, max_length=4)
    handoff_targets: list[RecommendedAction] = Field(default_factory=list, max_length=4)
    selection_tags: list[str] = Field(default_factory=list, max_length=12)
    handoff_contract: str = Field(default="", max_length=800)


class WorkflowPolicySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: Literal[2]
    workflow: str = Field(min_length=1, max_length=80)
    action: Literal[
        "run_panda",
        "run_puma",
        "run_lioness_panda",
        "run_lioness_puma",
        "run_lioness_coexpression",
        "run_condor",
        "run_cobra",
        "run_sambar",
        "run_dragon",
        "run_otter",
        "run_giraffe",
    ]
    description: str = Field(min_length=1, max_length=500)
    required_inputs: list[str] = Field(max_length=12)
    optional_inputs: list[str] = Field(default_factory=list, max_length=12)
    validation_steps: list[Literal[
        "inspect_inputs", "inspect_condor_inputs", "inspect_cobra_inputs",
        "inspect_sambar_inputs", "inspect_dragon_inputs", "inspect_otter_inputs",
        "inspect_giraffe_inputs",
    ]] = Field(
        default_factory=list, max_length=4
    )
    execution_step: Literal[
        "run_panda",
        "run_puma",
        "run_lioness_panda",
        "run_lioness_puma",
        "run_lioness_coexpression",
        "run_condor",
        "run_cobra",
        "run_sambar",
        "run_dragon",
        "run_otter",
        "run_giraffe",
    ]
    output_capability: WorkflowOutputCapabilitySpec
    conventions: list[str] = Field(default_factory=list, max_length=20)

class ProjectPolicySnapshot(BaseModel):
    policy_version: Literal[2]
    project: str
    agents_path: str
    workflow_spec_dir: str
    policy_hash: str
    conventions: list[str] = Field(default_factory=list)
    workflows: dict[str, WorkflowPolicySpec]

    def router_capability_summary(self) -> str:
        """Generate the run-workflow catalog from the validated policy registry."""
        lines = []
        for action, spec in sorted(self.workflows.items()):
            capability = spec.output_capability
            lines.append(
                f"- {action}: {spec.description} "
                f"Produces: operation={capability.operation}, "
                f"artifact={capability.artifact_type}, "
                f"entities={','.join(capability.entity_types) or 'none'}, "
                f"regulators={','.join(capability.regulator_types) or 'none'}, "
                f"targets={','.join(capability.target_types) or 'none'}, "
                f"granularities={','.join(capability.granularities)}. "
                f"Selection tags: {','.join(capability.selection_tags) or 'none'}. "
                f"Consumes: {','.join(capability.input_artifacts) or 'raw/user input'}. "
                f"Handoff targets: {','.join(capability.handoff_targets) or 'none'}. "
                f"Required inputs: {', '.join(spec.required_inputs)}. "
                f"Handoff contract: {capability.handoff_contract or 'none'}."
            )
        return "\n".join(lines)

__all__ = [
    "AgentsPolicyHeader",
    "ProjectPolicySnapshot",
    "WorkflowOutputCapabilitySpec",
    "WorkflowPolicySpec",
]
