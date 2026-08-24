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
    "inspect_cobra_inputs",
    "format_expression",
    "convert_expression",
    "run_panda",
    "run_puma",
    "run_lioness_panda",
    "run_lioness_puma",
    "run_lioness_coexpression",
    "run_condor",
    "run_cobra",
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
    "run_cobra",
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
    input_artifacts: frozenset[ArtifactType] = frozenset()
    handoff_targets: tuple[RecommendedAction, ...] = ()
    selection_tags: frozenset[str] = frozenset()
    handoff_contract: str = ""


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
    "inspect_cobra_inputs": ActionDefinition(
        "inspect_cobra_inputs",
        "COBRA-INPUTS",
        required_inputs=("expression_file", "design_file"),
        executor_fields=("expression_file", "design_file"),
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
            input_artifacts=frozenset({"expression_matrix"}),
            handoff_targets=("run_condor",),
            selection_tags=frozenset({"tf_gene_regulation", "aggregate_network"}),
            handoff_contract=(
                "PANDA consumes a gene-by-sample expression matrix plus motif and "
                "PPI priors, and produces a weighted TF-to-gene regulatory network. "
                "Convert that network to a source-target-weight bipartite edge list "
                "before handing it to CONDOR."
            ),
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
            input_artifacts=frozenset({"expression_matrix"}),
            handoff_targets=("run_condor",),
            selection_tags=frozenset({"mirna_regulation", "aggregate_network"}),
            handoff_contract=(
                "PUMA consumes a gene-by-sample expression matrix plus motif, PPI, "
                "and miRNA priors, and produces a weighted regulator-to-gene network. "
                "Convert that network to a source-target-weight bipartite edge list "
                "before handing it to CONDOR."
            ),
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
            input_artifacts=frozenset({"expression_matrix"}),
            selection_tags=frozenset({"sample_specific", "tf_gene_regulation"}),
            handoff_contract=(
                "LIONESS-PANDA uses the expression matrix and PANDA-compatible "
                "priors to derive sample-specific TF-to-gene networks."
            ),
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
            input_artifacts=frozenset({"expression_matrix"}),
            selection_tags=frozenset({"sample_specific", "mirna_regulation"}),
            handoff_contract=(
                "LIONESS-PUMA uses the expression matrix and PUMA-compatible "
                "priors to derive sample-specific TF/miRNA-to-gene networks."
            ),
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
            input_artifacts=frozenset({"expression_matrix"}),
            selection_tags=frozenset({"sample_specific", "coexpression"}),
            handoff_contract=(
                "LIONESS co-expression consumes a gene-by-sample expression matrix "
                "and produces sample-specific co-expression networks."
            ),
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
            input_artifacts=frozenset({"regulatory_network"}),
            selection_tags=frozenset({"bipartite_community_detection", "modules"}),
            handoff_contract=(
                "CONDOR consumes a weighted source-target bipartite edge list made "
                "from a validated regulator-gene network and returns community "
                "assignments with regulator-side and gene-side partitions."
            ),
        ),
    ),
    "run_cobra": ActionDefinition(
        "run_cobra",
        "COBRA",
        required_inputs=("expression_file", "design_file", "output_dir"),
        executor_fields=("expression_file", "design_file", "output_dir"),
        validation_steps=("inspect_cobra_inputs",),
        local=True,
        run=True,
        memory_metadata={"method_family": "cobra"},
        output_capability=OutputCapabilityDefinition(
            operation="analyze",
            artifact_type="coexpression_network",
            entity_types=frozenset({"gene"}),
            granularities=frozenset({"aggregate"}),
            input_artifacts=frozenset({"expression_matrix"}),
            handoff_targets=("run_panda",),
            selection_tags=frozenset(
                {
                    "covariate_association",
                    "hospital_effect_assessment",
                    "sequencing_batch_effect_assessment",
                }
            ),
            handoff_contract=(
                "COBRA consumes a gene-by-sample expression matrix and numeric sample "
                "covariates, then produces a covariate-associated covariance "
                "decomposition. This output is evidence for covariate handling, not "
                "a replacement expression matrix; PANDA must receive an independently "
                "prepared corrected gene-by-sample matrix."
            ),
        ),
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
LOCAL_EXECUTION_ACTIONS = LOCAL_WORKFLOW_ACTIONS
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


def registered_actions_for_family(family: str) -> tuple[ActionName, ...]:
    """Return registered runnable actions for a declared method family."""
    return tuple(
        action
        for action, definition in ACTION_DEFINITIONS.items()
        if definition.run and definition.memory_metadata.get("method_family") == family
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
