## S137

Request (turn 1): We have expression, motifs and PPI from 75 tumors. We want each TF's activity in each tumor and a signed TF-gene regulatory matrix.

Requirements to judge (in the user's words):
R1: "each TF's activity in each tumor"
R2: "a signed TF-gene regulatory matrix"

Reply:

````
What I understood you are asking for:
1. "each TF's activity in each tumor" -- available from GIRAFFE.
2. "a signed TF-gene regulatory matrix" -- available from GIRAFFE.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Your request can be read 2 ways, and they lead to different workflows.
- question: Which reading should we start with?
- option: Reading 1: “We want each TF's activity in each tumor” — GIRAFFE: a cohort-level TF activity matrix · Also estimates per-sample TF activity and signed activating/repressing effects
- option: Reading 2: “a signed TF-gene regulatory matrix.” — GIRAFFE: a cohort-level signed regulatory-effect network · Also estimates per-sample TF activity and signed activating/repressing effects
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S138

Request (turn 1): We have expression, TF motifs and PPI from 70 samples and want a regulatory network.
Request (turn 2): Our regulators also include miRNAs, with predicted target sites.

Requirements to judge (in the user's words):
R1: "Our regulators also include miRNAs"

Reply:

````
Routing matched these registered workflows to your words, but the capability check found no result in your request to check them against, so none is confirmed to give what you asked for:
- **PUMA** — produces: One weighted network of how TFs and miRNAs regulate genes, across all samples.

Compare what each produces with what you asked for, or describe the result you want from your data and it is checked against what each workflow produces.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check found no result in your request to check them against.
- point: Compare what each produces with what you asked for; describing the result you want has it checked.
- point: Your request names only a miRNA list; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior and a PPI network?
- option: Only a miRNA list — Ask what the data you named can give instead
- option: I also have a motif prior and a PPI network — Continues with the workflows this reply names
- next step: Start a new task

## S139

Request (turn 1): We have expression from 40 samples and want a gene co-expression network for each sample.
Request (turn 2): These are single cells, not tissue samples: 40 individual cells.

Requirements to judge (in the user's words):
R1: "These are single cells, not tissue samples"

Reply:

````
I could not tell which registered result you are asking for, so no workflow is offered for it.

If a registered workflow should give part of it, describe that result from your data, and it is checked against what the workflows produce.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Your request was not mapped to a result any registered workflow produces, so no workflow is offered.
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task

## S140

Request (turn 1): When is a Gaussian graphical model better than plain correlation for linking two omics layers?

Requirements to judge (in the user's words):
(none: this request asks about methods; give `R: []`)
Judge `consult` for this session.

Reply:

````
Selected path: **DRAGON**.

Your question asks for a cohort-level multi-omic network. **DRAGON** fits that result and scale.

**DRAGON** — Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Outputs:

- `multi_omic_network`: Inferred associations between omics features.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: DRAGON fits your goal: cohort-level multi-omic network.
- point: Method: Partial-correlation network across two omics layers of the same samples.
- point: Needs: omics layer 1, omics layer 2.
- point: Produces: multi-omic network (one cohort-level result).
- next step: Plan DRAGON with my data
- next step: Start a new task

## S141

Request (turn 1): We have expression, motifs and PPI from 90 tumors. Which method tells, for each TF-gene edge, whether the TF activates or represses that gene in each individual tumor?

Requirements to judge (in the user's words):
R1: "whether the TF activates or represses that gene in each individual tumor"

Reply:

````
What I understood you are asking for:
1. "Which method tells, for each TF-gene edge, whether the TF activates or represses that gene in each individual tumor?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Which method tells, for each TF-gene edge, whether the TF activates or… — Not matched to any registered workflow.
- next step: Start a new task

## S142

Request (turn 1): Why does OTTER need a PPI network as well as expression data?

Requirements to judge (in the user's words):
(none: this request asks about methods; give `R: []`)
Judge `consult` for this session.

Reply:

````
OTTER: Infer an aggregate TF-to-gene regulatory network with OTTER by solving a continuous-relaxation graph-matching optimization with an explicit objective and gamma regularization that balances motif/PPI priors with co-expression constraints.
Registered required inputs: motif_file, ppi_file, output_file.
Registered workflow controls: output_format (type=enum, default='matrix'), computing (type=enum, default='cpu'), precision (type=enum, default='double'), lam (type=number, default=0.035), gamma (type=number, default=0.335), iterations (type=integer, default=60), eta (type=number, default=1e-05), bexp (type=number, default=1.0).
Output: aggregate TF-to-gene regulatory networks.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 
- next step: Start a new task

## S143

Request (turn 1): We have expression and methylation from 80 patients at two visits. Is there a method that captures how methylation at the first visit drives expression at the second visit?

Requirements to judge (in the user's words):
R1: "captures how methylation at the first visit drives expression at the second visit"

Reply:

````
What I understood you are asking for:
1. "Is there a method that captures how methylation at the first visit drives expression at the second visit?" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Is there a method that captures how methylation at the first visit drives… — Every registered workflow estimates associations or model coefficients from observational data.
- next step: Start a new task

## S144

Request (turn 1): We have expression and methylation from 90 samples. We want the cross-layer network and the causal direction of each link.

Requirements to judge (in the user's words):
R1: "the cross-layer network"
R2: "the causal direction of each link"

Reply:

````
What I understood you are asking for:
1. "cross-layer network" -- available from DRAGON.
2. "causal direction of each link" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

About "the causal direction of each link": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

Selected path: **DRAGON**.

Your question asks for a cohort-level multi-omic network. **DRAGON** fits that result and scale.

**DRAGON** — Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Outputs:

- `multi_omic_network`: Inferred associations between omics features.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: DRAGON fits your goal: cohort-level multi-omic network.
- point: Method: Partial-correlation network across two omics layers of the same samples.
- point: Needs: omics layer 1, omics layer 2.
- point: Produces: multi-omic network (one cohort-level result).
- not available: “causal direction of each link” — Every registered workflow estimates associations or model coefficients from observational data.
- not available: Show that one thing causes another — Registered workflows estimate associations; they can describe what changes, not prove its cause.
- next step: Plan DRAGON with my data
- next step: Start a new task

## S145

Request (turn 1): We have a bipartite TF-gene network from PANDA. Is there a method that lets a TF belong to more than one module at the same time?

Requirements to judge (in the user's words):
R1: "lets a TF belong to more than one module at the same time"

Reply:

````
What I understood you are asking for:
1. "Is there a method that lets a TF belong to more than one module at the same time?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Is there a method that lets a TF belong to more than one module at the same… — Not matched to any registered workflow.
- next step: Start a new task

## S146

Request (turn 1): We have expression and methylation from 90 matched samples and want a network linking them.
Request (turn 2): We also need a p-value for each edge.

Requirements to judge (in the user's words):
R1: "a p-value for each edge"

Reply:

````
What I understood you are asking for:
1. "We also need a p-value for each edge." -- available from DRAGON.

Fallback recommendation: **BONOBO**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a p-value matrix. **BONOBO** is related to that result. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression.

What you asked about:

- "We also need a p-value for each edge." — With `sparsify=true` BONOBO computes a p-value for every connection in every sample and keeps those with a two-sided p-value below `bonobo_confidence` (default 0.05), without multiple-testing correction. With `save_pvals=true` as well, the full network is kept and the p-values are saved beside it instead.

**BONOBO**: Infer sample-specific gene-gene co-expression networks with netZooPy BONOBO.

Routing-level input modality: expression matrix.

Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices.

BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

Required workflow inputs:

- `expression_file`: expression matrix

Controls matching this request:

- `sparsify` (type=boolean; default=False)
- `bonobo_confidence` (type=number; default=0.05; range=0.0..1.0)
- `save_pvals` (type=boolean; default=False)

Other declared controls (not matched to this request; defaults apply unless you set them): `bonobo_output_format`=.h5, `sample_names`=[], `precision`=single, `keep_in_memory`=False, `delta`, `genes_axis`=auto, `log_transformed`, `centered`.

When `sparsify=False` and `save_pvals=False`: full sample-specific gene-gene co-expression matrices; no p-value artifact is written.

When `sparsify=True` and `save_pvals=False`: upstream thresholds each sample-specific co-expression matrix; no p-value artifact is written.

When `sparsify=True` and `save_pvals=True`: upstream retains the full co-expression matrix for each selected sample and writes a matching p-value matrix; threshold it from the saved p-value matrix; it does not also emit an already-thresholded network in this mode.

Distinct declared output artifacts (availability depends on workflow options):

- `coexpression_network`: Inferred gene-to-gene associations.
- `pvalue_matrix`: P-value matrix paired with a sample-specific gene-gene co-expression result.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: BONOBO is the closest registered match, but it is not a verified match for your request.
- point: Method: Per-sample co-expression with Bayesian shrinkage and a p-value per edge.
- point: Needs: expression matrix.
- point: Produces: co-expression network and p-value matrix (one per sample).
- next step: Start a new task

## S147

Request (turn 1): What is the difference between a per-sample regulatory network and a cohort network?

Requirements to judge (in the user's words):
(none: this request asks about methods; give `R: []`)
Judge `consult` for this session.

Reply:

````
I can map this to more than one compatible network result:

All of them derive each sample network from all-sample and leave-one-out networks, and iteratively exchange information across biological evidence networks.

**TF-only regulatory network**
- **LIONESS-PANDA** — Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **LIONESS-PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

**What your data allows.** LIONESS-PANDA also needs an expression matrix, a motif prior and a PPI network; LIONESS-PUMA also needs an expression matrix, a motif prior, a PPI network and a miRNA list. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered workflows fit; one detail about your study decides between them.
- point: Understood goal: a per-sample regulatory network.
- point: Your request names only the data I described; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior and a PPI network?
- option: Only the data I described — Ask what the data you named can give instead
- option: I also have a motif prior and a PPI network — Continues with the workflows this reply names
- next step: Start a new task

## S148

Request (turn 1): We have somatic mutations from 250 tumors. We want patient subtypes from pathway mutation scores and a comparison of survival between the subtypes.

Requirements to judge (in the user's words):
R1: "patient subtypes from pathway mutation scores"
R2: "a comparison of survival between the subtypes"

Reply:

````
What I understood you are asking for:
1. "patient subtypes from pathway mutation scores" -- available from SAMBAR.
2. "comparison of survival between the subtypes" -- available from SAMBAR's output plus a step you run outside NetZoo: A test outside NetZoo with a clinical table keyed by sample ID.

Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

Why this recommendation:

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

**SAMBAR** — Subtype somatic-mutation samples through pathway mutation scores with SAMBAR. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

Required workflow inputs:

- `mutation_file`: somatic mutation matrix
- `exon_size_file`: gene/exon-size CSV
- `cancer_gene_file`: cancer-gene list
- `pathway_file`: GMT pathway file

Outputs:

- `gene_mutation_scores`: Sample-by-gene mutation scores, not pathway scores.
- `pathway_mutation_matrix`: Pathway-by-sample mutation scores, not cluster labels.
- `sample_cluster_assignment`: Sample-to-cluster labels, separate from score and distance matrices.
- `sample_distance_matrix`: Pairwise sample distances, not cluster labels.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: SAMBAR fits your goal: cohort-level set of sample subtypes.
- point: Method: Pathway-level mutation scores, then patient subtypes by clustering.
- point: Needs: somatic mutation matrix, gene-length CSV, cancer-gene list, GMT pathway file.
- point: Produces: gene mutation score matrix, pathway mutation score matrix, set of sample subtypes and sample distance matrix (one cohort-level result).
- next step: Plan SAMBAR with my data
- next step: Start a new task

## S149

Request (turn 1): We have expression, motifs and PPI from 65 patients. We want a TF-gene network for each patient and also the network for the whole cohort.

Requirements to judge (in the user's words):
R1: "a TF-gene network for each patient"
R2: "the network for the whole cohort"

Reply:

````
What I understood you are asking for:
1. "a TF-gene network for each patient" -- available from LIONESS-PANDA.
2. "the network for the whole cohort" -- available from PANDA, OTTER or LIONESS-PANDA.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “TF-gene network for each patient”:

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

For “network for the whole cohort”:

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

For “network for the whole cohort”:

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
````

Card shown with the reply:
- headline: You described 2 approaches; 3 registered workflows fit them.
- question: Which hypothesis should we start with?
- option: LIONESS-PANDA — For “TF-gene network for each patient” · One TF-gene network per sample, derived leave-one-out from the cohort
- option: PANDA — For “network for the whole cohort” · Widely used baseline: message passing over motif, PPI and co-expression evidence
- option: OTTER — For “network for the whole cohort” · Explicit objective (graph matching), fitted by a fixed number of gradient steps; lighter on memory
- next step: Start a new task

## S150

Request (turn 1): We have expression with batch and sex recorded for 120 samples. Is there a method that separates how much of each gene pair's co-expression comes from each covariate?

Requirements to judge (in the user's words):
R1: "separates how much of each gene pair's co-expression comes from each covariate"

Reply:

````
What I understood you are asking for:
1. "Is there a method that separates how much of each gene pair's co-expression comes from each covariate?" -- available from COBRA.

Selected path: **COBRA**.

Your question asks for a co-expression network. **COBRA** fits that result.

**COBRA** — Model covariate-associated gene co-expression with COBRA. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: COBRA fits your goal: co-expression network.
- point: Picked from 3 fitting methods because you wrote “separates how much of each gene pair's…”; LIONESS-COEXPRESSION and BONOBO also fit.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- next step: Compare with LIONESS-COEXPRESSION and BONOBO
- next step: Plan COBRA with my data
- next step: Start a new task

## S151

Request (turn 1): We have expression from 2,000 single cells plus TF motifs and PPI. Is there a method that infers a regulatory network for each individual cell?

Requirements to judge (in the user's words):
R1: "infers a regulatory network for each individual cell"

Reply:

````
What I understood you are asking for:
1. "infers a regulatory network for each individual cell" -- not available here: no registered workflow produces this. LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “infers a regulatory network for each individual cell” — LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task

## S152

Request (turn 1): We have expression and metabolomics from 110 matched samples. We want a network linking the two layers and an adjusted significance value for each link.

Requirements to judge (in the user's words):
R1: "a network linking the two layers"
R2: "an adjusted significance value for each link"

Reply:

````
What I understood you are asking for:
1. "a network linking the two layers" -- available from DRAGON.
2. "an adjusted significance value for each link" -- available from DRAGON.

Selected path: **DRAGON**.

Your question asks for a cohort-level multi-omic network. **DRAGON** fits that result and scale.

**DRAGON** — Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Outputs:

- `multi_omic_network`: Inferred associations between omics features.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: DRAGON fits your goal: cohort-level multi-omic network.
- point: Method: Partial-correlation network across two omics layers of the same samples.
- point: Needs: omics layer 1, omics layer 2.
- point: Produces: multi-omic network (one cohort-level result).
- next step: Plan DRAGON with my data
- next step: Start a new task

## S153

Request (turn 1): How does PANDA combine the motif prior with the PPI network?

Requirements to judge (in the user's words):
(none: this request asks about methods; give `R: []`)
Judge `consult` for this session.

Reply:

````
Yes, in principle, data can weaken an unreliable TF-binding prior and quantify uncertainty about it, but only if the model explicitly represents that uncertainty. A hierarchical Bayesian model can treat binding-site predictions as noisy evidence about latent TF-gene edges, with a source-reliability parameter and an expression-data likelihood. Conflicting evidence can lower posterior edge support; learning the source's reliability itself also requires an identifiable model and informative data, potentially including independent binding evidence or multiple priors. A Bayesian label alone does not supply this model.

No qualified registered workflow fully matches the requested modeling philosophy.

Outside this agent (reference only; it cannot run these):
- **TIGER** (netZooR, R) — Bayesian matrix factorization of expression with a prior TF-gene network and TF activities; sparse edge priors let the data shrink unsupported prior edges, one edge at a time. Chen & Padi 2024, doi:10.1038/s41540-024-00386-w.
- **Werhli & Husmeier (2007)** (published method, no NetZoo implementation) — Bayesian networks that give each prior-knowledge source its own weight, sampled by MCMC, so the data decide how much each prior counts. PMID 17542777.

A registered method with that philosophy estimates a different result:
- **BONOBO** — declared output: co-expression networks and matching p-value matrices (one per sample). BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

If you relax that requirement, these registered approaches can infer the requested network through different assumptions:

PANDA and OTTER tie only on the stated output and scope. This does not show that they are equally robust to a noisy motif prior; neither estimates its reliability as a posterior probability.

1. **PANDA** — Iterative message passing reconciles the motif seed with TF-TF interactions and gene co-expression, repeatedly revising TF-gene edge support across those networks. The edge weights summarize integrated evidence, not a posterior probability that the motif prior is reliable.

2. **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

For the probabilistic reliability estimate you asked for, the hierarchical model above remains the recommendation. If stable network scores would suffice instead, perturb or replace the motif prior and compare inferred edges against independent evidence. Neither algorithm is known from the stated facts to be more robust for your study.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow implements the bayesian approach you asked for.
- point: Understood goal: a regulatory network.
- point: The registered alternatives do not fulfil the requested modeling requirement.
- question: Would one of these, without that requirement, work for you?
- option: PANDA — Widely used baseline: message passing over motif, PPI and co-expression evidence
- option: OTTER — Explicit objective (graph matching), fitted by a fixed number of gradient steps; lighter on memory
- not available: TIGER — Not runnable here (netZooR, R); Chen & Padi 2024, doi:10.1038/s41540-024-00386-w.
- not available: Werhli & Husmeier (2007) — Not runnable here (published method, no NetZoo implementation); PMID 17542777.
- next step: Start a new task

## S154

Request (turn 1): We have expression and metabolomics from 110 matched samples. We want a network linking the two layers and an adjusted significance value for each link.

Requirements to judge (in the user's words):
R1: "a network linking the two layers"
R2: "an adjusted significance value for each link"

Reply:

````
What I understood you are asking for:
1. "a network linking the two layers" -- available from DRAGON.
2. "an adjusted significance value for each link" -- available from DRAGON.

Selected path: **DRAGON**.

Your question asks for a cohort-level multi-omic network. **DRAGON** fits that result and scale.

**DRAGON** — Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Outputs:

- `multi_omic_network`: Inferred associations between omics features.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: DRAGON fits your goal: cohort-level multi-omic network.
- point: Method: Partial-correlation network across two omics layers of the same samples.
- point: Needs: omics layer 1, omics layer 2.
- point: Produces: multi-omic network (one cohort-level result).
- next step: Plan DRAGON with my data
- next step: Start a new task

## S155

Request (turn 1): We have a TF-gene network from PANDA. Which method groups the TFs and genes into modules by maximizing bipartite modularity?

Requirements to judge (in the user's words):
R1: "groups the TFs and genes into modules by maximizing bipartite modularity"

Reply:

````
What I understood you are asking for:
1. "Which method groups the TFs and genes into modules by maximizing bipartite modularity?" -- available from CONDOR.

Selected path: **CONDOR**.

Your question asks for a cohort-level community assignment. **CONDOR** fits that result and scale.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: CONDOR fits your goal: cohort-level set of network communities (modules).
- point: Method: Finds TF-gene communities (modules) in a two-mode network.
- point: Needs: TF-gene (bipartite) network.
- point: Before running: threshold a PANDA or LIONESS network so its edge weights are non-negative; CONDOR then gives each node one community and a core score.
- point: Produces: set of network communities (modules) (one cohort-level result).
- next step: Plan CONDOR with my data
- next step: Start a new task

## S156

Request (turn 1): We have expression from 100 samples with age recorded. We want the co-expression adjusted for age and a list of genes differentially expressed with age.

Requirements to judge (in the user's words):
R1: "the co-expression adjusted for age"
R2: "a list of genes differentially expressed with age"

Reply:

````
What I understood you are asking for:
1. "the co-expression adjusted for age" -- available from COBRA.
2. "a list of genes differentially expressed with age" -- not available here: no registered workflow produces this. COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.

Assumptions behind this recommendation (not confirmed facts):

- The expression data is suitable for co-expression analysis.
- Age is a relevant covariate for the analysis.

Selected path: **COBRA**.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale.

**COBRA** — Model covariate-associated gene co-expression with COBRA. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: COBRA fits your goal: cohort-level co-expression network.
- point: Picked from 2 fitting methods because you wrote “co-expression adjusted for age”; LIONESS-COEXPRESSION also fit.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- not available: “a list of genes differentially expressed with age” — COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.
- next step: Compare with LIONESS-COEXPRESSION
- next step: Plan COBRA with my data
- next step: Start a new task

## S157

Request (turn 1): We have a bipartite TF-gene network and want its modules.
Request (turn 2): Each TF should be allowed to belong to several modules.

Requirements to judge (in the user's words):
R1: "Each TF should be allowed to belong to several modules"

Reply:

````
What I understood you are asking for:
1. "Each TF should be allowed to belong to several modules." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Each TF should be allowed to belong to several modules.” — Not matched to any registered workflow.
- next step: Start a new task

## S158

Request (turn 1): We have expression, motifs and PPI from 50 samples and want a TF-gene network.
Request (turn 2): Actually we need it to say whether each TF activates or represses each target, separately in every sample.

Requirements to judge (in the user's words):
R1: "whether each TF activates or represses each target, separately in every sample"

Reply:

````
What I understood you are asking for:
1. "whether each TF activates or represses each target, separately in every sample" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “whether each TF activates or represses each target, separately in every sample” — Not matched to any registered workflow.
- next step: Start a new task

## S159

Request (turn 1): We have expression, TF motifs and PPI from 70 samples and want a regulatory network.
Request (turn 2): Our regulators also include miRNAs, with predicted target sites.

Requirements to judge (in the user's words):
R1: "Our regulators also include miRNAs"

Reply:

````
Routing matched these registered workflows to your words, but the capability check found no result in your request to check them against, so none is confirmed to give what you asked for:
- **PUMA** — produces: One weighted network of how TFs and miRNAs regulate genes, across all samples.
- **LIONESS-PUMA** — produces: One TF/miRNA-gene network per sample, plus the aggregate network.

Compare what each produces with what you asked for, or describe the result you want from your data and it is checked against what each workflow produces.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check found no result in your request to check them against.
- point: Compare what each produces with what you asked for; describing the result you want has it checked.
- point: Your request names only a miRNA list; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior and a PPI network?
- option: Only a miRNA list — Ask what the data you named can give instead
- option: I also have a motif prior and a PPI network — Continues with the workflows this reply names
- next step: Start a new task

## S160

Request (turn 1): We have expression from 2,000 single cells plus TF motifs and PPI. Is there a method that infers a regulatory network for each individual cell?

Requirements to judge (in the user's words):
R1: "infers a regulatory network for each individual cell"

Reply:

````
What I understood you are asking for:
1. "infers a regulatory network for each individual cell" -- not available here: no registered workflow produces this. LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “infers a regulatory network for each individual cell” — LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task

## S161

Request (turn 1): We have expression, motifs and PPI from 90 tumors. Which method tells, for each TF-gene edge, whether the TF activates or represses that gene in each individual tumor?

Requirements to judge (in the user's words):
R1: "whether the TF activates or represses that gene in each individual tumor"

Reply:

````
What I understood you are asking for:
1. "for each TF-gene edge, whether the TF activates or represses that gene in each individual tumor" -- not available here: no registered workflow produces this. PANDA does not give it: edge weights are unsigned support scores.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “for each TF-gene edge, whether the TF activates or represses that gene in… — PANDA does not give it: edge weights are unsigned support scores.
- next step: Start a new task

## S162

Request (turn 1): We have expression from 2,000 single cells plus TF motifs and PPI. Is there a method that infers a regulatory network for each individual cell?

Requirements to judge (in the user's words):
R1: "infers a regulatory network for each individual cell"

Reply:

````
What I understood you are asking for:
1. "infers a regulatory network for each individual cell" -- not available here: no registered workflow produces this. LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “infers a regulatory network for each individual cell” — LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task

## S163

Request (turn 1): We have expression and methylation from 90 samples. We want the cross-layer network and the causal direction of each link.

Requirements to judge (in the user's words):
R1: "the cross-layer network"
R2: "the causal direction of each link"

Reply:

````
What I understood you are asking for:
1. "the cross-layer network" -- available from DRAGON.
2. "the causal direction of each link" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

About "the causal direction of each link": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

Selected path: **DRAGON**.

Your question asks for a cohort-level multi-omic network. **DRAGON** fits that result and scale.

**DRAGON** — Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Outputs:

- `multi_omic_network`: Inferred associations between omics features.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: DRAGON fits your goal: cohort-level multi-omic network.
- point: Method: Partial-correlation network across two omics layers of the same samples.
- point: Needs: omics layer 1, omics layer 2.
- point: Produces: multi-omic network (one cohort-level result).
- not available: “the causal direction of each link” — Every registered workflow estimates associations or model coefficients from observational data.
- not available: Show that one thing causes another — Registered workflows estimate associations; they can describe what changes, not prove its cause.
- next step: Plan DRAGON with my data
- next step: Start a new task

## S164

Request (turn 1): How do bipartite community methods decide which genes are core to a module?

Requirements to judge (in the user's words):
(none: this request asks about methods; give `R: []`)
Judge `consult` for this session.

Reply:

````
Selected path: **CONDOR**.

Your question asks for a cohort-level community assignment. **CONDOR** fits that result and scale.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: CONDOR fits your goal: cohort-level set of network communities (modules).
- point: Method: Finds TF-gene communities (modules) in a two-mode network.
- point: Needs: TF-gene (bipartite) network.
- point: Before running: threshold a PANDA or LIONESS network so its edge weights are non-negative; CONDOR then gives each node one community and a core score.
- point: Produces: set of network communities (modules) (one cohort-level result).
- next step: Plan CONDOR with my data
- next step: Start a new task

## S165

Request (turn 1): We have spatial transcriptomics of 3,000 spots with motifs and PPI. Which method models how each spot's regulatory network is shaped by the networks of its neighbouring spots?

Requirements to judge (in the user's words):
R1: "models how each spot's regulatory network is shaped by the networks of its neighbouring spots"

Reply:

````
What I understood you are asking for:
1. "models how each spot's regulatory network is shaped by the networks of its neighbouring spots" -- not available here: no registered workflow produces this. OTTER does not give it: no per-sample OTTER is registered.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “models how each spot's regulatory network is shaped by the networks of its… — OTTER does not give it: no per-sample OTTER is registered.
- next step: Start a new task

## S166

Request (turn 1): We have RNA-seq from 70 liver samples plus TF motifs and PPI. Is there a method that weighs how strongly each TF regulates each gene by reconciling the motif prior with co-expression and protein interactions?

Requirements to judge (in the user's words):
R1: "weighs how strongly each TF regulates each gene by reconciling the motif prior with co-expression and protein interactions"

Reply:

````
What I understood you are asking for:
1. "weighs how strongly each TF regulates each gene by reconciling the motif prior with co-expression and protein interactions" -- available from PANDA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 4 registered methods can build a TF-gene regulatory network; they differ in scale (one network for all samples or one per sample) and in their modeling assumptions.
- point: Understood goal: a TF-gene regulatory network from expression data, a motif prior and a PPI network.
- point: Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and GIRAFFE give one across all samples.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: LIONESS-PANDA — One TF-gene network per sample, plus the cohort network · Lets you compare samples, or relate them to outcomes such as survival · Slower: it reruns PANDA once per sample
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- next step: Start a new task

## S167

Request (turn 1): We have expression, TF motifs and PPI from 70 samples and want a regulatory network.
Request (turn 2): Our regulators also include miRNAs, with predicted target sites.

Requirements to judge (in the user's words):
R1: "Our regulators also include miRNAs"

Reply:

````
I can map this to more than one compatible network result:

- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Should the result be aggregate or sample-specific?

**What your data allows.** Your request names only a miRNA list. PUMA and LIONESS-PUMA also need an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered workflows fit; one detail about your study decides between them.
- point: Understood goal: a miRNA-gene regulatory network.
- point: Your request names only a miRNA list; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior and a PPI network?
- option: Only a miRNA list — Ask what the data you named can give instead
- option: I also have a motif prior and a PPI network — Continues with the workflows this reply names
- next step: Start a new task

## S168

Request (turn 1): We have expression and methylation from 90 matched samples and want a network linking them.
Request (turn 2): We also need a p-value for each edge.

Requirements to judge (in the user's words):
R1: "a p-value for each edge"

Reply:

````
What I understood you are asking for:
1. "a p-value for each edge" -- available from DRAGON.

Fallback recommendation: **BONOBO**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a p-value matrix. **BONOBO** is related to that result. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression.

What you asked about:

- "We also need a p-value for each edge." — With `sparsify=true` BONOBO computes a p-value for every connection in every sample and keeps those with a two-sided p-value below `bonobo_confidence` (default 0.05), without multiple-testing correction. With `save_pvals=true` as well, the full network is kept and the p-values are saved beside it instead.

**BONOBO**: Infer sample-specific gene-gene co-expression networks with netZooPy BONOBO.

Routing-level input modality: expression matrix.

Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices.

BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

Required workflow inputs:

- `expression_file`: expression matrix

Controls matching this request:

- `sparsify` (type=boolean; default=False)
- `bonobo_confidence` (type=number; default=0.05; range=0.0..1.0)
- `save_pvals` (type=boolean; default=False)

Other declared controls (not matched to this request; defaults apply unless you set them): `bonobo_output_format`=.h5, `sample_names`=[], `precision`=single, `keep_in_memory`=False, `delta`, `genes_axis`=auto, `log_transformed`, `centered`.

When `sparsify=False` and `save_pvals=False`: full sample-specific gene-gene co-expression matrices; no p-value artifact is written.

When `sparsify=True` and `save_pvals=False`: upstream thresholds each sample-specific co-expression matrix; no p-value artifact is written.

When `sparsify=True` and `save_pvals=True`: upstream retains the full co-expression matrix for each selected sample and writes a matching p-value matrix; threshold it from the saved p-value matrix; it does not also emit an already-thresholded network in this mode.

Distinct declared output artifacts (availability depends on workflow options):

- `coexpression_network`: Inferred gene-to-gene associations.
- `pvalue_matrix`: P-value matrix paired with a sample-specific gene-gene co-expression result.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: BONOBO is the closest registered match, but it is not a verified match for your request.
- point: Method: Per-sample co-expression with Bayesian shrinkage and a p-value per edge.
- point: Needs: expression matrix.
- point: Produces: co-expression network and p-value matrix (one per sample).
- next step: Start a new task

## S169

Request (turn 1): We have a bipartite TF-gene network and want its modules.
Request (turn 2): Each TF should be allowed to belong to several modules.

Requirements to judge (in the user's words):
R1: "Each TF should be allowed to belong to several modules"

Reply:

````
What I understood you are asking for:
1. "Each TF should be allowed to belong to several modules." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Each TF should be allowed to belong to several modules.” — Not matched to any registered workflow.
- next step: Start a new task

## S170

Request (turn 1): We have a bipartite TF-gene network. We want its modules and the pathways enriched in each module.

Requirements to judge (in the user's words):
R1: "its modules"
R2: "the pathways enriched in each module"

Reply:

````
What I understood you are asking for:
1. "its modules" -- available from CONDOR.
2. "the pathways enriched in each module" -- available from CONDOR's output plus a step you run outside NetZoo: A gene-set tool outside NetZoo.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “modules”:

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

For “pathways enriched in each module”:

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

For “pathways enriched in each module”:

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
````

Card shown with the reply:
- headline: You described 2 approaches; 3 registered workflows fit them.
- question: Which hypothesis should we start with?
- option: CONDOR — For “modules” · Finds TF-gene communities (modules) in a two-mode network
- option: DRAGON — For “pathways enriched in each module” · Partial-correlation network across two omics layers of the same samples
- option: LIONESS-DRAGON — For “pathways enriched in each module” · One two-layer partial-correlation network per sample, derived leave-one-out
- next step: Start a new task
