## S001

Request (turn 1): We have RNA, ATAC and methylation for 60 matched samples. We want a single partial-correlation model of all three.

Requirements to judge (in the user's words):
R1: "a single partial-correlation model of all three"

Reply:

````
What I understood you are asking for:
1. "a single partial-correlation model of all three" -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a single partial-correlation model of all three” — DRAGON does not give it: two layers only.
- next step: Start a new task

## S002

Request (turn 1): We have expression for 60 responders and 60 non-responders. We want a volcano plot of the genes differentially expressed between them.

Requirements to judge (in the user's words):
R1: "a volcano plot of the genes differentially expressed between them"

Reply:

````
What I understood you are asking for:
1. "We want a volcano plot of the genes differentially expressed between them." -- not available here: no registered workflow produces this. COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a volcano plot of the genes differentially expressed between them.” — COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.
- next step: Start a new task

## S003

Request (turn 1): We have expression, motifs and PPI for 110 samples. We want to know which TFs bind DNA together as heterodimers.

Requirements to judge (in the user's words):
R1: "which TFs bind DNA together as heterodimers"

Reply:

````
What I understood you are asking for:
1. "which TFs bind DNA together as heterodimers" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “which TFs bind DNA together as heterodimers” — Not matched to any registered workflow.
- next step: Start a new task

## S004

Request (turn 1): We have expression for 60 responders and 60 non-responders. We want a volcano plot of the genes differentially expressed between them.

Requirements to judge (in the user's words):
R1: "a volcano plot of the genes differentially expressed between them"

Reply:

````
What I understood you are asking for:
1. "a volcano plot of the genes differentially expressed between them" -- not available here: no registered workflow produces this. COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a volcano plot of the genes differentially expressed between them” — COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.
- next step: Start a new task

## S005

Request (turn 1): We want TF-gene networks per sample from expression, motifs and PPI of 44 samples, and the networks uploaded to a public repository for us.

Requirements to judge (in the user's words):
R1: "TF-gene networks per sample"
R2: "the networks uploaded to a public repository for us"

Reply:

````
What I understood you are asking for:
1. "TF-gene networks per sample" -- available from LIONESS-PANDA.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 44 samples, 45 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 44 samples, 45 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S006

Request (turn 1): We only have bulk RNA-seq of 12 patient biopsies. We want sample-specific gene co-expression networks with a p-value for each edge.

Requirements to judge (in the user's words):
R1: "sample-specific gene co-expression networks with a p-value for each edge"

Reply:

````
What I understood you are asking for:
1. "sample-specific gene co-expression networks with a p-value for each edge" -- available from BONOBO.

Selected path: **BONOBO**.

Your question asks for a per-sample co-expression network. **BONOBO** fits that result and scale. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression.

What you asked about:

- "we want sample-specific gene co-expression networks with a p-value for each edge." — With `sparsify=true` BONOBO computes a p-value for every connection in every sample and keeps those with a two-sided p-value below `bonobo_confidence` (default 0.05), without multiple-testing correction. With `save_pvals=true` as well, the full network is kept and the p-values are saved beside it instead.

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

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: BONOBO fits your goal: per-sample co-expression network.
- point: Picked from 2 fitting methods because you wrote “p-value for each edge”; LIONESS-COEXPRESSION also fit.
- point: Method: Per-sample co-expression with Bayesian shrinkage and a p-value per edge.
- point: Needs: expression matrix.
- point: Produces: co-expression network and p-value matrix (one per sample).
- next step: Compare with LIONESS-COEXPRESSION
- next step: Plan BONOBO with my data
- next step: Start a new task

## S007

Request (turn 1): We have expression, motifs and PPI for 70 patients. We want to know whether TF activity changes cause the target gene changes or the other way round.

Requirements to judge (in the user's words):
R1: "whether TF activity changes cause the target gene changes or the other way round"

Reply:

````
What I understood you are asking for:
1. "whether TF activity changes cause the target gene changes or the other way round" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “whether TF activity changes cause the target gene changes or the other way… — Every registered workflow estimates associations or model coefficients from observational data.
- next step: Start a new task

## S008

Request (turn 1): We have mutation calls for 190 ovarian tumors plus gene lengths, cancer genes and pathway sets. We want subtypes from pathway mutation scores.

Requirements to judge (in the user's words):
R1: "subtypes from pathway mutation scores"

Reply:

````
What I understood you are asking for:
1. "subtypes from pathway mutation scores" -- available from SAMBAR.

Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

Why this recommendation:

Gene length normalization addresses the greater opportunity for mutations in longer genes; gene/exon sizes are therefore required, not just the mutation matrix.

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: SAMBAR fits your goal: cohort-level set of sample subtypes.
- point: Method: Pathway-level mutation scores, then patient subtypes by clustering.
- point: Needs: somatic mutation matrix, gene-length CSV, cancer-gene list, GMT pathway file.
- point: Produces: gene mutation score matrix, pathway mutation score matrix, set of sample subtypes and sample distance matrix (one cohort-level result).
- next step: Plan SAMBAR with my data
- next step: Start a new task

## S009

Request (turn 1): We have expression for 120 samples. We want the sequence motifs enriched in the promoters of our co-expressed genes.

Requirements to judge (in the user's words):
R1: "the sequence motifs enriched in the promoters of our co-expressed genes"

Reply:

````
What I understood you are asking for:
1. "the sequence motifs enriched in the promoters of our co-expressed genes" -- not available here: no registered workflow produces this. PANDA does not give it: the motif prior is an input; PANDA never searches sequence.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “the sequence motifs enriched in the promoters of our co-expressed genes” — PANDA does not give it: the motif prior is an input; PANDA never searches sequence.
- next step: Start a new task

## S010

Request (turn 1): We have mutations, exon sizes, cancer genes and pathways for 210 tumors. We want mutation-based subtypes and their association with overall survival.

Requirements to judge (in the user's words):
R1: "mutation-based subtypes and their association with overall survival"

Reply:

````
What I understood you are asking for:
1. "mutation-based subtypes" -- available from SAMBAR.
2. "their association with overall survival" -- available from SAMBAR's output plus a step you run outside NetZoo: A test outside NetZoo with a clinical table keyed by sample ID.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Your request can be read 2 ways, and they lead to different workflows.
- question: Which reading should we start with?
- option: Reading 1: “mutation-based subtypes” — SAMBAR: a cohort-level set of sample subtypes · Pathway-level mutation scores, then patient subtypes by clustering
- option: Reading 2 — SAMBAR: a cohort-level sample distance matrix · Pathway-level mutation scores, then patient subtypes by clustering
- next step: Plan SAMBAR with my data
- next step: Start a new task

## S011

Request (turn 1): We only have bulk RNA-seq of 12 patient biopsies. We want sample-specific gene co-expression networks with a p-value for each edge.

Requirements to judge (in the user's words):
R1: "sample-specific gene co-expression networks with a p-value for each edge"

Reply:

````
What I understood you are asking for:
1. "sample-specific gene co-expression networks with a p-value for each edge" -- available from BONOBO.

Selected path: **BONOBO**.

Your question asks for a per-sample co-expression network. **BONOBO** fits that result and scale. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression.

What you asked about:

- "we want sample-specific gene co-expression networks with a p-value for each edge" — With `sparsify=true` BONOBO computes a p-value for every connection in every sample and keeps those with a two-sided p-value below `bonobo_confidence` (default 0.05), without multiple-testing correction. With `save_pvals=true` as well, the full network is kept and the p-values are saved beside it instead.

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

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: BONOBO fits your goal: per-sample co-expression network.
- point: Picked from 2 fitting methods because you wrote “p-value for each edge”; LIONESS-COEXPRESSION also fit.
- point: Method: Per-sample co-expression with Bayesian shrinkage and a p-value per edge.
- point: Needs: expression matrix.
- point: Produces: co-expression network and p-value matrix (one per sample).
- next step: Compare with LIONESS-COEXPRESSION
- next step: Plan BONOBO with my data
- next step: Start a new task

## S012

Request (turn 1): We want communities in our bipartite TF-gene network and a tree of sub-communities nested inside each.

Requirements to judge (in the user's words):
R1: "communities in our bipartite TF-gene network"
R2: "a tree of sub-communities nested inside each"

Reply:

````
What I understood you are asking for:
1. "communities in our bipartite TF-gene network" -- available from CONDOR.
2. "a tree of sub-communities nested inside each." -- not matched to any registered workflow.

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
- not available: “a tree of sub-communities nested inside each.” — Not matched to any registered workflow.
- next step: Plan CONDOR with my data
- next step: Start a new task

## S013

Request (turn 1): We want each TF's activity per sample from expression, motifs and PPI of 66 samples, and a model that predicts drug response from those activities.

Requirements to judge (in the user's words):
R1: "each TF's activity per sample"
R2: "a model that predicts drug response from those activities"

Reply:

````
What I understood you are asking for:
1. "each TF's activity per sample" -- available from GIRAFFE.
2. "a model that predicts drug response from those activities" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "a model that predicts drug response from those activities": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Selected path: **GIRAFFE**.

**GIRAFFE** — Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.
- `tf_activity_matrix`: Inferred transcription-factor-by-sample activity values.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: GIRAFFE produces a regulatory network and TF activity matrix (one cohort-level result).
- point: Method: Also estimates per-sample TF activity and signed activating/repressing effects.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Produces: regulatory network and TF activity matrix (one cohort-level result).
- not available: “a model that predicts drug response from those activities” — No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.
- not available: Predict outcomes for new samples — No registered workflow builds a predictive model; per-sample results can only be its features.
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S014

Request (turn 1): We want qPCR primers designed for 15 target genes of our network.

Requirements to judge (in the user's words):
R1: "qPCR primers designed for 15 target genes"

Reply:

````
What I understood you are asking for:
1. "qPCR primers designed for 15 target genes of our network" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “qPCR primers designed for 15 target genes of our network” — Not matched to any registered workflow.
- next step: Start a new task

## S015

Request (turn 1): We want a co-expression network per sample for our 80 samples.
Request (turn 2): The 80 samples are cells from a single 10x run.

Requirements to judge (in the user's words):
R1: "The 80 samples are cells from a single 10x run"

Reply:

````
What I understood you are asking for:
1. "a co-expression network per sample" -- available from LIONESS-COEXPRESSION or BONOBO.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "80 samples". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered methods can build a per-sample co-expression network; they differ in their modeling assumptions.
- point: Understood goal: a per-sample co-expression network.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: LIONESS-COEXPRESSION — One gene co-expression network per sample, from expression data alone · Pick it if you have dozens of samples or more
- option: BONOBO — One gene co-expression network per sample, with a p-value for each connection · Pick it if you have only a handful of samples or you need a p-value for each edge
- next step: Start a new task

## S016

Request (turn 1): We have expression at 6 time points after infection, with motifs and PPI. We want the lagged regulatory effect of each TF from one time point on its targets at the next.

Requirements to judge (in the user's words):
R1: "the lagged regulatory effect of each TF from one time point on its targets at the next"

Reply:

````
What I understood you are asking for:
1. "the lagged regulatory effect of each TF from one time point on its targets at the next" -- not available here: no registered workflow produces this. PANDA does not give it: one static network per set of samples; time points can only be compared as separate networks.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “the lagged regulatory effect of each TF from one time point on its targets at… — PANDA does not give it: one static network per set of samples; time points can only be compared as separate networks.
- next step: Start a new task

## S017

Request (turn 1): We have expression for 100 cases and 100 controls. We want the gene pairs whose co-expression differs significantly between them, with p-values.

Requirements to judge (in the user's words):
R1: "the gene pairs whose co-expression differs significantly between them, with p-values"

Reply:

````
What I understood you are asking for:
1. "the gene pairs whose co-expression differs significantly between them, with p-values" -- not available here: no registered workflow produces this. COBRA does not give it: components are effect contributions; deciding significance is a separate analysis.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “the gene pairs whose co-expression differs significantly between them, with… — COBRA does not give it: components are effect contributions; deciding significance is a separate analysis.
- next step: Start a new task

## S018

Request (turn 1): We have expression and copy number for 150 tumors. We want an expression matrix corrected for copy-number dosage.

Requirements to judge (in the user's words):
R1: "an expression matrix corrected for copy-number dosage"

Reply:

````
What I understood you are asking for:
1. "We want an expression matrix corrected for copy-number dosage." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want an expression matrix corrected for copy-number dosage.” — Not matched to any registered workflow.
- next step: Show what NetZoo can do here
- next step: Start a new task

## S019

Request (turn 1): From expression, motifs and PPI of 80 tumors and 80 normals, we want TF activity per sample compared between tumor and normal.

Requirements to judge (in the user's words):
R1: "TF activity per sample compared between tumor and normal"

Reply:

````
What I understood you are asking for:
1. "TF activity per sample compared between tumor and normal" -- available from GIRAFFE's output plus a step you run outside NetZoo: A statistical test outside NetZoo on the activity matrix, with multiple-testing correction.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "we want TF activity per sample compared between tumor and normal." — The activity matrix holds one value per TF per sample (TF by sample, written as the `.tfa` output). GIRAFFE reports absolute activity, so every value is zero or positive.

**GIRAFFE** — Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.
- `tf_activity_matrix`: Inferred transcription-factor-by-sample activity values.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

Ask for the workflow's controls and defaults if you want to set them.

For your question ("we want TF activity per sample compared between tumor and normal"):
- **GIRAFFE** — The activity matrix compares TF activity, not network wiring, between the conditions; test each TF's activity between them (paired when the same individuals give both).

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: GIRAFFE fits your goal: cohort-level TF activity matrix.
- point: Method: Also estimates per-sample TF activity and signed activating/repressing effects.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Produces: regulatory network and TF activity matrix (one cohort-level result).
- point: Your question: whether the groups or time points differ; the reply says what GIRAFFE give toward it and the step after each.
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S020

Request (turn 1): We have expression of 90 samples. Is there a method that gives each sample its own Pearson co-expression network?

Requirements to judge (in the user's words):
R1: "gives each sample its own Pearson co-expression network"

Reply:

````
What I understood you are asking for:
1. "each sample its own Pearson co-expression network" -- available from LIONESS-COEXPRESSION.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "90 samples". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered methods can build a per-sample co-expression network; they differ in their modeling assumptions.
- point: Understood goal: a per-sample co-expression network.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: LIONESS-COEXPRESSION — One gene co-expression network per sample, from expression data alone · Pick it if you have dozens of samples or more
- option: BONOBO — One gene co-expression network per sample, with a p-value for each connection · Pick it if you have only a handful of samples or you need a p-value for each edge
- next step: Start a new task

## S021

Request (turn 1): We have a TF-gene network. We want a soft clustering in which each TF gets a membership weight in every module.

Requirements to judge (in the user's words):
R1: "a soft clustering in which each TF gets a membership weight in every module"

Reply:

````
What I understood you are asking for:
1. "a soft clustering in which each TF gets a membership weight in every module" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a soft clustering in which each TF gets a membership weight in every module” — Not matched to any registered workflow.
- next step: Start a new task

## S022

Request (turn 1): We have expression, motifs, PPI and follow-up for 260 patients. We want a model that forecasts each patient's relapse risk.

Requirements to judge (in the user's words):
R1: "a model that forecasts each patient's relapse risk"

Reply:

````
What I understood you are asking for:
1. "a model that forecasts each patient's relapse risk" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a model that forecasts each patient's relapse risk” — No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.
- next step: Start a new task

## S023

Request (turn 1): We have expression for 48 donors, TF motifs, PPI and TargetScan miRNA predictions. We want TF and miRNA regulatory networks for each donor separately.

Requirements to judge (in the user's words):
R1: "TF and miRNA regulatory networks for each donor separately"

Reply:

````
What I understood you are asking for:
1. "TF and miRNA regulatory networks for each donor separately" -- available from LIONESS-PUMA.

For the sample-specific output you described, use **LIONESS-PUMA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network
   - `mirna_file`: miRNA list

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PUMA** separately; **LIONESS-PUMA** also produces the aggregate output. Use **PUMA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 48 donors, 49 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PUMA gives the per-sample result you asked for; it also writes the cohort network, so PUMA need not run first.
- point: Method: One TF + miRNA network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network, miRNA list.
- point: Cost: N samples take N+1 PUMA runs (for your 48 donors, 49 PUMA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- next step: Plan LIONESS-PUMA with my data
- next step: Start a new task

## S024

Request (turn 1): We want gene co-expression for our 150 samples.
Request (turn 2): They come from three hospitals, and the hospital effect should be separated from the co-expression.

Requirements to judge (in the user's words):
R1: "the hospital effect should be separated from the co-expression"

Reply:

````
What I understood you are asking for:
1. "gene co-expression for our 150 samples" -- available from LIONESS-COEXPRESSION.

Assumptions behind this recommendation (not confirmed facts):

- The user has a dataset of gene expression measurements for the 150 samples.
- The hospital effect needs to be accounted for separately, indicating a need for a method that can adjust for this effect.

Selected path: **LIONESS-COEXPRESSION**.

Your question asks for a cohort-level co-expression network. **LIONESS-COEXPRESSION** fits that result and scale.

**LIONESS-COEXPRESSION** — Infer aggregate and sample-specific co-expression networks with LIONESS. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

Required workflow inputs:

- `expression_file`: expression matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-COEXPRESSION fits your goal: cohort-level co-expression network.
- point: Method: One gene co-expression network per sample; needs only expression data.
- point: Needs: expression matrix.
- point: Produces: co-expression network (cohort-level and per-sample).
- next step: Plan LIONESS-COEXPRESSION with my data
- next step: Start a new task

## S025

Request (turn 1): We have expression, motifs and PPI for 85 samples. We want lncRNAs included as regulators alongside the TFs.

Requirements to judge (in the user's words):
R1: "lncRNAs included as regulators alongside the TFs"

Reply:

````
What I understood you are asking for:
1. "We want lncRNAs included as regulators alongside the TFs." -- not available here: no registered workflow produces this. PUMA does not give it: PUMA's non-TF regulators are miRNAs given by a target prior; it has no lncRNA layer and models no sponging.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want lncRNAs included as regulators alongside the TFs.” — PUMA does not give it: PUMA's non-TF regulators are miRNAs given by a target prior; it has no lncRNA layer and models no sponging.
- next step: Start a new task
