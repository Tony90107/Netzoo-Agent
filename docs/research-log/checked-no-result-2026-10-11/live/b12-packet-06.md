## S171

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

## S172

Request (turn 1): We have expression, motifs and PPI from 90 tumors. Which method tells, for each TF-gene edge, whether the TF activates or represses that gene in each individual tumor?

Requirements to judge (in the user's words):
R1: "whether the TF activates or represses that gene in each individual tumor"

Reply:

````
What I understood you are asking for:
1. "Which method tells, for each TF-gene edge, whether the TF activates or represses that gene in each individual tumor?" -- not available here: no registered workflow produces this. GIRAFFE does not give it: the regulatory matrix is one for all samples; only activity is per sample.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Which method tells, for each TF-gene edge, whether the TF activates or… — GIRAFFE does not give it: the regulatory matrix is one for all samples; only activity is per sample.
- next step: Start a new task

## S173

Request (turn 1): We have expression, motifs and PPI from 50 samples and want a TF-gene network.
Request (turn 2): Actually we need it to say whether each TF activates or represses each target, separately in every sample.

Requirements to judge (in the user's words):
R1: "whether each TF activates or represses each target, separately in every sample"

Reply:

````
What I understood you are asking for:
1. "whether each TF activates or represses each target, separately in every sample." -- not available here: no registered workflow produces this. GIRAFFE does not give it: the regulatory matrix is one for all samples; only activity is per sample.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “whether each TF activates or represses each target, separately in every… — GIRAFFE does not give it: the regulatory matrix is one for all samples; only activity is per sample.
- next step: Start a new task

## S174

Request (turn 1): When is a Gaussian graphical model better than plain correlation for linking two omics layers?

Requirements to judge (in the user's words):
(none: this request asks about methods; give `R: []`)
Judge `consult` for this session.

Reply:

````
I can map this to more than one compatible network result:

- **DRAGON** — DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Per-sample version: **LIONESS-DRAGON**. Needs DRAGON omics layer 1 and DRAGON omics layer 2.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered workflows fit; one detail about your study decides between them.
- point: Understood goal: a multi-omic network.
- question: Should the result be aggregate or sample-specific?
- option: One cohort-wide network — Leads to DRAGON
- option: One network per sample — Leads to LIONESS-DRAGON · Lets you compare samples, or relate them to outcomes such as survival · Slower: it reruns DRAGON once per sample
- next step: Start a new task

## S175

Request (turn 1): We profiled liver expression every 3 hours across two days, with TF motifs and PPI. Is there a method that models how each TF's influence on a target at one time point carries over to the next time point?

Requirements to judge (in the user's words):
R1: "models how each TF's influence on a target at one time point carries over to the next time point"

Reply:

````
Routing matched these registered workflows to your words, but the capability check found no result in your request to check them against, so none is confirmed to give what you asked for:
- **PANDA** — produces: One weighted TF-to-gene regulatory network across all the samples given.
- **LIONESS-PANDA** — produces: One TF-gene network per sample, plus the aggregate network.
- **OTTER** — produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- **GIRAFFE** — produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.

Compare what each produces with what you asked for, or describe the result you want from your data and it is checked against what each workflow produces.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check found no result in your request to check them against.
- point: Compare what each produces with what you asked for; describing the result you want has it checked.
- question: Which one do you want to look at?
- option: PANDA — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all the samples given.
- option: LIONESS-PANDA — Not confirmed. Produces: One TF-gene network per sample, plus the aggregate network.
- option: OTTER — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- option: GIRAFFE — Not confirmed. Produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.
- next step: Start a new task

## S176

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

## S177

Request (turn 1): We have somatic mutations from 300 tumors. Which method groups the patients by how their mutations spread across pathways?

Requirements to judge (in the user's words):
R1: "groups the patients by how their mutations spread across pathways"

Reply:

````
What I understood you are asking for:
1. "Which method groups the patients by how their mutations spread across pathways?" -- available from SAMBAR.

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

## S178

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

## S179

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

## S180

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

## S181

Request (turn 1): We have expression, motifs and PPI from 80 samples and want a TF-gene network.
Request (turn 2): Actually we need a separate network for each sample.

Requirements to judge (in the user's words):
R1: "a separate network for each sample"

Reply:

````
What I understood you are asking for:
1. "Actually we need a separate network for each sample." -- available from LIONESS-PANDA, LIONESS-PUMA, LIONESS-DRAGON, LIONESS-COEXPRESSION or BONOBO.

I can map this to more than one compatible network result:

All of them derive each sample network from all-sample and leave-one-out networks, and iteratively exchange information across biological evidence networks.

**TF-only regulatory network**
- **LIONESS-PANDA** — Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **LIONESS-PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered workflows fit; one detail about your study decides between them.
- point: Understood goal: a per-sample regulatory network.
- question: Which regulator type should the network model: transcription factors, miRNA regulators, or both?
- option: Transcription factors only — Leads to LIONESS-PANDA · One TF-gene network per sample, plus the cohort network
- option: Both TFs and miRNAs — Leads to LIONESS-PUMA · One TF + miRNA network per sample, plus the cohort network · Also needs miRNA list
- next step: Start a new task

## S182

Request (turn 1): When is a Gaussian graphical model better than plain correlation for linking two omics layers?

Requirements to judge (in the user's words):
(none: this request asks about methods; give `R: []`)
Judge `consult` for this session.

Reply:

````
Routing matched these registered workflows to your words, but the capability check found no result in your request to check them against, so none is confirmed to give what you asked for:
- **DRAGON** — produces: One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples. A p-value and a Benjamini-Hochberg adjusted p-value for every edge (adjusted within each layer and across the layers), to filter edges by significance.

Compare what each produces with what you asked for, or describe the result you want from your data and it is checked against what each workflow produces.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check found no result in your request to check them against.
- point: Compare what each produces with what you asked for; describing the result you want has it checked.
- question: Which one do you want to look at?
- option: DRAGON — Not confirmed. Produces: One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples. A p-value and a Benjamini-Hochberg adjusted p-value for every edge (adjusted…
- next step: Start a new task

## S183

Request (turn 1): We have expression, motifs and PPI from 80 samples and want a TF-gene network.
Request (turn 2): Actually we need a separate network for each sample.

Requirements to judge (in the user's words):
R1: "a separate network for each sample"

Reply:

````
What I understood you are asking for:
1. "Actually we need a separate network for each sample." -- available from LIONESS-PANDA, LIONESS-PUMA, LIONESS-DRAGON, LIONESS-COEXPRESSION or BONOBO.

I can map this to more than one compatible network result:

All of them derive each sample network from all-sample and leave-one-out networks, and iteratively exchange information across biological evidence networks.

**TF-only regulatory network**
- **LIONESS-PANDA** — Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **LIONESS-PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered workflows fit; one detail about your study decides between them.
- point: Understood goal: a per-sample regulatory network.
- question: Which regulator type should the network model: transcription factors, miRNA regulators, or both?
- option: Transcription factors only — Leads to LIONESS-PANDA · One TF-gene network per sample, plus the cohort network
- option: Both TFs and miRNAs — Leads to LIONESS-PUMA · One TF + miRNA network per sample, plus the cohort network · Also needs miRNA list
- next step: Start a new task

## S184

Request (turn 1): When is a Gaussian graphical model better than plain correlation for linking two omics layers?

Requirements to judge (in the user's words):
(none: this request asks about methods; give `R: []`)
Judge `consult` for this session.

Reply:

````
Routing matched these registered workflows to your words, but the capability check found no result in your request to check them against, so none is confirmed to give what you asked for:
- **DRAGON** — produces: One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples. A p-value and a Benjamini-Hochberg adjusted p-value for every edge (adjusted within each layer and across the layers), to filter edges by significance.

Compare what each produces with what you asked for, or describe the result you want from your data and it is checked against what each workflow produces.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check found no result in your request to check them against.
- point: Compare what each produces with what you asked for; describing the result you want has it checked.
- question: Which one do you want to look at?
- option: DRAGON — Not confirmed. Produces: One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples. A p-value and a Benjamini-Hochberg adjusted p-value for every edge (adjusted…
- next step: Start a new task

## S185

Request (turn 1): We have expression, motifs and PPI from 80 samples and want a TF-gene network.
Request (turn 2): Actually we need a separate network for each sample.

Requirements to judge (in the user's words):
R1: "a separate network for each sample"

Reply:

````
What I understood you are asking for:
1. "Actually we need a separate network for each sample." -- available from LIONESS-PANDA or LIONESS-PUMA.

I can map this to more than one compatible network result:

All of them derive each sample network from all-sample and leave-one-out networks, and iteratively exchange information across biological evidence networks.

**TF-only regulatory network**
- **LIONESS-PANDA** — Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **LIONESS-PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered workflows fit; one detail about your study decides between them.
- point: Understood goal: a per-sample regulatory network.
- question: Which regulator type should the network model: transcription factors, miRNA regulators, or both?
- option: Transcription factors only — Leads to LIONESS-PANDA · One TF-gene network per sample, plus the cohort network
- option: Both TFs and miRNAs — Leads to LIONESS-PUMA · One TF + miRNA network per sample, plus the cohort network · Also needs miRNA list
- next step: Start a new task

## S186

Request (turn 1): We profiled liver expression every 3 hours across two days, with TF motifs and PPI. Is there a method that models how each TF's influence on a target at one time point carries over to the next time point?

Requirements to judge (in the user's words):
R1: "models how each TF's influence on a target at one time point carries over to the next time point"

Reply:

````
What I understood you are asking for:
1. "Is there a method that models how each TF's influence on a target at one time point carries over to the next time point?" -- not available here: no registered workflow produces this. PANDA does not give it: one static network per set of samples; time points can only be compared as separate networks.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Is there a method that models how each TF's influence on a target at one time… — PANDA does not give it: one static network per set of samples; time points can only be compared as separate networks.
- next step: Start a new task

## S187

Request (turn 1): We have somatic mutations from 300 tumors. Which method groups the patients by how their mutations spread across pathways?

Requirements to judge (in the user's words):
R1: "groups the patients by how their mutations spread across pathways"

Reply:

````
What I understood you are asking for:
1. "Which method groups the patients by how their mutations spread across pathways?" -- available from SAMBAR.

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

## S188

Request (turn 1): We have expression, motifs and PPI from 60 tumors. We want each TF's activity per tumor and each TF's protein abundance in each tumor.

Requirements to judge (in the user's words):
R1: "each TF's activity per tumor"
R2: "each TF's protein abundance in each tumor"

Reply:

````
What I understood you are asking for:
1. "each TF's activity per tumor" -- available from GIRAFFE.
2. "each TF's protein abundance in each tumor" -- not available here: no registered workflow produces this. GIRAFFE does not give it: activity is inferred from expression and priors, not measured.

Assumptions behind this recommendation (not confirmed facts):

- The expression data is suitable for inferring TF activity.
- The motifs and PPI data are relevant for the analysis.
- The expression data is suitable for inferring TF protein abundance.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

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
- headline: GIRAFFE fits your goal: cohort-level TF activity matrix.
- point: Method: Also estimates per-sample TF activity and signed activating/repressing effects.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Produces: regulatory network and TF activity matrix (one cohort-level result).
- not available: “each TF's protein abundance in each tumor” — GIRAFFE does not give it: activity is inferred from expression and priors, not measured.
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S189

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

## S190

Request (turn 1): When is a Gaussian graphical model better than plain correlation for linking two omics layers?

Requirements to judge (in the user's words):
(none: this request asks about methods; give `R: []`)
Judge `consult` for this session.

Reply:

````
Routing matched these registered workflows to your words, but the capability check found no result in your request to check them against, so none is confirmed to give what you asked for:
- **DRAGON** — produces: One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples. A p-value and a Benjamini-Hochberg adjusted p-value for every edge (adjusted within each layer and across the layers), to filter edges by significance.

Compare what each produces with what you asked for, or describe the result you want from your data and it is checked against what each workflow produces.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check found no result in your request to check them against.
- point: Compare what each produces with what you asked for; describing the result you want has it checked.
- question: Which one do you want to look at?
- option: DRAGON — Not confirmed. Produces: One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples. A p-value and a Benjamini-Hochberg adjusted p-value for every edge (adjusted…
- next step: Start a new task

## S191

Request (turn 1): What is the difference between a per-sample regulatory network and a cohort network?

Requirements to judge (in the user's words):
(none: this request asks about methods; give `R: []`)
Judge `consult` for this session.

Reply:

````
Routing matched these registered workflows to your words, but the capability check found no result in your request to check them against, so none is confirmed to give what you asked for:
- **LIONESS-PANDA** — produces: One TF-gene network per sample, plus the aggregate network.
- **LIONESS-PUMA** — produces: One TF/miRNA-gene network per sample, plus the aggregate network.

Compare what each produces with what you asked for, or describe the result you want from your data and it is checked against what each workflow produces.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check found no result in your request to check them against.
- point: Compare what each produces with what you asked for; describing the result you want has it checked.
- point: Your request names only the data I described; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior and a PPI network?
- option: Only the data I described — Ask what the data you named can give instead
- option: I also have a motif prior and a PPI network — Continues with the workflows this reply names
- next step: Start a new task

## S192

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

## S193

Request (turn 1): We have expression and methylation from 100 matched samples. Is there a method that captures the direct links between the two layers while conditioning on all the other features?

Requirements to judge (in the user's words):
R1: "captures the direct links between the two layers while conditioning on all the other features"

Reply:

````
What I understood you are asking for:
1. "Is there a method that captures the direct links between the two layers while conditioning on all the other features?" -- available from DRAGON.

Assumptions behind this recommendation (not confirmed facts):

- The user has expression and methylation data from matched samples.
- The analysis aims to explore relationships while controlling for other variables.

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

## S194

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

- The user has the necessary data for age adjustment.
- The user is interested in aggregate results rather than sample-specific outputs.

Selected path: **COBRA**.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale.

What you asked about:

- "We want the co-expression adjusted for age and a list of genes differentially expressed with age." — Each covariate's component is a gene-by-gene co-expression attributable to that covariate; the adjusted co-expression can be passed to PANDA, PUMA or OTTER as coexpression_file after its identifiers and order are revalidated. Interpret each component relative to how the design matrix codes that covariate (for example, which level is the reference).

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
- point: Picked from 2 fitting methods because you wrote “We want the co-expression adjusted for…”; LIONESS-COEXPRESSION also fit.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- not available: “a list of genes differentially expressed with age” — COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.
- next step: Compare with LIONESS-COEXPRESSION
- next step: Plan COBRA with my data
- next step: Start a new task

## S195

Request (turn 1): We have somatic mutations from 300 tumors. Which method groups the patients by how their mutations spread across pathways?

Requirements to judge (in the user's words):
R1: "groups the patients by how their mutations spread across pathways"

Reply:

````
What I understood you are asking for:
1. "Which method groups the patients by how their mutations spread across pathways?" -- available from SAMBAR.

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

## S196

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

## S197

Request (turn 1): We have expression and methylation from 100 matched samples. Is there a method that captures the direct links between the two layers while conditioning on all the other features?

Requirements to judge (in the user's words):
R1: "captures the direct links between the two layers while conditioning on all the other features"

Reply:

````
What I understood you are asking for:
1. "captures the direct links between the two layers while conditioning on all the other features" -- available from DRAGON.

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

## S198

Request (turn 1): We have expression and methylation from 90 matched samples and want a network linking them.
Request (turn 2): We also need a p-value for each edge.

Requirements to judge (in the user's words):
R1: "a p-value for each edge"

Reply:

````
What I understood you are asking for:
1. "We also need a p-value for each edge." -- available from DRAGON.

Fallback recommendation: **BONOBO**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a p-value matrix. **BONOBO** is related to that result.

**BONOBO** — Infer sample-specific gene-gene co-expression networks with netZooPy BONOBO. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

Required workflow inputs:

- `expression_file`: expression matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.
- `pvalue_matrix`: P-value matrix paired with a sample-specific gene-gene co-expression result.

When `sparsify=False` and `save_pvals=False`: full sample-specific gene-gene co-expression matrices; no p-value artifact is written.

When `sparsify=True` and `save_pvals=False`: upstream thresholds each sample-specific co-expression matrix; no p-value artifact is written.

When `sparsify=True` and `save_pvals=True`: upstream retains the full co-expression matrix for each selected sample and writes a matching p-value matrix; threshold it from the saved p-value matrix; it does not also emit an already-thresholded network in this mode.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: BONOBO is the closest registered match, but it is not a verified match for your request.
- point: Method: Per-sample co-expression with Bayesian shrinkage and a p-value per edge.
- point: Needs: expression matrix.
- point: Produces: co-expression network and p-value matrix (one per sample).
- next step: Start a new task

## S199

Request (turn 1): We have a TF-gene network from PANDA. We want its communities and, for each community, the TFs that are most central to it.

Requirements to judge (in the user's words):
R1: "its communities"
R2: "for each community, the TFs that are most central to it"

Reply:

````
What I understood you are asking for:
1. "its communities" -- available from CONDOR.
2. "for each community, the TFs that are most central to it" -- available from CONDOR.

Assumptions behind this recommendation (not confirmed facts):

- The TF-gene network is suitable for community detection analysis.

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

## S200

Request (turn 1): We have expression, motifs and PPI from 60 patients. Which method estimates each patient's own TF-gene network from how the cohort network changes when that patient is left out?

Requirements to judge (in the user's words):
R1: "estimates each patient's own TF-gene network"

Reply:

````
What I understood you are asking for:
1. "each patient's own TF-gene network from how the cohort network changes when that patient is left out" -- available from LIONESS-PANDA.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 60 patients, 61 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

For your question ("how the cohort network changes when that patient is left out"):
- **LIONESS-PANDA** — Each sample gets its own network; comparing each sample's network or targeting scores with the rest of the cohort shows which individuals stand out.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 60 patients, 61 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- point: Your question: which individuals change or stand out; the reply says what LIONESS-PANDA give toward it and the step after each.
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S201

Request (turn 1): We have expression with batch and sex recorded for 120 samples. Is there a method that separates how much of each gene pair's co-expression comes from each covariate?

Requirements to judge (in the user's words):
R1: "separates how much of each gene pair's co-expression comes from each covariate"

Reply:

````
What I understood you are asking for:
1. "separates how much of each gene pair's co-expression comes from each covariate" -- available from COBRA.

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
- point: Picked from 3 fitting methods because you wrote “Is there a method that separates how…”; LIONESS-COEXPRESSION and BONOBO also fit.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- next step: Compare with LIONESS-COEXPRESSION and BONOBO
- next step: Plan COBRA with my data
- next step: Start a new task

## S202

Request (turn 1): We profiled liver expression every 3 hours across two days, with TF motifs and PPI. Is there a method that models how each TF's influence on a target at one time point carries over to the next time point?

Requirements to judge (in the user's words):
R1: "models how each TF's influence on a target at one time point carries over to the next time point"

Reply:

````
What I understood you are asking for:
1. "Is there a method that models how each TF's influence on a target at one time point carries over to the next time point?" -- not available here: no registered workflow produces this. PANDA does not give it: one static network per set of samples; time points can only be compared as separate networks.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Is there a method that models how each TF's influence on a target at one time… — PANDA does not give it: one static network per set of samples; time points can only be compared as separate networks.
- next step: Start a new task

## S203

Request (turn 1): We profiled liver expression every 3 hours across two days, with TF motifs and PPI. Is there a method that models how each TF's influence on a target at one time point carries over to the next time point?

Requirements to judge (in the user's words):
R1: "models how each TF's influence on a target at one time point carries over to the next time point"

Reply:

````
What I understood you are asking for:
1. "Is there a method that models how each TF's influence on a target at one time point carries over to the next time point?" -- not available here: no registered workflow produces this. PANDA does not give it: one static network per set of samples; time points can only be compared as separate networks.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Is there a method that models how each TF's influence on a target at one time… — PANDA does not give it: one static network per set of samples; time points can only be compared as separate networks.
- next step: Start a new task

## S204

Request (turn 1): We have expression, motifs and PPI from 60 patients. Which method estimates each patient's own TF-gene network from how the cohort network changes when that patient is left out?

Requirements to judge (in the user's words):
R1: "estimates each patient's own TF-gene network"

Reply:

````
What I understood you are asking for:
1. "each patient's own TF-gene network from how the cohort network changes when that patient is left out" -- available from LIONESS-PANDA.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 60 patients, 61 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

For your question ("how the cohort network changes when that patient is left out"):
- **LIONESS-PANDA** — Each sample gets its own network; comparing each sample's network or targeting scores with the rest of the cohort shows which individuals stand out.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 60 patients, 61 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- point: Your question: which individuals change or stand out; the reply says what LIONESS-PANDA give toward it and the step after each.
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task
