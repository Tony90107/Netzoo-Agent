"""Code-enforced workflow/action registry for the NetZoo harness.

The YAML workflow files remain independently validated policy data. This module
is the single Python source for action names, required inputs, validation steps,
executor arguments, and memory metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, get_args


ActionName = Literal[
    "no_tool",
    "inspect_inputs",
    "inspect_condor_inputs",
    "format_expression",
    "convert_expression",
    "run_panda",
    "run_puma",
    "run_lioness_panda",
    "run_lioness_puma",
    "run_lioness_coexpression",
    "run_condor",
    "discover_workspace_resources",
    "query_context7",
    "web_search",
]

RecommendedAction = Literal[
    "inspect_inputs",
    "inspect_condor_inputs",
    "format_expression",
    "convert_expression",
    "run_panda",
    "run_puma",
    "run_lioness_panda",
    "run_lioness_puma",
    "run_lioness_coexpression",
    "run_condor",
]

IntentType = Literal[
    "answer_question",
    "inspect_input",
    "prepare_input",
    "run_analysis",
    "demo_run",
    "unknown",
]

PreferenceKey = Literal[
    "default_output_dir",
    "allow_demo_autofill",
    "reuse_last_inputs",
    "preferred_workflow",
]

Operation = Literal[
    "acquire",
    "prepare",
    "validate",
    "infer",
    "analyze",
    "explain",
    "unknown",
]
ArtifactType = Literal[
    "measurement_dataset",
    "expression_matrix",
    "regulatory_network",
    "coexpression_network",
    "community_assignment",
    "validation_report",
    "unknown",
]
EntityType = Literal["tf", "mirna", "gene", "protein", "sample", "unknown"]
Granularity = Literal["aggregate", "sample_specific", "not_applicable", "unknown"]


@dataclass(frozen=True, slots=True)
class OutputCapabilityDefinition:
    operation: Literal["infer", "analyze"]
    artifact_type: ArtifactType
    entity_types: frozenset[EntityType]
    granularities: frozenset[Granularity]
    regulator_types: frozenset[Literal["tf", "mirna"]] = frozenset()
    target_types: frozenset[Literal["gene"]] = frozenset()
    guidance_predecessors: tuple[RecommendedAction, ...] = ()


@dataclass(frozen=True, slots=True)
class DiscoverySpec:
    """Registry-owned rules for finding one workflow's input resources."""

    input_roles: tuple[str, ...]
    filename_hints: Mapping[str, tuple[str, ...]]
    allowed_extensions: frozenset[str] = frozenset({".tsv", ".tab", ".txt", ".csv"})
    validator_ids: tuple[str, ...] = ()
    min_samples: int | None = None
    ranking_hints: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ActionDefinition:
    action: ActionName
    workflow: str
    required_inputs: tuple[str, ...] = ()
    optional_inputs: tuple[str, ...] = ()
    executor_fields: tuple[str, ...] = ()
    executor_defaults: Mapping[str, Any] = field(default_factory=dict)
    validation_steps: tuple[str, ...] = ()
    local: bool = False
    run: bool = False
    memory_metadata: Mapping[str, str] = field(default_factory=dict)
    output_capability: OutputCapabilityDefinition | None = None
    read_only: bool = False
    discovery: DiscoverySpec | None = None


ACTION_DEFINITIONS: dict[ActionName, ActionDefinition] = {
    "no_tool": ActionDefinition("no_tool", "NO-TOOL"),
    "inspect_inputs": ActionDefinition(
        "inspect_inputs",
        "INPUTS",
        required_inputs=("expression_file", "motif_file", "ppi_file"),
        executor_fields=("expression_file", "motif_file", "ppi_file", "mirna_file"),
        executor_defaults={"mirna_file": ""},
        local=True,
    ),
    "inspect_condor_inputs": ActionDefinition(
        "inspect_condor_inputs",
        "CONDOR-INPUTS",
        required_inputs=("network_file",),
        executor_fields=("network_file",),
        local=True,
    ),
    "format_expression": ActionDefinition(
        "format_expression",
        "FORMAT-EXPRESSION",
        required_inputs=("expression_file", "output_file"),
        executor_fields=(
            "expression_file",
            "output_file",
            "genes_axis",
            "with_header",
        ),
        local=True,
    ),
    "convert_expression": ActionDefinition(
        "convert_expression",
        "CONVERT-EXPRESSION",
        required_inputs=("expression_file", "output_file"),
        executor_fields=("expression_file", "output_file"),
        local=True,
    ),
    "run_panda": ActionDefinition(
        "run_panda",
        "PANDA",
        required_inputs=("expression_file", "motif_file", "ppi_file", "output_file"),
        optional_inputs=("with_header",),
        executor_fields=(
            "expression_file",
            "motif_file",
            "ppi_file",
            "output_file",
            "with_header",
        ),
        validation_steps=("inspect_inputs",),
        local=True,
        run=True,
        memory_metadata={"method_family": "panda"},
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=frozenset({"tf", "gene"}),
            regulator_types=frozenset({"tf"}),
            target_types=frozenset({"gene"}),
            granularities=frozenset({"aggregate"}),
        ),
        discovery=DiscoverySpec(
            input_roles=("expression_file", "motif_file", "ppi_file"),
            filename_hints={
                "expression_file": ("expression", "expr"),
                "motif_file": ("panda", "motif", "prior"),
                "ppi_file": ("ppi",),
            },
            validator_ids=("inspect_netzoo_inputs",),
        ),
    ),
    "run_puma": ActionDefinition(
        "run_puma",
        "PUMA",
        required_inputs=(
            "expression_file",
            "motif_file",
            "ppi_file",
            "mirna_file",
            "output_file",
        ),
        executor_fields=(
            "expression_file",
            "motif_file",
            "ppi_file",
            "mirna_file",
            "output_file",
        ),
        validation_steps=("inspect_inputs",),
        local=True,
        run=True,
        memory_metadata={"method_family": "puma"},
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=frozenset({"tf", "mirna", "gene"}),
            regulator_types=frozenset({"tf", "mirna"}),
            target_types=frozenset({"gene"}),
            granularities=frozenset({"aggregate"}),
        ),
        discovery=DiscoverySpec(
            input_roles=(
                "expression_file",
                "motif_file",
                "ppi_file",
                "mirna_file",
            ),
            filename_hints={
                "expression_file": ("expression", "expr"),
                "motif_file": ("puma", "motif", "prior"),
                "ppi_file": ("ppi",),
                "mirna_file": ("mirna", "mir"),
            },
            validator_ids=("inspect_netzoo_inputs",),
        ),
    ),
    "run_lioness_panda": ActionDefinition(
        "run_lioness_panda",
        "LIONESS-PANDA",
        required_inputs=(
            "expression_file",
            "motif_file",
            "ppi_file",
            "output_file",
            "lioness_output",
        ),
        executor_fields=(
            "expression_file",
            "motif_file",
            "ppi_file",
            "output_file",
            "lioness_output",
        ),
        validation_steps=("inspect_inputs",),
        local=True,
        run=True,
        memory_metadata={"method_family": "lioness", "base_method": "panda"},
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=frozenset({"tf", "gene"}),
            regulator_types=frozenset({"tf"}),
            target_types=frozenset({"gene"}),
            granularities=frozenset({"aggregate", "sample_specific"}),
            guidance_predecessors=("run_panda",),
        ),
        discovery=DiscoverySpec(
            input_roles=("expression_file", "motif_file", "ppi_file"),
            filename_hints={
                "expression_file": ("expression", "expr"),
                "motif_file": ("panda", "motif", "prior"),
                "ppi_file": ("ppi",),
            },
            validator_ids=("inspect_netzoo_inputs",),
            min_samples=3,
            ranking_hints=("lioness",),
        ),
    ),
    "run_lioness_puma": ActionDefinition(
        "run_lioness_puma",
        "LIONESS-PUMA",
        required_inputs=(
            "expression_file",
            "motif_file",
            "ppi_file",
            "mirna_file",
            "output_file",
            "lioness_output",
        ),
        executor_fields=(
            "expression_file",
            "motif_file",
            "ppi_file",
            "mirna_file",
            "output_file",
            "lioness_output",
        ),
        validation_steps=("inspect_inputs",),
        local=True,
        run=True,
        memory_metadata={"method_family": "lioness", "base_method": "puma"},
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=frozenset({"tf", "mirna", "gene"}),
            regulator_types=frozenset({"tf", "mirna"}),
            target_types=frozenset({"gene"}),
            granularities=frozenset({"aggregate", "sample_specific"}),
            guidance_predecessors=("run_puma",),
        ),
        discovery=DiscoverySpec(
            input_roles=(
                "expression_file",
                "motif_file",
                "ppi_file",
                "mirna_file",
            ),
            filename_hints={
                "expression_file": ("expression", "expr"),
                "motif_file": ("puma", "motif", "prior"),
                "ppi_file": ("ppi",),
                "mirna_file": ("mirna", "mir"),
            },
            validator_ids=("inspect_netzoo_inputs",),
            min_samples=3,
            ranking_hints=("lioness",),
        ),
    ),
    "run_lioness_coexpression": ActionDefinition(
        "run_lioness_coexpression",
        "LIONESS-COEXPRESSION",
        required_inputs=("expression_file", "output_file", "lioness_output"),
        executor_fields=("expression_file", "output_file", "lioness_output"),
        local=True,
        run=True,
        memory_metadata={
            "method_family": "lioness",
            "base_method": "coexpression",
        },
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="coexpression_network",
            entity_types=frozenset({"gene"}),
            granularities=frozenset({"aggregate", "sample_specific"}),
        ),
        discovery=DiscoverySpec(
            input_roles=("expression_file",),
            filename_hints={"expression_file": ("expression", "expr")},
            validator_ids=("inspect_expression",),
            min_samples=3,
            ranking_hints=("lioness",),
        ),
    ),
    "run_condor": ActionDefinition(
        "run_condor",
        "CONDOR",
        required_inputs=("network_file", "output_dir"),
        optional_inputs=("prefix",),
        executor_fields=("network_file", "output_dir", "prefix"),
        executor_defaults={"prefix": "condor"},
        validation_steps=("inspect_condor_inputs",),
        local=True,
        run=True,
        memory_metadata={"method_family": "condor"},
        output_capability=OutputCapabilityDefinition(
            operation="analyze",
            artifact_type="community_assignment",
            entity_types=frozenset({"gene"}),
            granularities=frozenset({"not_applicable"}),
        ),
        discovery=DiscoverySpec(
            input_roles=("network_file",),
            filename_hints={"network_file": ("condor", "bipartite", "network")},
            validator_ids=("inspect_condor_inputs",),
        ),
    ),
    "discover_workspace_resources": ActionDefinition(
        "discover_workspace_resources",
        "WORKSPACE-RESOURCES",
        required_inputs=("workspace_root",),
        executor_fields=("workspace_root", "resource_subpath", "resource_actions"),
        read_only=True,
    ),
    "query_context7": ActionDefinition(
        "query_context7",
        "CONTEXT7",
        required_inputs=("library_name", "docs_query"),
        executor_fields=("library_name", "docs_query", "library_id"),
    ),
    "web_search": ActionDefinition(
        "web_search",
        "WEB-SEARCH",
        required_inputs=("web_query",),
        executor_fields=("web_query",),
    ),
}

ACTION_NAMES = frozenset(get_args(ActionName))
READ_ONLY_ACTIONS = frozenset(
    action for action, definition in ACTION_DEFINITIONS.items() if definition.read_only
)
DISCOVERABLE_ACTIONS = tuple(
    action for action, definition in ACTION_DEFINITIONS.items() if definition.discovery is not None
)
PROFILE_PREFERENCE_KEYS = frozenset(get_args(PreferenceKey))
REQUIRED_INPUTS = {
    action: definition.required_inputs
    for action, definition in ACTION_DEFINITIONS.items()
    if definition.required_inputs
}
RUN_ACTIONS = frozenset(
    action for action, definition in ACTION_DEFINITIONS.items() if definition.run
)
LOCAL_WORKFLOW_ACTIONS = frozenset(
    action for action, definition in ACTION_DEFINITIONS.items() if definition.local
)
LOCAL_EXECUTION_ACTIONS = LOCAL_WORKFLOW_ACTIONS | READ_ONLY_ACTIONS
CODE_VALIDATION_STEPS = {
    action: list(ACTION_DEFINITIONS[action].validation_steps) for action in RUN_ACTIONS
}
WORKFLOW_MEMORY_METADATA = {
    action: dict(ACTION_DEFINITIONS[action].memory_metadata) for action in RUN_ACTIONS
}
OUTPUT_CAPABILITIES = {
    action: definition.output_capability
    for action, definition in ACTION_DEFINITIONS.items()
    if definition.run and definition.output_capability is not None
}


def workflow_name(action: str) -> str:
    definition = ACTION_DEFINITIONS.get(action)
    if definition is not None:
        return definition.workflow
    return (
        action.removeprefix("run_").removeprefix("inspect_").replace("_", "-").upper()
    )


def executor_arguments(action: ActionName, decision: Any) -> dict[str, Any]:
    """Build the allow-listed executor payload for one typed decision."""
    definition = ACTION_DEFINITIONS[action]
    arguments = {}
    for field_name in definition.executor_fields:
        value = getattr(decision, field_name, None)
        if value in (None, "") and field_name in definition.executor_defaults:
            value = definition.executor_defaults[field_name]
        arguments[field_name] = value
    return arguments
