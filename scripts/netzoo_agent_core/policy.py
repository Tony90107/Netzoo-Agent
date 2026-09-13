"""Fail-closed loading and validation of project and workflow policy."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from types import UnionType
from typing import Any, Literal, Union, get_args, get_origin

import yaml
from pydantic import TypeAdapter

from workflow_registry import (
    ACTION_DEFINITIONS,
    ConditionalOutputDefinition,
    OutputCapabilityDefinition,
    RUN_ACTIONS,
    SELECTION_TAG_GLOSSARY,
    WorkflowControlDefinition,
)

from .contracts import (
    AgentsPolicyHeader,
    ConditionalOutputSpec,
    PROJECT_ROOT,
    ProjectPolicySnapshot,
    TaskDecision,
    WorkflowControlSpec,
    WorkflowPolicySpec,
    _display_path,
)

__all__ = [
    "ProjectPolicyError",
    "ProjectPolicyLoader",
]


class ProjectPolicyError(RuntimeError):
    """Raised when project policy is missing, malformed, or conflicts with code."""


def _control_from_spec(spec: WorkflowControlSpec) -> WorkflowControlDefinition:
    return WorkflowControlDefinition(
        name=spec.name,
        control_type=spec.control_type,
        default=spec.default,
        allowed_values=tuple(spec.allowed_values),
        minimum=spec.minimum,
        maximum=spec.maximum,
        nullable=spec.nullable,
        selection_tags=frozenset(spec.selection_tags),
        executor_argument=spec.executor_argument,
        description=spec.description,
    )


def _conditional_output_from_spec(
    spec: ConditionalOutputSpec,
) -> ConditionalOutputDefinition:
    return ConditionalOutputDefinition(
        when=dict(spec.when),
        produced_artifacts=frozenset(spec.produced_artifacts),
        semantics=spec.semantics,
        manifest_expectations=dict(spec.manifest_expectations),
        valid=spec.valid,
    )


def _control_type_for_annotation(annotation: Any) -> str | None:
    origin = get_origin(annotation)
    if origin in {Union, UnionType}:
        non_null = [item for item in get_args(annotation) if item is not type(None)]
        if len(non_null) == 1:
            return _control_type_for_annotation(non_null[0])
    if origin is Literal:
        return "enum"
    if origin is list:
        return "string_list"
    if annotation is bool:
        return "boolean"
    if annotation is int:
        return "integer"
    if annotation is float:
        return "number"
    if annotation is str:
        return "string"
    return None


def _validate_control_value(
    action: str,
    control: WorkflowControlSpec,
    value: Any,
    label: str,
    adapter: TypeAdapter,
) -> None:
    if value is None:
        if not control.nullable:
            raise ProjectPolicyError(
                f"{action} control {control.name} has a null {label} but is not nullable."
            )
        return
    try:
        adapter.validate_python(value)
    except Exception as error:
        raise ProjectPolicyError(
            f"{action} control {control.name} has an invalid {label}: {error}."
        ) from error
    if control.control_type in {"integer", "number"} and isinstance(value, (int, float)):
        if control.minimum is not None and value < control.minimum:
            raise ProjectPolicyError(
                f"{action} control {control.name} {label} is below minimum {control.minimum}."
            )
        if control.maximum is not None and value > control.maximum:
            raise ProjectPolicyError(
                f"{action} control {control.name} {label} exceeds maximum {control.maximum}."
            )
    if control.allowed_values and value not in control.allowed_values:
        raise ProjectPolicyError(
            f"{action} control {control.name} {label} is not an allowed value."
        )


def _validate_controls(
    action: str,
    spec: WorkflowPolicySpec,
    definition,
    known_fields: set[str],
) -> tuple[WorkflowControlDefinition, ...]:
    controls = spec.controls
    names = [item.name for item in controls]
    if len(names) != len(set(names)):
        raise ProjectPolicyError(f"{action} declares duplicate workflow controls.")
    executor_arguments = [item.executor_argument for item in controls]
    if len(executor_arguments) != len(set(executor_arguments)):
        raise ProjectPolicyError(f"{action} declares duplicate control executor arguments.")
    required = set(spec.required_inputs)
    optional = set(spec.optional_inputs)
    executor_fields = set(definition.executor_fields)
    unknown_executor_fields = executor_fields - known_fields
    if unknown_executor_fields:
        raise ProjectPolicyError(
            f"{action} has unknown executor arguments: {sorted(unknown_executor_fields)}."
        )
    converted = tuple(_control_from_spec(item) for item in controls)
    expected = tuple(definition.controls)
    if converted != expected:
        raise ProjectPolicyError(
            f"{action} controls conflict with the registry declaration: "
            f"yaml={converted}, code={expected}."
        )
    for item in controls:
        if item.name not in known_fields:
            raise ProjectPolicyError(f"{action} control {item.name} is not a TaskDecision field.")
        if item.name in required or item.name in optional and item.name in required:
            raise ProjectPolicyError(
                f"{action} control {item.name} collides with a required input."
            )
        if item.executor_argument not in executor_fields or item.executor_argument not in known_fields:
            raise ProjectPolicyError(
                f"{action} control {item.name} references unknown executor argument "
                f"{item.executor_argument}."
            )
        if item.control_type not in {"boolean", "integer", "number", "string", "string_list", "enum"}:
            raise ProjectPolicyError(f"{action} control {item.name} has unknown control type.")
        field = TaskDecision.model_fields[item.name]
        expected_type = _control_type_for_annotation(field.annotation)
        if expected_type != item.control_type:
            raise ProjectPolicyError(
                f"{action} control {item.name} type {item.control_type} does not match "
                f"TaskDecision type {expected_type}."
            )
        adapter = TypeAdapter(field.annotation)
        _validate_control_value(action, item, item.default, "default", adapter)
        if item.control_type == "enum" and not item.allowed_values:
            raise ProjectPolicyError(
                f"{action} enum control {item.name} must declare allowed values."
            )
        if (
            item.default is not None
            and item.allowed_values
            and item.default not in item.allowed_values
        ):
            raise ProjectPolicyError(
                f"{action} control {item.name} default is not an allowed value."
            )
        for allowed in item.allowed_values:
            _validate_control_value(action, item, allowed, "allowed value", adapter)
        if (
            (item.minimum is not None or item.maximum is not None)
            and item.control_type not in {"integer", "number"}
        ):
            raise ProjectPolicyError(
                f"{action} control {item.name} declares a range for a non-numeric type."
            )
        if item.minimum is not None and item.maximum is not None and item.minimum > item.maximum:
            raise ProjectPolicyError(f"{action} control {item.name} has an inverted range.")
        if item.selection_tags and not set(item.selection_tags).issubset(SELECTION_TAG_GLOSSARY):
            unknown = sorted(set(item.selection_tags) - set(SELECTION_TAG_GLOSSARY))
            raise ProjectPolicyError(f"{action} control {item.name} uses unknown selection tags: {unknown}.")
    modeled = required | optional | {item.executor_argument for item in controls}
    unmodeled = executor_fields - modeled
    if unmodeled:
        raise ProjectPolicyError(
            f"{action} has executor arguments without an input or control declaration: "
            f"{sorted(unmodeled)}."
        )
    return converted


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
            code_groups = [list(group) for group in definition.required_input_groups]
            if spec.required_input_groups != code_groups:
                raise ProjectPolicyError(
                    f"{action} required_input_groups conflict with Python: "
                    f"yaml={spec.required_input_groups}, code={code_groups}."
                )
            unknown_group_fields = {
                field
                for group in spec.required_input_groups
                for field in group
                if field not in known_fields
            }
            if any(not group for group in spec.required_input_groups) or unknown_group_fields:
                raise ProjectPolicyError(
                    f"{action} has invalid required_input_groups: "
                    f"unknown={sorted(unknown_group_fields)}."
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
            _validate_controls(action, spec, definition, known_fields)
            output_capability = definition.output_capability
            if output_capability is None:
                raise ProjectPolicyError(f"{action} has no output capability definition.")
            unknown_tags = set(spec.output_capability.selection_tags) - set(SELECTION_TAG_GLOSSARY)
            if unknown_tags:
                raise ProjectPolicyError(
                    f"{action} uses unregistered selection tags: {sorted(unknown_tags)}."
                )
            referenced_controls = {item.name: item for item in spec.controls}
            seen_conditions: set[tuple[tuple[str, Any], ...]] = set()
            for conditional in spec.output_capability.conditional_outputs:
                undeclared_artifacts = set(conditional.produced_artifacts) - set(
                    spec.output_capability.produced_artifacts
                )
                if undeclared_artifacts:
                    raise ProjectPolicyError(
                        f"{action} conditional output references unregistered artifacts: "
                        f"{sorted(undeclared_artifacts)}."
                    )
                unknown_condition_controls = set(conditional.when) - set(referenced_controls)
                if unknown_condition_controls:
                    raise ProjectPolicyError(
                        f"{action} conditional output references unknown controls: "
                        f"{sorted(unknown_condition_controls)}."
                    )
                condition_key = tuple(
                    sorted((name, repr(value)) for name, value in conditional.when.items())
                )
                if condition_key in seen_conditions:
                    raise ProjectPolicyError(
                        f"{action} declares duplicate conditional output rules."
                    )
                seen_conditions.add(condition_key)
                for name, value in conditional.when.items():
                    control = referenced_controls[name]
                    _validate_control_value(
                        action,
                        control,
                        value,
                        f"conditional value for {name}",
                        TypeAdapter(TaskDecision.model_fields[name].annotation),
                    )
                if not conditional.valid and conditional.produced_artifacts:
                    raise ProjectPolicyError(
                        f"{action} invalid conditional output rules cannot produce artifacts."
                    )
            yaml_capability = OutputCapabilityDefinition(
                operation=spec.output_capability.operation,
                artifact_type=spec.output_capability.artifact_type,
                entity_types=frozenset(spec.output_capability.entity_types),
                granularities=frozenset(spec.output_capability.granularities),
                accepted_input_modalities=frozenset(
                    spec.output_capability.accepted_input_modalities
                ),
                guidance_notes=tuple(spec.output_capability.guidance_notes),
                accepted_input_granularities=frozenset(
                    spec.output_capability.accepted_input_granularities
                ),
                produced_artifacts=frozenset(
                    spec.output_capability.produced_artifacts
                ),
                transformations=frozenset(spec.output_capability.transformations),
                scientific_objectives=frozenset(
                    spec.output_capability.scientific_objectives
                ),
                incompatible_input_artifacts=frozenset(
                    spec.output_capability.incompatible_input_artifacts
                ),
                selection_phrases=tuple(spec.output_capability.selection_phrases),
                regulator_types=frozenset(spec.output_capability.regulator_types),
                target_types=frozenset(spec.output_capability.target_types),
                guidance_predecessors=tuple(
                    spec.output_capability.guidance_predecessors
                ),
                input_artifacts=frozenset(spec.output_capability.input_artifacts),
                # Required executor prerequisites are code-enforced registry
                # metadata, not provider outcome fields; keep them out of the
                # public policy schema while retaining the comparison here.
                required_input_artifacts=definition.output_capability.required_input_artifacts,
                handoff_targets=tuple(spec.output_capability.handoff_targets),
                selection_tags=frozenset(spec.output_capability.selection_tags),
                handoff_contract=spec.output_capability.handoff_contract,
                conditional_outputs=tuple(
                    _conditional_output_from_spec(item)
                    for item in spec.output_capability.conditional_outputs
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
