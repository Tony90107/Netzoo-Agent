"""Project and workflow policy contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

class AgentsPolicyHeader(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: Literal[1]
    project: str = Field(min_length=1, max_length=120)
    workflow_spec_dir: str = Field(min_length=1, max_length=200)
    conventions: list[str] = Field(default_factory=list, max_length=20)

class WorkflowPolicySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: Literal[1]
    workflow: str = Field(min_length=1, max_length=80)
    action: Literal[
        "run_panda",
        "run_puma",
        "run_lioness_panda",
        "run_lioness_puma",
        "run_lioness_coexpression",
        "run_condor",
    ]
    description: str = Field(min_length=1, max_length=500)
    required_inputs: list[str] = Field(max_length=12)
    optional_inputs: list[str] = Field(default_factory=list, max_length=12)
    validation_steps: list[Literal["inspect_inputs", "inspect_condor_inputs"]] = Field(
        default_factory=list, max_length=4
    )
    execution_step: Literal[
        "run_panda",
        "run_puma",
        "run_lioness_panda",
        "run_lioness_puma",
        "run_lioness_coexpression",
        "run_condor",
    ]
    conventions: list[str] = Field(default_factory=list, max_length=20)

class ProjectPolicySnapshot(BaseModel):
    policy_version: Literal[1]
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
            lines.append(
                f"- {action}: {spec.description} "
                f"Required inputs: {', '.join(spec.required_inputs)}."
            )
        return "\n".join(lines)

__all__ = ['AgentsPolicyHeader', 'WorkflowPolicySpec', 'ProjectPolicySnapshot']
