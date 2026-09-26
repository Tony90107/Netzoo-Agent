"""Project and workflow policy contracts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from workflow_registry import (
    ArtifactType,
    EntityType,
    Granularity,
    InputModality,
    RecommendedAction,
    SELECTION_AXES,
)

class AgentsPolicyHeader(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: Literal[2]
    project: str = Field(min_length=1, max_length=120)
    workflow_spec_dir: str = Field(min_length=1, max_length=200)
    conventions: list[str] = Field(default_factory=list, max_length=20)


ControlType = Literal[
    "boolean", "integer", "number", "string", "string_list", "enum"
]


class WorkflowControlSpec(BaseModel):
    """YAML representation of one registry-owned workflow control."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str = Field(min_length=1, max_length=80)
    control_type: ControlType = Field(alias="type")
    default: Any = None
    allowed_values: list[Any] = Field(default_factory=list, max_length=32)
    minimum: float | None = None
    maximum: float | None = None
    nullable: bool = False
    selection_tags: list[str] = Field(default_factory=list, max_length=8)
    executor_argument: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=400)

    @property
    def type(self) -> ControlType:
        """Compatibility accessor for callers that use the YAML field name."""
        return self.control_type


class ConditionalOutputSpec(BaseModel):
    """YAML representation of a control-dependent output rule."""

    model_config = ConfigDict(extra="forbid")

    when: dict[str, Any] = Field(min_length=1, max_length=8)
    produced_artifacts: list[ArtifactType] = Field(default_factory=list, max_length=8)
    semantics: str = Field(min_length=1, max_length=800)
    manifest_expectations: dict[str, Any] = Field(default_factory=dict, max_length=16)
    valid: bool = True

class WorkflowOutputCapabilitySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: Literal["infer", "analyze"]
    artifact_type: ArtifactType
    entity_types: list[EntityType] = Field(max_length=8)
    granularities: list[Granularity] = Field(max_length=3)
    accepted_input_modalities: list[InputModality] = Field(
        default_factory=list, max_length=8
    )
    guidance_notes: list[str] = Field(default_factory=list, max_length=8)
    # Experimental conditions ("axis:value" from SELECTION_AXES) under which
    # this workflow is preferred over a same-output alternative (Log 139).
    prefer_when: list[str] = Field(default_factory=list, max_length=4)
    accepted_input_granularities: list[Granularity] = Field(
        default_factory=list, max_length=3
    )
    produced_artifacts: list[ArtifactType] = Field(default_factory=list, max_length=8)
    transformations: list[str] = Field(default_factory=list, max_length=16)
    scientific_objectives: list[str] = Field(default_factory=list, max_length=12)
    incompatible_input_artifacts: list[ArtifactType] = Field(
        default_factory=list, max_length=8
    )
    selection_phrases: list[str] = Field(default_factory=list, max_length=32)
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
    conditional_outputs: list[ConditionalOutputSpec] = Field(
        default_factory=list, max_length=8
    )

    @field_validator("prefer_when")
    @classmethod
    def _registered_conditions_only(cls, values: list[str]) -> list[str]:
        for value in values:
            axis, _, level = value.partition(":")
            if level not in SELECTION_AXES.get(axis, {}).get("values", {}):
                raise ValueError(f"Unknown selection condition: {value}")
        return values


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
        "run_bonobo",
    ]
    description: str = Field(min_length=1, max_length=500)
    required_inputs: list[str] = Field(max_length=12)
    required_input_groups: list[list[str]] = Field(default_factory=list, max_length=8)
    optional_inputs: list[str] = Field(default_factory=list, max_length=12)
    output_files: list[str] = Field(default_factory=list, max_length=20)
    validation_steps: list[Literal[
        "inspect_inputs", "inspect_condor_inputs", "inspect_cobra_inputs",
        "inspect_sambar_inputs", "inspect_dragon_inputs", "inspect_otter_inputs",
        "inspect_giraffe_inputs", "inspect_bonobo_inputs",
    ]] = Field(
        default_factory=list, max_length=4
    )
    input_validator: Literal[
        "run_panda", "run_puma", "run_lioness_panda", "run_lioness_puma",
        "run_lioness_coexpression", "run_condor", "run_cobra", "run_sambar",
        "run_dragon", "run_otter", "run_giraffe", "run_bonobo",
    ]
    controls: list[WorkflowControlSpec] = Field(default_factory=list, max_length=32)
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
        "run_giraffe", "run_bonobo",
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
                f"Input modalities: {','.join(capability.accepted_input_modalities) or 'unspecified'}. "
                f"Accepted input granularities: "
                f"{','.join(capability.accepted_input_granularities) or 'unspecified'}. "
                f"Produced artifacts: {','.join(capability.produced_artifacts) or capability.artifact_type}. "
                f"Transformations: {','.join(capability.transformations) or 'none'}. "
                f"Objectives: {','.join(capability.scientific_objectives) or 'none'}. "
                f"Incompatible inputs: {','.join(capability.incompatible_input_artifacts) or 'none'}. "
                f"Selection tags: {','.join(capability.selection_tags) or 'none'}. "
                f"Consumes: {','.join(capability.input_artifacts) or 'raw/user input'}. "
                f"Handoff targets: {','.join(capability.handoff_targets) or 'none'}. "
                f"Required inputs: {', '.join(spec.required_inputs)}. "
                f"Required input alternatives: "
                f"{' AND '.join(' OR '.join(group) for group in spec.required_input_groups) or 'none'}. "
                f"Controls: "
                f"{', '.join(item.name for item in spec.controls) or 'none'}. "
                f"Handoff contract: {capability.handoff_contract or 'none'}."
            )
        return "\n".join(lines)

__all__ = [
    "AgentsPolicyHeader",
    "ProjectPolicySnapshot",
    "WorkflowControlSpec",
    "ConditionalOutputSpec",
    "WorkflowOutputCapabilitySpec",
    "WorkflowPolicySpec",
]
