## S103

Request (turn 1): We have somatic mutations from 250 tumors. We want patient subtypes from pathway mutation scores and a comparison of survival between the subtypes.

Requirements to judge (in the user's words):
R1: "patient subtypes from pathway mutation scores"
R2: "a comparison of survival between the subtypes"

Reply:

````
What I understood you are asking for:
1. "patient subtypes from pathway mutation scores" -- available from SAMBAR.
2. "a comparison of survival between the subtypes" -- available from SAMBAR's output plus a step you run outside NetZoo: A test outside NetZoo with a clinical table keyed by sample ID.

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

## S104

Request (turn 1): We have a TF-gene network from PANDA. We want its communities and a 3D animation of the communities rotating.

Requirements to judge (in the user's words):
R1: "its communities"
R2: "a 3D animation of the communities rotating"

Reply:

````
What I understood you are asking for:
1. "its communities" -- available from CONDOR.
2. "a 3D animation of the communities rotating." -- not matched to any registered workflow.

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
- not available: “a 3D animation of the communities rotating.” — Not matched to any registered workflow.
- next step: Plan CONDOR with my data
- next step: Start a new task

## S105

Request (turn 1): We have expression and methylation from 100 matched samples. Is there a method that captures the direct links between the two layers while conditioning on all the other features?

Requirements to judge (in the user's words):
R1: "captures the direct links between the two layers while conditioning on all the other features"

Reply:

````
What I understood you are asking for:
1. "Is there a method that captures the direct links between the two layers while conditioning on all the other features?" -- available from DRAGON.

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

## S106

Request (turn 1): What does LIONESS assume about the samples when it estimates one network per sample?

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

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered workflows fit; one detail about your study decides between them.
- point: Understood goal: a per-sample regulatory network.
- question: Which regulator type should the network model: transcription factors, miRNA regulators, or both?
- option: Transcription factors only — Leads to LIONESS-PANDA · One TF-gene network per sample, plus the cohort network
- option: Both TFs and miRNAs — Leads to LIONESS-PUMA · One TF + miRNA network per sample, plus the cohort network · Also needs miRNA list
- next step: Start a new task

## S107

Request (turn 1): We have a TF-gene network from PANDA. We want its communities and a 3D animation of the communities rotating.

Requirements to judge (in the user's words):
R1: "its communities"
R2: "a 3D animation of the communities rotating"

Reply:

````
What I understood you are asking for:
1. "its communities" -- available from CONDOR.
2. "a 3D animation of the communities rotating" -- not matched to any registered workflow.

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
- not available: “a 3D animation of the communities rotating” — Not matched to any registered workflow.
- next step: Plan CONDOR with my data
- next step: Start a new task

## S108

Request (turn 1): We have expression, motifs and PPI from 65 patients. We want a TF-gene network for each patient and also the network for the whole cohort.

Requirements to judge (in the user's words):
R1: "a TF-gene network for each patient"
R2: "the network for the whole cohort"

Reply:

````
What I understood you are asking for:
1. "a TF-gene network for each patient" -- available from LIONESS-PANDA.
2. "the network for the whole cohort" -- available from PANDA.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 65 patients, 66 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 65 patients, 66 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S109

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

- The user has the necessary data to compute protein abundance per tumor.

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
- not available: “each TF's protein abundance in each tumor” — GIRAFFE does not give it: activity is inferred from expression and priors, not measured.
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S110

Request (turn 1): We have expression, motifs and PPI from 60 patients. Which method estimates each patient's own TF-gene network from how the cohort network changes when that patient is left out?

Requirements to judge (in the user's words):
R1: "estimates each patient's own TF-gene network"

Reply:

````
What I understood you are asking for:
1. "estimates each patient's own TF-gene network from how the cohort network changes when that patient is left out" -- available from LIONESS-PANDA.

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

## S111

Request (turn 1): We have a TF-gene network from PANDA. We want its communities and, for each community, the TFs that are most central to it.

Requirements to judge (in the user's words):
R1: "its communities"
R2: "for each community, the TFs that are most central to it"

Reply:

````
What I understood you are asking for:
1. "its communities" -- available from CONDOR.
2. "the TFs that are most central to it" -- available from CONDOR.

Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: I could not validate an interpretation of this request, so nothing was selected.
- point: This does not mean your question is unclear; restating the result you want usually helps.
- next step: Start a new task

## S112

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

## S113

Request (turn 1): We have somatic mutations from 250 tumors. We want patient subtypes from pathway mutation scores and a comparison of survival between the subtypes.

Requirements to judge (in the user's words):
R1: "patient subtypes from pathway mutation scores"
R2: "a comparison of survival between the subtypes"

Reply:

````
What I understood you are asking for:
1. "patient subtypes from pathway mutation scores" -- available from SAMBAR.
2. "a comparison of survival between the subtypes" -- available from SAMBAR's output plus a step you run outside NetZoo: A test outside NetZoo with a clinical table keyed by sample ID.

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

## S114

Request (turn 1): We have a TF-gene network from PANDA. We want its communities and a 3D animation of the communities rotating.

Requirements to judge (in the user's words):
R1: "its communities"
R2: "a 3D animation of the communities rotating"

Reply:

````
What I understood you are asking for:
1. "its communities" -- available from CONDOR.
2. "a 3D animation of the communities rotating" -- not matched to any registered workflow.

Fallback recommendation: **CONDOR**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a cohort-level community assignment. **CONDOR** is related to that result and scale.

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
- headline: CONDOR is the closest registered match, but it is not a verified match for your request.
- point: Method: Finds TF-gene communities (modules) in a two-mode network.
- point: Needs: TF-gene (bipartite) network.
- point: Before running: threshold a PANDA or LIONESS network so its edge weights are non-negative; CONDOR then gives each node one community and a core score.
- point: Produces: set of network communities (modules) (one cohort-level result).
- not available: “a 3D animation of the communities rotating” — Not matched to any registered workflow.
- next step: Start a new task

## S115

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

## S116

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

## S117

Request (turn 1): We have somatic mutations from 250 tumors. We want patient subtypes from pathway mutation scores and a comparison of survival between the subtypes.

Requirements to judge (in the user's words):
R1: "patient subtypes from pathway mutation scores"
R2: "a comparison of survival between the subtypes"

Reply:

````
What I understood you are asking for:
1. "patient subtypes from pathway mutation scores" -- available from SAMBAR.
2. "a comparison of survival between the subtypes" -- available from SAMBAR's output plus a step you run outside NetZoo: A test outside NetZoo with a clinical table keyed by sample ID.

Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

Why this recommendation:

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

What you asked about:

- "a comparison of survival between the subtypes" — Subtype labels can be compared with clinical variables -- survival between subtypes, for example; that needs a clinical table keyed by the same sample IDs. The pathway mutation scores show which pathways separate the subtypes.

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

## S118

Request (turn 1): How do bipartite community methods decide which genes are core to a module?

Requirements to judge (in the user's words):
(none: this request asks about methods; give `R: []`)
Judge `consult` for this session.

Reply:

````
Routing matched these registered workflows to your words, but the capability check found no result in your request to check them against, so none is confirmed to give what you asked for:
- **CONDOR** — produces: Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity. Each regulator's and gene's core score -- its share of its community's modularity -- to pick out each community's core nodes.

Compare what each produces with what you asked for, or describe the result you want from your data and it is checked against what each workflow produces.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check found no result in your request to check them against.
- point: Compare what each produces with what you asked for; describing the result you want has it checked.
- question: Which one do you want to look at?
- option: CONDOR — Not confirmed. Produces: Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity. Each regulator's and gene's core score -- its share of its community's modularity -- to pick out each community's core nodes.
- next step: Start a new task

## S119

Request (turn 1): We have expression, motifs and PPI from 90 tumors. Which method tells, for each TF-gene edge, whether the TF activates or represses that gene in each individual tumor?

Requirements to judge (in the user's words):
R1: "whether the TF activates or represses that gene in each individual tumor"

Reply:

````
What I understood you are asking for:
1. "Which method tells, for each TF-gene edge, whether the TF activates or represses that gene in each individual tumor?" -- not available here: no registered workflow produces this. PANDA does not give it: edge weights are unsigned support scores.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Which method tells, for each TF-gene edge, whether the TF activates or… — PANDA does not give it: edge weights are unsigned support scores.
- next step: Start a new task

## S120

Request (turn 1): We have a TF-gene network from PANDA. We want its communities and a 3D animation of the communities rotating.

Requirements to judge (in the user's words):
R1: "its communities"
R2: "a 3D animation of the communities rotating"

Reply:

````
What I understood you are asking for:
1. "its communities" -- available from CONDOR.
2. "a 3D animation of the communities rotating." -- not matched to any registered workflow.

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
- not available: “a 3D animation of the communities rotating.” — Not matched to any registered workflow.
- next step: Plan CONDOR with my data
- next step: Start a new task

## S121

Request (turn 1): We have somatic mutations from 250 tumors. We want patient subtypes from pathway mutation scores and a comparison of survival between the subtypes.

Requirements to judge (in the user's words):
R1: "patient subtypes from pathway mutation scores"
R2: "a comparison of survival between the subtypes"

Reply:

````
What I understood you are asking for:
1. "patient subtypes from pathway mutation scores" -- available from SAMBAR.
2. "a comparison of survival between the subtypes" -- available from SAMBAR's output plus a step you run outside NetZoo: A test outside NetZoo with a clinical table keyed by sample ID.

Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: I could not validate an interpretation of this request, so nothing was selected.
- point: This does not mean your question is unclear; restating the result you want usually helps.
- next step: Start a new task

## S122

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

## S123

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
- point: Your request names only the data I described; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior and a PPI network?
- option: Only the data I described — Ask what the data you named can give instead
- option: I also have a motif prior and a PPI network — Continues with the workflows this reply names
- next step: Start a new task

## S124

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

## S125

Request (turn 1): We have spatial transcriptomics of 3,000 spots with motifs and PPI. Which method models how each spot's regulatory network is shaped by the networks of its neighbouring spots?

Requirements to judge (in the user's words):
R1: "models how each spot's regulatory network is shaped by the networks of its neighbouring spots"

Reply:

````
What I understood you are asking for:
1. "Which method models how each spot's regulatory network is shaped by the networks of its neighbouring spots?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Which method models how each spot's regulatory network is shaped by the… — Not matched to any registered workflow.
- next step: Start a new task

## S126

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

## S127

Request (turn 1): We have expression and methylation from 100 matched samples. Is there a method that captures the direct links between the two layers while conditioning on all the other features?

Requirements to judge (in the user's words):
R1: "captures the direct links between the two layers while conditioning on all the other features"

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

## S128

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

## S129

Request (turn 1): We profiled liver expression every 3 hours across two days, with TF motifs and PPI. Is there a method that models how each TF's influence on a target at one time point carries over to the next time point?

Requirements to judge (in the user's words):
R1: "models how each TF's influence on a target at one time point carries over to the next time point"

Reply:

````
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
- point: Understood goal: a TF-gene regulatory network.
- point: Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and GIRAFFE give one across all samples.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: LIONESS-PANDA — One TF-gene network per sample, plus the cohort network · Lets you compare samples, or relate them to outcomes such as survival · Slower: it reruns PANDA once per sample
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- next step: Start a new task

## S130

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

## S131

Request (turn 1): We have RNA-seq from 70 liver samples plus TF motifs and PPI. Is there a method that weighs how strongly each TF regulates each gene by reconciling the motif prior with co-expression and protein interactions?

Requirements to judge (in the user's words):
R1: "weighs how strongly each TF regulates each gene by reconciling the motif prior with co-expression and protein interactions"

Reply:

````
What I understood you are asking for:
1. "weighs how strongly each TF regulates each gene by reconciling the motif prior with co-expression and protein interactions?" -- available from PANDA.

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

## S132

Request (turn 1): We have a TF-gene network from PANDA. We want its communities and a 3D animation of the communities rotating.

Requirements to judge (in the user's words):
R1: "its communities"
R2: "a 3D animation of the communities rotating"

Reply:

````
What I understood you are asking for:
1. "its communities" -- available from CONDOR.
2. "a 3D animation of the communities rotating" -- not matched to any registered workflow.

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
- not available: “a 3D animation of the communities rotating” — Not matched to any registered workflow.
- next step: Plan CONDOR with my data
- next step: Start a new task

## S133

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

## S134

Request (turn 1): We have expression, motifs and PPI from 90 tumors. Which method tells, for each TF-gene edge, whether the TF activates or represses that gene in each individual tumor?

Requirements to judge (in the user's words):
R1: "whether the TF activates or represses that gene in each individual tumor"

Reply:

````
What I understood you are asking for:
1. "Which method tells, for each TF-gene edge, whether the TF activates or represses that gene in each individual tumor?" -- not available here: no registered workflow produces this. PANDA does not give it: edge weights are unsigned support scores.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Which method tells, for each TF-gene edge, whether the TF activates or… — PANDA does not give it: edge weights are unsigned support scores.
- next step: Start a new task

## S135

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

## S136

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
