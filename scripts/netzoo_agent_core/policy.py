"""Fail-closed loading and validation of project and workflow policy."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml

from workflow_registry import (
    ACTION_DEFINITIONS,
    OutputCapabilityDefinition,
    RUN_ACTIONS,
)

from .contracts import (
    AgentsPolicyHeader,
    PROJECT_ROOT,
    ProjectPolicySnapshot,
    TaskDecision,
    WorkflowPolicySpec,
    _display_path,
)

__all__ = [
    "ProjectPolicyError",
    "ProjectPolicyLoader",
]


class ProjectPolicyError(RuntimeError):
    """Raised when project policy is missing, malformed, or conflicts with code."""


class ProjectPolicyLoader:
    """Load versioned project conventions without granting them tool authority."""

    def __init__(self, start: Path | None = None, max_agents_bytes: int = 64_000):
        self.start = (start or PROJECT_ROOT).resolve()
        self.max_agents_bytes = max_agents_bytes

    def find_agents_file(self) -> Path:
        current = self.start if self.start.is_dir() else self.start.parent
        while True:
            candidate = current / "AGENTS.md"
            if candidate.is_file():
                return candidate
            if (current / ".git").exists() or current == current.parent:
                break
            current = current.parent
        raise ProjectPolicyError(
            f"No AGENTS.md was found from {self.start} up to the project boundary."
        )

    @staticmethod
    def _parse_front_matter(text: str, path: Path) -> AgentsPolicyHeader:
        match = re.match(
            r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)",
            text,
            flags=re.DOTALL,
        )
        if not match:
            raise ProjectPolicyError(
                f"{path} must begin with YAML front matter delimited by --- lines."
            )
        try:
            payload = yaml.safe_load(match.group(1))
            header = AgentsPolicyHeader.model_validate(payload)
        except Exception as error:
            raise ProjectPolicyError(
                f"Invalid AGENTS.md policy header in {path}: {error}"
            ) from error
        for convention in header.conventions:
            if not convention.strip() or len(convention) > 400:
                raise ProjectPolicyError(
                    "Every AGENTS.md convention must contain 1-400 characters."
                )
        return header

    @staticmethod
    def _load_workflow_spec(path: Path) -> WorkflowPolicySpec:
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
            spec = WorkflowPolicySpec.model_validate(payload)
        except Exception as error:
            raise ProjectPolicyError(
                f"Invalid workflow policy in {path}: {error}"
            ) from error
        for convention in spec.conventions:
            if not convention.strip() or len(convention) > 400:
                raise ProjectPolicyError(
                    f"Every convention in {path} must contain 1-400 characters."
                )
        return spec

    @staticmethod
    def _validate_against_code(specs: dict[str, WorkflowPolicySpec]) -> None:
        configured = set(specs)
        if configured != RUN_ACTIONS:
            missing = sorted(RUN_ACTIONS - configured)
            extra = sorted(configured - RUN_ACTIONS)
            raise ProjectPolicyError(
                "Workflow policies must exactly match the Python run-action allowlist; "
                f"missing={missing}, extra={extra}."
            )
        known_fields = set(TaskDecision.model_fields)
        for action, spec in specs.items():
            definition = ACTION_DEFINITIONS[action]
            code_required = list(definition.required_inputs)
            if spec.required_inputs != code_required:
                raise ProjectPolicyError(
                    f"{action} required_inputs conflict with Python: "
                    f"yaml={spec.required_inputs}, code={code_required}."
                )
            if spec.execution_step != action:
                raise ProjectPolicyError(
                    f"{action} execution_step must equal its code-enforced action."
                )
            expected_validation = list(definition.validation_steps)
            if spec.validation_steps != expected_validation:
                raise ProjectPolicyError(
                    f"{action} validation_steps conflict with Python: "
                    f"yaml={spec.validation_steps}, code={expected_validation}."
                )
            if spec.workflow != definition.workflow:
                raise ProjectPolicyError(
                    f"{action} workflow must be {definition.workflow}."
                )
            yaml_capability = OutputCapabilityDefinition(
                operation=spec.output_capability.operation,
                artifact_type=spec.output_capability.artifact_type,
                entity_types=frozenset(spec.output_capability.entity_types),
                granularities=frozenset(spec.output_capability.granularities),
                regulator_types=frozenset(spec.output_capability.regulator_types),
                target_types=frozenset(spec.output_capability.target_types),
                guidance_predecessors=tuple(
                    spec.output_capability.guidance_predecessors
                ),
            )
            if yaml_capability != definition.output_capability:
                raise ProjectPolicyError(
                    f"{action} output_capability conflict with Python: "
                    f"yaml={yaml_capability}, code={definition.output_capability}."
                )
            unknown_optional = set(spec.optional_inputs) - known_fields
            overlap = set(spec.optional_inputs) & set(spec.required_inputs)
            expected_optional = list(definition.optional_inputs)
            if spec.optional_inputs != expected_optional or unknown_optional or overlap:
                raise ProjectPolicyError(
                    f"{action} has invalid optional inputs; "
                    f"yaml={spec.optional_inputs}, code={expected_optional}, "
                    f"unknown={sorted(unknown_optional)}, overlap={sorted(overlap)}."
                )

    def load(self) -> ProjectPolicySnapshot:
        agents_path = self.find_agents_file()
        raw_agents = agents_path.read_bytes()
        if len(raw_agents) > self.max_agents_bytes:
            raise ProjectPolicyError(
                f"{agents_path} exceeds the {self.max_agents_bytes}-byte policy limit."
            )
        try:
            agents_text = raw_agents.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ProjectPolicyError(f"{agents_path} must be UTF-8.") from error
        header = self._parse_front_matter(agents_text, agents_path)

        relative_spec_dir = Path(header.workflow_spec_dir)
        if relative_spec_dir.is_absolute() or ".." in relative_spec_dir.parts:
            raise ProjectPolicyError(
                "workflow_spec_dir must be a relative path contained by the AGENTS.md directory."
            )
        spec_dir = (agents_path.parent / relative_spec_dir).resolve()
        if (
            not spec_dir.is_relative_to(agents_path.parent.resolve())
            or not spec_dir.is_dir()
        ):
            raise ProjectPolicyError(
                f"Workflow policy directory does not exist inside the project: {spec_dir}"
            )
        spec_paths = sorted([*spec_dir.glob("*.yaml"), *spec_dir.glob("*.yml")])
        if not spec_paths:
            raise ProjectPolicyError(
                f"No workflow YAML files were found in {spec_dir}."
            )

        specs: dict[str, WorkflowPolicySpec] = {}
        digest = hashlib.sha256(raw_agents)
        for path in spec_paths:
            spec = self._load_workflow_spec(path)
            if spec.action in specs:
                raise ProjectPolicyError(
                    f"Duplicate workflow policy for action {spec.action}."
                )
            specs[spec.action] = spec
            digest.update(path.name.encode("utf-8"))
            digest.update(path.read_bytes())
        self._validate_against_code(specs)
        return ProjectPolicySnapshot(
            policy_version=header.policy_version,
            project=header.project,
            agents_path=_display_path(agents_path),
            workflow_spec_dir=_display_path(spec_dir),
            policy_hash=digest.hexdigest(),
            conventions=header.conventions,
            workflows=specs,
        )
