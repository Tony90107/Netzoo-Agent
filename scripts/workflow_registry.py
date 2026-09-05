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
    "inspect_sambar_inputs",
    "inspect_dragon_inputs",
    "inspect_otter_inputs",
    "inspect_giraffe_inputs",
    "inspect_bonobo_inputs",
    "format_expression",
    "convert_expression",
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
    "run_sambar",
    "run_dragon",
    "run_otter",
    "run_giraffe",
    "run_bonobo",
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
    "mutation_matrix",
    "pathway_mutation_matrix",
    "gene_mutation_scores",
    "sample_distance_matrix",
    "sample_cluster_assignment",
    "community_assignment",
    "validation_report",
    "multi_omic_network",
    "unknown",
]
InputModality = Literal[
    "gene_expression",
    "somatic_mutation",
    "coexpression",
    "regulatory_network",
    "multi_omic_continuous",
    "unknown",
]
EntityType = Literal[
    "tf", "mirna", "gene", "protein", "sample", "pathway",
    "omics_layer_1_feature", "omics_layer_2_feature", "unknown",
]
Granularity = Literal["aggregate", "sample_specific", "not_applicable", "unknown"]


@dataclass(frozen=True, slots=True)
class OutputCapabilityDefinition:
    operation: Literal["infer", "analyze"]
    artifact_type: ArtifactType
    entity_types: frozenset[EntityType]
    granularities: frozenset[Granularity]
    accepted_input_modalities: frozenset[InputModality] = frozenset()
    produced_artifacts: frozenset[ArtifactType] = frozenset()
    transformations: frozenset[str] = frozenset()
    scientific_objectives: frozenset[str] = frozenset()
    incompatible_input_artifacts: frozenset[ArtifactType] = frozenset()
    selection_phrases: tuple[str, ...] = ()
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
    cli_command: str | None = None
    handoff_cli_commands: Mapping[str, str] = field(default_factory=dict)
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
    "inspect_sambar_inputs": ActionDefinition(
        "inspect_sambar_inputs",
        "SAMBAR-INPUTS",
        required_inputs=("mutation_file", "exon_size_file", "cancer_gene_file", "pathway_file"),
        executor_fields=("mutation_file", "exon_size_file", "cancer_gene_file", "pathway_file", "kmin", "kmax", "cluster"),
        local=True,
    ),
    "inspect_dragon_inputs": ActionDefinition(
        "inspect_dragon_inputs",
        "DRAGON-INPUTS",
        required_inputs=("omics_layer_1", "omics_layer_2"),
        executor_fields=("omics_layer_1", "omics_layer_2"),
        local=True,
    ),
    "inspect_otter_inputs": ActionDefinition(
        "inspect_otter_inputs",
        "OTTER-INPUTS",
        required_inputs=("motif_file", "ppi_file"),
        optional_inputs=("expression_file", "coexpression_file"),
        executor_fields=(
            "expression_file", "coexpression_file", "motif_file", "ppi_file", "precision",
        ),
        local=True,
    ),
    "inspect_giraffe_inputs": ActionDefinition(
        "inspect_giraffe_inputs",
        "GIRAFFE-INPUTS",
        required_inputs=("expression_file", "motif_file", "ppi_file"),
        executor_fields=("expression_file", "motif_file", "ppi_file"),
        local=True,
    ),
    "inspect_bonobo_inputs": ActionDefinition(
        "inspect_bonobo_inputs",
        "BONOBO-INPUTS",
        required_inputs=("expression_file",),
        optional_inputs=(
            "output_dir", "bonobo_output_format", "sample_names", "sparsify",
            "bonobo_confidence", "save_pvals", "genes_axis", "log_transformed", "centered",
        ),
        executor_fields=(
            "expression_file", "output_dir", "bonobo_output_format", "sample_names",
            "sparsify", "bonobo_confidence", "save_pvals", "genes_axis", "log_transformed", "centered",
        ),
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
        optional_inputs=("with_header", "coexpression_file"),
        executor_fields=(
            "expression_file",
            "motif_file",
            "ppi_file",
            "output_file",
            "with_header",
            "coexpression_file",
        ),
        validation_steps=("inspect_inputs",),
        local=True,
        run=True,
        memory_metadata={"method_family": "panda"},
        cli_command="run-panda",
        handoff_cli_commands={"coexpression_file": "run-panda-precomputed"},
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=frozenset({"tf", "gene"}),
            regulator_types=frozenset({"tf"}),
            target_types=frozenset({"gene"}),
            granularities=frozenset({"aggregate"}),
            accepted_input_modalities=frozenset(
                {"gene_expression", "coexpression"}
            ),
            produced_artifacts=frozenset({"regulatory_network"}),
            incompatible_input_artifacts=frozenset({"mutation_matrix"}),
            input_artifacts=frozenset({"expression_matrix", "coexpression_network"}),
            handoff_targets=("run_condor",),
            selection_tags=frozenset({"tf_gene_regulation", "aggregate_network"}),
            handoff_contract=(
                "PANDA consumes a gene-by-sample expression matrix plus motif and "
                "PPI priors, or a validated adjusted gene-by-gene co-expression "
                "matrix through coexpression_file. When supplied, the adjusted matrix "
                "replaces PANDA's Pearson co-expression construction while the expression "
                "file remains the gene-order and prior compatibility source. PANDA "
                "produces a weighted TF-to-gene regulatory network. "
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
            "coexpression_file",
        ),
        optional_inputs=("coexpression_file",),
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
            accepted_input_modalities=frozenset(
                {"gene_expression", "coexpression"}
            ),
            produced_artifacts=frozenset({"regulatory_network"}),
            incompatible_input_artifacts=frozenset({"mutation_matrix"}),
            input_artifacts=frozenset({"expression_matrix", "coexpression_network"}),
            handoff_targets=("run_condor",),
            selection_tags=frozenset({"mirna_regulation", "aggregate_network"}),
            handoff_contract=(
                "PUMA consumes a gene-by-sample expression matrix plus motif, PPI, "
                "and miRNA priors, or a validated adjusted gene-by-gene co-expression "
                "matrix through coexpression_file. When supplied, the adjusted matrix "
                "replaces PUMA's Pearson co-expression construction. PUMA produces "
                "a weighted regulator-to-gene network. "
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
            accepted_input_modalities=frozenset({"gene_expression"}),
            produced_artifacts=frozenset({"regulatory_network"}),
            incompatible_input_artifacts=frozenset({"mutation_matrix"}),
            guidance_predecessors=("run_panda",),
            input_artifacts=frozenset({"expression_matrix"}),
            selection_tags=frozenset({"sample_specific", "tf_gene_regulation"}),
            handoff_contract=(
                "LIONESS-PANDA uses the original gene-by-sample expression matrix, "
                "motif and PPI priors to internally infer the aggregate PANDA "
                "network and derive sample-specific TF-to-gene networks. The PANDA "
                "predecessor is a guidance prerequisite, not a direct file handoff."
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
            accepted_input_modalities=frozenset({"gene_expression"}),
            produced_artifacts=frozenset({"regulatory_network"}),
            incompatible_input_artifacts=frozenset({"mutation_matrix"}),
            guidance_predecessors=("run_puma",),
            input_artifacts=frozenset({"expression_matrix"}),
            selection_tags=frozenset({"sample_specific", "mirna_regulation"}),
            handoff_contract=(
                "LIONESS-PUMA uses the original gene-by-sample expression matrix, "
                "motif, PPI, and miRNA priors to internally infer the aggregate PUMA "
                "network and derive sample-specific TF/miRNA-to-gene networks. The "
                "PUMA predecessor is a guidance prerequisite, not a direct file handoff."
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
            accepted_input_modalities=frozenset({"gene_expression"}),
            produced_artifacts=frozenset({"coexpression_network"}),
            incompatible_input_artifacts=frozenset({"mutation_matrix"}),
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
        cli_command="run-cobra",
        output_capability=OutputCapabilityDefinition(
            operation="analyze",
            artifact_type="coexpression_network",
            entity_types=frozenset({"gene"}),
            granularities=frozenset({"aggregate"}),
            input_artifacts=frozenset({"expression_matrix"}),
            handoff_targets=("run_panda", "run_puma", "run_otter"),
            selection_tags=frozenset(
                {
                    "covariate_association",
                    "hospital_effect_assessment",
                    "sequencing_batch_effect_assessment",
                    "batch_correction",
                    "high_order_correlation",
                }
            ),
            handoff_contract=(
                "COBRA consumes a gene-by-sample expression matrix and numeric sample "
                "covariates, then produces a covariate-associated covariance "
                "decomposition and a labeled adjusted gene-by-gene co-expression "
                "artifact. PANDA, PUMA, or OTTER may consume the adjusted artifact "
                "through coexpression_file only after the downstream identifier/order "
                "contract is revalidated; the raw components are not a matrix input "
                "by themselves."
            ),
        ),
    ),
    "run_sambar": ActionDefinition(
        "run_sambar",
        "SAMBAR",
        required_inputs=(
            "mutation_file",
            "exon_size_file",
            "cancer_gene_file",
            "pathway_file",
            "output_dir",
        ),
        optional_inputs=(
            "norm_patient",
            "kmin",
            "kmax",
            "gmt_msigdb",
            "subset_cancer_genes",
            "distance",
            "linkage",
            "cluster",
        ),
        executor_fields=(
            "mutation_file",
            "exon_size_file",
            "cancer_gene_file",
            "pathway_file",
            "output_dir",
            "norm_patient",
            "kmin",
            "kmax",
            "gmt_msigdb",
            "subset_cancer_genes",
            "distance",
            "linkage",
            "cluster",
        ),
        executor_defaults={
            "norm_patient": True,
            "kmin": 2,
            "kmax": 4,
            "gmt_msigdb": True,
            "subset_cancer_genes": True,
            "distance": "binomial",
            "linkage": "complete",
            "cluster": True,
        },
        validation_steps=("inspect_sambar_inputs",),
        local=True,
        run=True,
        memory_metadata={"method_family": "sambar"},
        output_capability=OutputCapabilityDefinition(
            operation="analyze",
            artifact_type="pathway_mutation_matrix",
            entity_types=frozenset({"sample", "gene", "pathway"}),
            granularities=frozenset({"aggregate"}),
            accepted_input_modalities=frozenset({"somatic_mutation"}),
            produced_artifacts=frozenset(
                {
                    "gene_mutation_scores",
                    "pathway_mutation_matrix",
                    "sample_cluster_assignment",
                    "sample_distance_matrix",
                }
            ),
            transformations=frozenset(
                {
                    "gene_length_normalization",
                    "patient_mutation_burden_normalization",
                    "pathway_aggregation",
                    "sample_distance",
                    "sample_clustering",
                }
            ),
            scientific_objectives=frozenset({"cancer_subtyping"}),
            incompatible_input_artifacts=frozenset({"expression_matrix"}),
            selection_phrases=(
                "somatic mutation",
                "tumor mutation burden",
                "gene length",
                "pathway score",
                "sparse mutation",
                "patient clustering",
                "體細胞突變",
                "突變負荷",
                "基因長度",
                "途徑分數",
                "生物途徑",
                "稀疏",
                "病患分群",
                "亞型分群",
            ),
            input_artifacts=frozenset({"mutation_matrix"}),
            selection_tags=frozenset({"somatic_mutation", "cancer_subtyping", "pathway_scores"}),
            handoff_contract=(
                "SAMBAR consumes a samples-by-genes somatic mutation CSV, a gene-length "
                "CSV, a tab-delimited cancer-gene list, and a GMT pathway file. It produces "
                "gene and pathway mutation-score matrices plus optional sample cluster labels. "
                "These are not direct inputs to PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, "
                "CONDOR, or COBRA; prepare and validate that workflow's declared input "
                "artifact separately before any composition."
            ),
        ),
    ),
    "run_dragon": ActionDefinition(
        "run_dragon",
        "DRAGON",
        required_inputs=("omics_layer_1", "omics_layer_2", "output_file"),
        optional_inputs=("output_format", "lambda1", "lambda2"),
        executor_fields=(
            "omics_layer_1", "omics_layer_2", "output_file",
            "output_format", "lambda1", "lambda2",
        ),
        executor_defaults={"output_format": "matrix"},
        validation_steps=("inspect_dragon_inputs",),
        local=True,
        run=True,
        memory_metadata={"method_family": "dragon", "api": "netZooPy.dragon"},
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="multi_omic_network",
            entity_types=frozenset({"omics_layer_1_feature", "omics_layer_2_feature"}),
            granularities=frozenset({"aggregate"}),
            input_artifacts=frozenset({"measurement_dataset"}),
            selection_tags=frozenset({"multi_omic_network", "partial_correlation", "aggregate_network"}),
            handoff_contract=(
                "DRAGON consumes exactly two paired sample-by-feature continuous omics tables "
                "and produces one aggregate undirected multi-omic network. The matrix is a "
                "symmetric partial-correlation GGM with layer-qualified node IDs; edge lists "
                "contain source, target, partial_correlation, and precision. This is an "
                "association network, not a causal graph. There is no direct handoff to PANDA, "
                "PUMA, LIONESS, CONDOR, BONOBO, or OTTER; a separate validated conversion would "
                "be required before any tool that consumes a different artifact contract."
            ),
        ),
    ),
    "run_otter": ActionDefinition(
        "run_otter",
        "OTTER",
        required_inputs=("motif_file", "ppi_file", "output_file"),
        optional_inputs=(
            "expression_file", "coexpression_file", "output_format", "computing",
            "precision", "lam", "gamma", "iterations", "eta", "bexp",
        ),
        executor_fields=(
            "expression_file", "coexpression_file", "motif_file", "ppi_file", "output_file",
            "output_format", "computing", "precision", "lam", "gamma", "iterations", "eta", "bexp",
        ),
        validation_steps=("inspect_otter_inputs",),
        local=True,
        run=True,
        memory_metadata={"method_family": "otter", "api": "netZooPy.otter.otter"},
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=frozenset({"tf", "gene"}),
            regulator_types=frozenset({"tf"}),
            target_types=frozenset({"gene"}),
            granularities=frozenset({"aggregate"}),
            guidance_predecessors=(),
            input_artifacts=frozenset({"expression_matrix", "coexpression_network"}),
            handoff_targets=("run_condor",),
            selection_tags=frozenset({"tf_gene_regulation", "aggregate_network", "relaxed_graph_matching"}),
            handoff_contract=(
                "OTTER consumes an OTTER seed/prior TF-by-gene edge list W, a TF-TF PPI "
                "projection P, and either a gene-by-sample expression matrix (from which "
                "C is computed) or a validated labeled gene-by-gene co-expression matrix. "
                "Its lam parameter weights co-expression versus PPI as (lam, 1-lam), and "
                "gamma is the verified regularization parameter. It produces an aggregate "
                "TF-to-gene network whose edge weight is the optimized OTTER W score. "
                "PPI and co-expression are never PANDA motif priors. Only a validated "
                "source-target-weight edge-list export with disjoint regulator/target IDs "
                "may be handed to CONDOR; a matrix export needs an explicit conversion."
            ),
        ),
    ),
    "run_giraffe": ActionDefinition(
        "run_giraffe",
        "GIRAFFE",
        required_inputs=("expression_file", "motif_file", "ppi_file", "output_file"),
        executor_fields=("expression_file", "motif_file", "ppi_file", "output_file"),
        validation_steps=("inspect_giraffe_inputs",),
        local=True,
        run=True,
        memory_metadata={
            "method_family": "giraffe",
            "api": "netZooPy.giraffe.Giraffe",
            "runtime": "docker",
            "netzoopy_version": "0.11.0",
        },
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=frozenset({"tf", "gene", "sample"}),
            regulator_types=frozenset({"tf"}),
            target_types=frozenset({"gene"}),
            # GIRAFFE returns an aggregate TF-gene regulation matrix plus a
            # TF-by-sample activity matrix; it does not return sample-specific
            # TF-gene networks.
            granularities=frozenset({"aggregate"}),
            input_artifacts=frozenset({"expression_matrix"}),
            handoff_targets=(),
            selection_tags=frozenset({"tf_gene_regulation", "tfa", "aggregate_network"}),
            handoff_contract=(
                "GIRAFFE consumes gene-by-sample expression, a TF-by-gene motif/prior, "
                "and a TF-by-TF PPI matrix after explicit labelled-file conversion. "
                "It produces an aggregate TF-by-gene regulation matrix and a TF-by-sample "
                "TFA matrix. GIRAFFE is not a direct CONDOR edge-list handoff; an "
                "explicit validated matrix-to-edge-list conversion and user confirmation "
                "are required before any downstream workflow. GIRAFFE has no direct "
                "handoff to PANDA, PUMA, LIONESS, SAMBAR, DRAGON, OTTER, BONOBO, COBRA, "
                "or CONDOR."
            ),
        ),
    ),
    "run_bonobo": ActionDefinition(
        "run_bonobo",
        "BONOBO",
        required_inputs=("expression_file", "output_dir"),
        optional_inputs=(
            "bonobo_output_format", "sample_names", "sparsify", "bonobo_confidence",
            "save_pvals", "precision", "keep_in_memory", "delta", "genes_axis",
            "log_transformed", "centered",
        ),
        executor_fields=(
            "expression_file", "output_dir", "bonobo_output_format", "sample_names",
            "sparsify", "bonobo_confidence", "save_pvals", "precision", "keep_in_memory",
            "delta", "genes_axis", "log_transformed", "centered",
        ),
        executor_defaults={
            "bonobo_output_format": ".h5",
            "sample_names": [],
            "sparsify": False,
            "bonobo_confidence": 0.05,
            "save_pvals": False,
            "precision": "single",
            "keep_in_memory": False,
            "genes_axis": "auto",
        },
        validation_steps=("inspect_bonobo_inputs",),
        local=True,
        run=True,
        memory_metadata={
            "method_family": "bonobo",
            "api": "netZooPy.bonobo.Bonobo.run_bonobo",
            "netzoopy_version": "0.11.0",
        },
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="coexpression_network",
            entity_types=frozenset({"gene", "sample"}),
            granularities=frozenset({"sample_specific"}),
            input_artifacts=frozenset({"expression_matrix"}),
            handoff_targets=(),
            selection_tags=frozenset({"sample_specific", "coexpression", "bayesian"}),
            handoff_contract=(
                "BONOBO consumes a labelled gene-by-sample expression matrix and "
                "produces one gene-by-gene sample-specific co-expression matrix per "
                "selected sample, plus optional matching p-value matrices. It does "
                "not produce an aggregate/prior network, GRN, TF-gene regulation, or "
                "causal network. BONOBO output is not a direct PANDA/PUMA "
                "coexpression_file handoff: those workflows require one validated "
                "aggregate labeled gene-by-gene matrix. A separate explicit "
                "sample-selection or aggregation conversion is required, with its "
                "own validation and user confirmation. It is not a direct handoff "
                "to LIONESS, CONDOR, COBRA, DRAGON, or OTTER either."
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


def _is_text_input(decision: Any, field_name: str) -> bool:
    """Report whether the typed decision declares this input as text."""
    fields = getattr(type(decision), "model_fields", None)
    field = fields.get(field_name) if isinstance(fields, dict) else None
    return field is None or "str" in str(field.annotation)


def executor_arguments(action: ActionName, decision: Any) -> dict[str, Any]:
    """Build the allow-listed executor payload for one typed decision."""
    definition = ACTION_DEFINITIONS[action]
    arguments = {}
    for field_name in definition.executor_fields:
        value = getattr(decision, field_name, None)
        if value in (None, "") and field_name in definition.executor_defaults:
            value = definition.executor_defaults[field_name]
        elif value is None and field_name in definition.optional_inputs:
            # Text adapters use an empty string to mean "optional input omitted",
            # because passing None leaks through their strict tool schema and turns
            # a valid plan preview into a ValidationError. A non-text optional is
            # declared `X | None` in the decision contract and its tool schema
            # rejects "", so it is omitted instead and inherits the adapter's own
            # meaning for an absent value, such as DRAGON estimating omitted
            # penalty parameters.
            if not _is_text_input(decision, field_name):
                continue
            value = ""
        arguments[field_name] = value
    return arguments
