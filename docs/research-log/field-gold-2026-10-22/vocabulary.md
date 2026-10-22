# Registry vocabulary for field-gold labelling

Built by `vocabulary.py` from the registry (setting meanings, capability sheet, workflow YAMLs).

## Settings (`WORKFLOW.setting: what it does`)

- BONOBO.bonobo_output_format: File type of the per-sample matrices: .h5 or .hdf (HDF5), .txt or .csv.
- BONOBO.sample_names: Explicit sample IDs; never positional sample indices.
- BONOBO.sparsify: Compute approximate edge p-values and threshold each sample's co-expression matrix at bonobo_confidence (with save_pvals, the full matrix is kept and the p-values are written).
- BONOBO.bonobo_confidence: Significance level at which sparsify thresholds the edges.
- BONOBO.save_pvals: Write each sample's edge p-value matrix; requires sparsify.
- BONOBO.precision: Floating-point precision: single or double.
- BONOBO.keep_in_memory: Keep the per-sample matrices in memory during the run (upstream run_bonobo option).
- BONOBO.delta: Weight of the sample in its covariance; empty estimates it per sample. With sparsify it must be above 0 and below 1/3 (Log 224).
- BONOBO.genes_axis: Where the gene IDs are in the expression table: auto, rows or columns (BONOBO needs them on rows).
- BONOBO.log_transformed: The expression is declared log-transformed; BONOBO requires it.
- BONOBO.centered: The expression is declared centered; BONOBO requires it.
- CONDOR.prefix: Prefix for derived CONDOR artifacts.
- DRAGON.output_format: matrix: a labeled symmetric partial-correlation matrix; edge_list: one row per feature pair (source, target, partial_correlation, precision).
- DRAGON.lambda1: Shrinkage of omics layer 1 (DRAGON's layer-specific shrinkage, not a generic graphical-lasso or sparsity penalty). Empty estimates it; a manual value needs lambda1 and lambda2 together, both in [0, 1].
- DRAGON.lambda2: Shrinkage of omics layer 2 (DRAGON's layer-specific shrinkage, not a generic graphical-lasso or sparsity penalty). Empty estimates it; a manual value needs lambda1 and lambda2 together, both in [0, 1].
- LIONESS-DRAGON.lambda1: Shrinkage of omics layer 1 (DRAGON's layer-specific shrinkage, not a generic graphical-lasso or sparsity penalty). Empty estimates it once on all samples; a manual value needs lambda1 and lambda2 together, both in [0, 1].
- LIONESS-DRAGON.lambda2: Shrinkage of omics layer 2 (DRAGON's layer-specific shrinkage, not a generic graphical-lasso or sparsity penalty). Empty estimates it once on all samples; a manual value needs lambda1 and lambda2 together, both in [0, 1].
- OTTER.output_format: matrix: a labeled TF-by-gene matrix; edge_list: a complete source,target,weight TF-to-gene grid.
- OTTER.computing: Hardware the optimization runs on: cpu or gpu.
- OTTER.precision: Floating-point precision of the optimization: single or double.
- OTTER.lam: Weight of gene co-expression versus the TF-TF PPI network in OTTER's fit, as (lam, 1 - lam); not a sparsity penalty.
- OTTER.gamma: L2-style regularization of the TF-gene matrix W; not a sparsity penalty or threshold.
- OTTER.iterations: Number of optimization iterations.
- OTTER.eta: Step size (learning rate) of OTTER's gradient optimization.
- OTTER.bexp: Exponent used in OTTER's optimization updates; it controls the optimization, not regularization.
- PANDA.with_header: Expression input has a header.
- SAMBAR.norm_patient: Normalize gene mutation scores by each patient's mutation burden.
- SAMBAR.kmin: Smallest number of sample subtypes (clusters) tried; at least 2.
- SAMBAR.kmax: Largest number of sample subtypes (clusters) tried; at least kmin and at most the number of samples.
- SAMBAR.gmt_msigdb: The pathway GMT file is in MSigDB format.
- SAMBAR.subset_cancer_genes: Score only the listed cancer-associated genes.
- SAMBAR.distance: Distance (a scipy metric name) between samples' pathway scores used for clustering.
- SAMBAR.linkage: Hierarchical-clustering linkage method (a scipy name).
- SAMBAR.cluster: Cluster samples into subtypes; false returns the mutation scores only.

## PRODUCES entries (results a registered workflow gives)

- `panda.tf_gene_network` (PANDA): One weighted TF-to-gene regulatory network across all the samples given.
- `panda.targeting_scores` (PANDA): Each TF's out-degree and each gene's in-degree (targeting scores) in that network.
- `panda.condition_comparison` (PANDA): Which edges or TF targeting scores differ between conditions.
- `puma.regulator_gene_network` (PUMA): One weighted network of how TFs and miRNAs regulate genes, across all samples.
- `puma.targeting_scores` (PUMA): Each regulator's out-degree and each gene's in-degree.
- `lioness_panda.per_sample_networks` (LIONESS-PANDA): One TF-gene network per sample, plus the aggregate network.
- `lioness_panda.per_sample_targeting` (LIONESS-PANDA): A TF-by-sample (or gene-by-sample) targeting-score matrix.
- `lioness_panda.association_tests` (LIONESS-PANDA): Edges or targeting scores tested between groups, paired time points, or against clinical variables (e.g. survival).
- `lioness_puma.per_sample_networks` (LIONESS-PUMA): One TF/miRNA-gene network per sample, plus the aggregate network.
- `lioness_puma.per_sample_targeting` (LIONESS-PUMA): A TF-by-sample (or gene-by-sample) targeting-score matrix.
- `lioness_puma.association_tests` (LIONESS-PUMA): Edges or targeting scores tested between groups, paired time points, or against clinical variables (e.g. survival).
- `otter.tf_gene_network` (OTTER): One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- `otter.targeting_scores` (OTTER): Each TF's out-degree and each gene's in-degree (targeting scores) in that network.
- `giraffe.signed_regulation` (GIRAFFE): A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples.
- `giraffe.tf_activity` (GIRAFFE): Each TF's activity in each sample, estimated apart from its own mRNA level.
- `giraffe.activity_tests` (GIRAFFE): TF activity tested between conditions or against clinical variables.
- `dragon.two_layer_network` (DRAGON): One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples.
- `dragon.edge_pvalues` (DRAGON): A p-value and a Benjamini-Hochberg adjusted p-value for every edge (adjusted within each layer and across the layers), to filter edges by significance.
- `dragon.group_comparison` (DRAGON): Cross-layer edges compared between groups.
- `lioness_dragon.per_sample_networks` (LIONESS-DRAGON): One two-layer partial-correlation network per sample, plus the aggregate.
- `lioness_dragon.association_tests` (LIONESS-DRAGON): Per-sample edges compared between groups or individuals.
- `lioness_coexpression.per_sample_networks` (LIONESS-COEXPRESSION): One gene-gene co-expression network per sample, plus the aggregate.
- `lioness_coexpression.comparisons` (LIONESS-COEXPRESSION): Per-sample gene degree or edge weights compared across samples or groups.
- `bonobo.per_sample_networks` (BONOBO): One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample.
- `cobra.covariate_components` (COBRA): The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix.
- `cobra.adjusted_input_to_regulation` (COBRA): A regulatory network built from batch-adjusted co-expression.
- `condor.communities` (CONDOR): Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity.
- `condor.core_scores` (CONDOR): Each regulator's and gene's core score -- its share of its community's modularity -- to pick out each community's core nodes.
- `condor.enrichment` (CONDOR): Pathway enrichment of each community's genes.
- `sambar.subtypes` (SAMBAR): Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them -- with the scores, the cluster labels and the sample distance matrix.
- `sambar.clinical_comparison` (SAMBAR): Subtypes compared with clinical variables such as survival.

## Near-miss entries (results a workflow does NOT give, and why)

- `panda.no_complexes` (PANDA): Which TFs physically form complexes, or complex stoichiometry. -- why not: The PPI network is an input of possible TF cooperation. PANDA refines a cooperativity matrix internally, but the executor does not save it, and it is not a measurement of physical complexes or stoichiometry.
- `panda.no_sign` (PANDA): Whether a TF activates or represses a gene. -- why not: Edge weights are unsigned support scores.
- `panda.no_motif_discovery` (PANDA): Discover a TF's binding motif or binding sites. -- why not: The motif prior is an input; PANDA never searches sequence.
- `panda.no_dynamics` (PANDA): A model of how expression or regulation evolves over time. -- why not: One static network per set of samples; time points can only be compared as separate networks.
- `puma.no_lncrna_cerna` (PUMA): lncRNA regulators, ceRNA or miRNA-sponge networks. -- why not: PUMA's non-TF regulators are miRNAs given by a target prior; it has no lncRNA layer and models no sponging.
- `puma.no_mirna_expression_use` (PUMA): miRNA-gene edges estimated from miRNA expression (e.g. anti-correlation). -- why not: The miRNA's own expression is not an input.
- `lioness.no_single_cell` (LIONESS-PANDA): Networks for individual cells. -- why not: Built for bulk samples; per-cell co-expression is dominated by dropout.
- `lioness_panda.no_sign` (LIONESS-PANDA): Whether a TF activates or represses a gene. -- why not: Edge weights are unsigned support scores.
- `lioness_panda.no_complexes` (LIONESS-PANDA): Which TFs physically form complexes, or complex stoichiometry. -- why not: The PPI network is an input of possible TF cooperation. PANDA refines a cooperativity matrix internally, but the executor does not save it, and it is not a measurement of physical complexes or stoichiometry.
- `lioness_puma.no_single_cell` (LIONESS-PUMA): Networks for individual cells. -- why not: Built for bulk samples; per-cell co-expression is dominated by dropout.
- `lioness_puma.no_lncrna_cerna` (LIONESS-PUMA): lncRNA regulators, ceRNA or miRNA-sponge networks. -- why not: PUMA's non-TF regulators are miRNAs given by a target prior; it has no lncRNA layer and models no sponging.
- `otter.no_per_sample` (OTTER): One network per sample. -- why not: No per-sample OTTER is registered.
- `otter.no_global_optimum` (OTTER): A convex or globally optimal solution. -- why not: Non-convex objective; netZooPy takes fixed gradient steps.
- `otter.no_complexes` (OTTER): Which TFs physically form complexes, or complex stoichiometry. -- why not: The PPI network is an input of possible TF cooperation. PANDA refines a cooperativity matrix internally, but the executor does not save it, and it is not a measurement of physical complexes or stoichiometry.
- `otter.no_sign` (OTTER): Whether a TF activates or represses a gene. -- why not: Edge weights are unsigned support scores.
- `giraffe.no_protein_level` (GIRAFFE): Measured TF protein abundance or binding occupancy. -- why not: Activity is inferred from expression and priors, not measured.
- `giraffe.no_per_sample_wiring` (GIRAFFE): A separate regulatory network for each sample. -- why not: The regulatory matrix is one for all samples; only activity is per sample.
- `dragon.no_flux_or_pathway_activity` (DRAGON): Metabolic flux, pathway activity or quantities derived from a biochemical model. -- why not: DRAGON returns associations between measured features; it has no stoichiometric or kinetic model.
- `dragon.no_more_layers` (DRAGON): Three or more omics layers in one model. -- why not: Two layers only.
- `lioness_dragon.no_pvalues` (LIONESS-DRAGON): Per-sample edge p-values. -- why not: LIONESS-DRAGON writes per-sample edge weights only; DRAGON's p-values are for the aggregate network.
- `lioness_dragon.no_flux_or_pathway_activity` (LIONESS-DRAGON): Metabolic flux, pathway activity or quantities derived from a biochemical model. -- why not: DRAGON returns associations between measured features; it has no stoichiometric or kinetic model.
- `lioness_dragon.no_single_cell` (LIONESS-DRAGON): Networks for individual cells. -- why not: Built for bulk samples; per-cell co-expression is dominated by dropout.
- `coexpression.no_regulation` (LIONESS-COEXPRESSION): Which regulator controls which gene, or edge direction. -- why not: Co-expression is undirected gene-gene similarity, with no regulator layer.
- `lioness_coexpression.no_single_cell` (LIONESS-COEXPRESSION): Networks for individual cells. -- why not: Built for bulk samples; per-cell co-expression is dominated by dropout.
- `bonobo.no_regulation` (BONOBO): Which regulator controls which gene, or edge direction. -- why not: Co-expression is undirected gene-gene similarity, with no regulator layer.
- `bonobo.no_single_cell` (BONOBO): Networks for individual cells. -- why not: Built for bulk samples; per-cell co-expression is dominated by dropout.
- `cobra.no_differential_expression` (COBRA): Differentially expressed genes, fold changes or p-values per gene. -- why not: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.
- `cobra.no_pair_significance` (COBRA): Which gene pairs differ significantly between groups. -- why not: Components are effect contributions; deciding significance is a separate analysis.
- `condor.no_two_network_comparison` (CONDOR): Differential module structure between two networks. -- why not: One network at a time.
- `condor.no_variant_mapping` (CONDOR): Fine-mapping causal variants, or variant effects on binding. -- why not: CONDOR partitions a given network; it does not test or fine-map variants (its original eQTL use takes eQTL associations as input).
- `sambar.no_expression_subtypes` (SAMBAR): Subtypes from expression, methylation or other non-mutation data. -- why not: SAMBAR's input is somatic mutations.
- `sambar.no_driver_calls` (SAMBAR): Which mutations are drivers, or mutation calling. -- why not: SAMBAR summarizes given mutation calls; it does not call or rank driver mutations.

## Registry-wide limits (no registered workflow gives these)

- `causal_proof`: Proof that one thing causes another (causal drivers, causal direction of an edge, ruling out confounding). -- why not: Every registered workflow estimates associations or model coefficients from observational data.
- `outcome_prediction`: A trained model that predicts an outcome, a future state or a perturbation effect, with its accuracy. -- why not: No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.
- `delivery`: Results sent, uploaded, published or shown to anyone outside the analysis (e-mail, a public or shared database or repository, a website, a dashboard or app). -- why not: Every registered workflow writes result files to the output folder you give; sending, uploading, publishing or showing them is done outside NetZoo.

## Input slots (data a workflow takes, from each YAML's required_inputs / optional_inputs)

- `expression_file`: required by BONOBO, COBRA, GIRAFFE, LIONESS-COEXPRESSION, LIONESS-PANDA, LIONESS-PUMA, PANDA, PUMA; optional for OTTER
- `design_file`: required by COBRA; optional for -
- `network_file`: required by CONDOR; optional for -
- `omics_layer_1`: required by DRAGON, LIONESS-DRAGON; optional for -
- `omics_layer_2`: required by DRAGON, LIONESS-DRAGON; optional for -
- `motif_file`: required by GIRAFFE, LIONESS-PANDA, LIONESS-PUMA, OTTER, PANDA, PUMA; optional for -
- `ppi_file`: required by GIRAFFE, LIONESS-PANDA, LIONESS-PUMA, OTTER, PANDA, PUMA; optional for -
- `mirna_file`: required by LIONESS-PUMA, PUMA; optional for -
- `coexpression_file`: required by -; optional for OTTER, PANDA, PUMA
- `mutation_file`: required by SAMBAR; optional for -
- `exon_size_file`: required by SAMBAR; optional for -
- `cancer_gene_file`: required by SAMBAR; optional for -
- `pathway_file`: required by SAMBAR; optional for -
