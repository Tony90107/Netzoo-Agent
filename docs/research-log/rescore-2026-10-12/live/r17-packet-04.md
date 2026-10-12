## S076

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

## S077

Request (turn 1): We have expression, motifs, PPI and miRNA target predictions for 100 samples. Is there a method that builds one network including both TF and miRNA regulators?

Requirements to judge (in the user's words):
R1: "builds one network including both TF and miRNA regulators"

Reply:

````
What I understood you are asking for:
1. "Is there a method that builds one network including both TF and miRNA regulators?" -- available from PUMA or LIONESS-PUMA.

Selected path: **PUMA**.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale.

**PUMA** — Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Workflow-specific scientific notes:

- PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: PUMA fits your goal: cohort-level TF/miRNA-gene regulatory network.
- point: Method: PANDA's message passing with miRNA regulators added.
- point: Needs: expression matrix, motif prior, PPI network, miRNA list.
- point: Produces: regulatory network (one cohort-level result).
- next step: Plan PUMA with my data
- next step: Start a new task

## S078

Request (turn 1): We have matched lipidomics and transcriptomics for 130 subjects. We want conditional associations between lipids and genes, with an adjusted p-value for each.

Requirements to judge (in the user's words):
R1: "conditional associations between lipids and genes, with an adjusted p-value for each"

Reply:

````
What I understood you are asking for:
1. "conditional associations between lipids and genes, with an adjusted p-value for each" -- available from DRAGON.

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

## S079

Request (turn 1): From expression, motifs and PPI of 95 blood samples, we want TF activity scores per sample that do not just mirror TF mRNA levels.

Requirements to judge (in the user's words):
R1: "TF activity scores per sample that do not just mirror TF mRNA levels"

Reply:

````
What I understood you are asking for:
1. "TF activity scores per sample that do not just mirror TF mRNA levels" -- available from GIRAFFE.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "do not just mirror TF mRNA levels" — GIRAFFE fits each TF's activity (`tf_activity_matrix`) from the expression of its target genes and the TF-TF protein interactions; the TF's own mRNA level is not an input to it. If the TF's gene is among the expression rows it still counts as an ordinary target, so its activity is not tied to its mRNA rather than independent of it.

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
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S080

Request (turn 1): We have expression, motifs and PPI for 90 samples. We want each TF's binding affinity to its targets in nanomolar.

Requirements to judge (in the user's words):
R1: "each TF's binding affinity to its targets in nanomolar"

Reply:

````
What I understood you are asking for:
1. "each TF's binding affinity to its targets in nanomolar" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “each TF's binding affinity to its targets in nanomolar” — Not matched to any registered workflow.
- next step: Start a new task

## S081

Request (turn 1): We have Slide-seq data from 9,000 beads. We want TF-gene networks smoothed over neighbouring beads.

Requirements to judge (in the user's words):
R1: "TF-gene networks smoothed over neighbouring beads"

Reply:

````
What I understood you are asking for:
1. "TF-gene networks smoothed over neighbouring beads" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “TF-gene networks smoothed over neighbouring beads” — Not matched to any registered workflow.
- next step: Start a new task

## S082

Request (turn 1): We have RNA, ATAC and methylation for 60 matched samples. We want a single partial-correlation model of all three.

Requirements to judge (in the user's words):
R1: "a single partial-correlation model of all three"

Reply:

````
What I understood you are asking for:
1. "We want a single partial-correlation model of all three." -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a single partial-correlation model of all three.” — DRAGON does not give it: two layers only.
- next step: Start a new task

## S083

Request (turn 1): We have a TF-gene network from PANDA. We want a low-dimensional embedding vector for every gene.

Requirements to judge (in the user's words):
R1: "a low-dimensional embedding vector for every gene"

Reply:

````
What I understood you are asking for:
1. "We want a low-dimensional embedding vector for every gene." -- available from CONDOR.

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
- point: Understood goal: a TF-gene regulatory network.
- point: The registered alternatives do not fulfil the requested modeling requirement.
- question: Would one of these, without that requirement, work for you?
- option: PANDA — Widely used baseline: message passing over motif, PPI and co-expression evidence
- option: OTTER — Explicit objective (graph matching), fitted by a fixed number of gradient steps; lighter on memory
- not available: TIGER — Not runnable here (netZooR, R); Chen & Padi 2024, doi:10.1038/s41540-024-00386-w.
- not available: Werhli & Husmeier (2007) — Not runnable here (published method, no NetZoo implementation); PMID 17542777.
- next step: Start a new task

## S084

Request (turn 1): We want a TF-gene network across our 100 samples from expression, motifs and PPI.
Request (turn 2): We'd rather have one network for every patient.

Requirements to judge (in the user's words):
R1: "one network for every patient"

Reply:

````
What I understood you are asking for:
1. "a TF-gene network across our 100 samples" -- available from PANDA or OTTER.
2. "one network for every patient" -- available from LIONESS-PANDA or LIONESS-PUMA.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 100 samples, 101 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 100 samples, 101 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S085

Request (turn 1): We have somatic mutation calls for 330 tumors. We want our mutated genes ranked by how likely they are to be cancer drivers.

Requirements to judge (in the user's words):
R1: "our mutated genes ranked by how likely they are to be cancer drivers"

Reply:

````
What I understood you are asking for:
1. "our mutated genes ranked by how likely they are to be cancer drivers" -- not available here: no registered workflow produces this. SAMBAR does not give it: SAMBAR summarizes given mutation calls; it does not call or rank driver mutations.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “our mutated genes ranked by how likely they are to be cancer drivers” — SAMBAR does not give it: SAMBAR summarizes given mutation calls; it does not call or rank driver mutations.
- next step: Start a new task

## S086

Request (turn 1): We have copy number and expression for 58 matched tumors. We want each tumor's own copy-number-expression partial-correlation network.

Requirements to judge (in the user's words):
R1: "each tumor's own copy-number-expression partial-correlation network"

Reply:

````
What I understood you are asking for:
1. "each tumor's own copy-number-expression partial-correlation network" -- available from LIONESS-DRAGON.

Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Selected path: **LIONESS-DRAGON**.

Your question asks for a multi-omic network. **LIONESS-DRAGON** fits that result.

**LIONESS-DRAGON** — Infer one sample-specific two-layer multi-omic partial-correlation network per sample with LIONESS-DRAGON. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files. Plan the runtime and disk space, and filter edges before downstream statistics.

Outputs:

- `multi_omic_network`: Inferred associations between omics features.

Workflow-specific scientific notes:

- LIONESS-DRAGON estimates DRAGON's two shrinkage values once on all samples, then derives each sample's network from the all-sample network and the network refitted without that sample.
- Each sample's network is an undirected partial-correlation graph across both layers; like DRAGON's, it is an association graph, not a causal one.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-DRAGON fits your goal: multi-omic network.
- point: Method: One two-layer partial-correlation network per sample, derived leave-one-out.
- point: Needs: omics layer 1, omics layer 2.
- point: Cost: N samples take N+1 DRAGON runs (for your 58 tumors, 59 DRAGON runs).
- point: Produces: multi-omic network (one per sample).
- next step: Plan LIONESS-DRAGON with my data
- next step: Start a new task

## S087

Request (turn 1): We want gene co-expression for our 150 samples.
Request (turn 2): They come from three hospitals, and the hospital effect should be separated from the co-expression.

Requirements to judge (in the user's words):
R1: "the hospital effect should be separated from the co-expression"

Reply:

````
What I understood you are asking for:
1. "gene co-expression for our 150 samples." -- available from LIONESS-COEXPRESSION.
2. "the hospital effect should be separated from the co-expression." -- available from COBRA.

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
- point: Picked from 2 fitting methods because you wrote “They come from three hospitals, and…”; LIONESS-COEXPRESSION also fit.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- next step: Compare with LIONESS-COEXPRESSION
- next step: Plan COBRA with my data
- next step: Start a new task

## S088

Request (turn 1): We have a thresholded TF-gene network from PANDA. We want its communities by bipartite modularity.

Requirements to judge (in the user's words):
R1: "its communities by bipartite modularity"

Reply:

````
What I understood you are asking for:
1. "We want its communities by bipartite modularity." -- available from CONDOR.

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

## S089

Request (turn 1): We want one TF-gene network for 90 samples from expression, motifs and PPI, with its edges ranked by evolutionary conservation across 30 species.

Requirements to judge (in the user's words):
R1: "one TF-gene network"
R2: "its edges ranked by evolutionary conservation across 30 species"

Reply:

````
What I understood you are asking for:
1. "We want one TF-gene network for 90 samples from expression, motifs and PPI, with its edges ranked by evolutionary conservation across 30 species." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want one TF-gene network for 90 samples from expression, motifs and PPI… — Not matched to any registered workflow.
- next step: Start a new task

## S090

Request (turn 1): We have expression for 80 samples. We want each gene's mRNA half-life.

Requirements to judge (in the user's words):
R1: "each gene's mRNA half-life"

Reply:

````
What I understood you are asking for:
1. "each gene's mRNA half-life" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “each gene's mRNA half-life” — Not matched to any registered workflow.
- next step: Start a new task

## S091

Request (turn 1): We want subtypes from somatic mutations of 175 tumors and the driver gene of each subtype.

Requirements to judge (in the user's words):
R1: "subtypes from somatic mutations"
R2: "the driver gene of each subtype"

Reply:

````
What I understood you are asking for:
1. "subtypes from somatic mutations" -- available from SAMBAR.
2. "driver gene of each subtype" -- not available here: no registered workflow produces this. SAMBAR does not give it: SAMBAR summarizes given mutation calls; it does not call or rank driver mutations.

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
- not available: “driver gene of each subtype” — SAMBAR does not give it: SAMBAR summarizes given mutation calls; it does not call or rank driver mutations.
- next step: Plan SAMBAR with my data
- next step: Start a new task

## S092

Request (turn 1): We have RNA-seq of 75 lung adenocarcinomas plus a motif prior and a PPI network. We want a cohort-wide TF-to-gene network.

Requirements to judge (in the user's words):
R1: "a cohort-wide TF-to-gene network"

Reply:

````
What I understood you are asking for:
1. "a cohort-wide TF-to-gene network" -- available from PANDA, OTTER or LIONESS-PANDA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 3 registered methods can build a cohort-level TF-gene regulatory network; they differ in their modeling assumptions.
- point: Understood goal: a cohort-level TF-gene regulatory network from expression data, a motif prior and a PPI network.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- next step: Start a new task

## S093

Request (turn 1): We have a motif prior, PPI and a co-expression matrix for 60 samples. Which method fits a TF-gene network whose products match both the PPI and the co-expression?

Requirements to judge (in the user's words):
R1: "fits a TF-gene network whose products match both the PPI and the co-expression"

Reply:

````
What I understood you are asking for:
1. "Which method fits a TF-gene network whose products match both the PPI and the co-expression?" -- available from OTTER.

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

## S094

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

## S095

Request (turn 1): We have FASTQ files from 24 RNA-seq libraries. We want the reads aligned to the human genome.

Requirements to judge (in the user's words):
R1: "the reads aligned to the human genome"

Reply:

````
What I understood you are asking for:
1. "the reads aligned to the human genome" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “the reads aligned to the human genome” — Not matched to any registered workflow.
- next step: Show what NetZoo can do here
- next step: Start a new task

## S096

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

## S097

Request (turn 1): We want one network of how TFs and miRNAs regulate genes in our 70 samples.

Requirements to judge (in the user's words):
R1: "one network of how TFs and miRNAs regulate genes"

Reply:

````
What I understood you are asking for:
1. "one network of how TFs and miRNAs regulate genes" -- available from PUMA or LIONESS-PUMA.

**PUMA** fits the result you describe if you have a motif prior and a PPI network and a miRNA list.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale.

**PUMA** — Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Workflow-specific scientific notes:

- PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.

Ask for the workflow's controls and defaults if you want to set them.

**What your data allows.** PUMA also needs an expression matrix, a motif prior, a PPI network and a miRNA list. Do you also have a motif prior, a PPI network and a miRNA list?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: PUMA fits your goal if you have a motif prior and a PPI network and a miRNA list.
- point: Method: PANDA's message passing with miRNA regulators added.
- point: Needs: expression matrix, motif prior, PPI network, miRNA list.
- point: Produces: regulatory network (one cohort-level result).
- point: Your request names only the data I described; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior, a PPI network and a miRNA list?
- option: Only the data I described — Ask what the data you named can give instead
- option: I also have a motif prior, a PPI network and a miRNA list — Continues with the workflows this reply names
- next step: Plan PUMA with my data
- next step: Start a new task

## S098

Request (turn 1): We have a human TF-gene network. We want it aligned to the mouse network through orthologous genes.

Requirements to judge (in the user's words):
R1: "it aligned to the mouse network through orthologous genes"

Reply:

````
What I understood you are asking for:
1. "We want it aligned to the mouse network through orthologous genes." -- available from PANDA's output plus a step you run outside NetZoo: One run per condition on the same genes and priors, then compare; two aggregate networks give no per-sample spread for a test.

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

**What your data allows.** PANDA and GIRAFFE also need an expression matrix, a motif prior and a PPI network; OTTER also needs a motif prior, a PPI network and an expression matrix or adjusted co-expression matrix. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow implements the bayesian approach you asked for.
- point: Understood goal: a cohort-level TF-gene regulatory network.
- point: The registered alternatives do not fulfil the requested modeling requirement.
- question: Would one of these, without that requirement, work for you?
- option: PANDA — Widely used baseline: message passing over motif, PPI and co-expression evidence
- option: OTTER — Explicit objective (graph matching), fitted by a fixed number of gradient steps; lighter on memory
- not available: TIGER — Not runnable here (netZooR, R); Chen & Padi 2024, doi:10.1038/s41540-024-00386-w.
- not available: Werhli & Husmeier (2007) — Not runnable here (published method, no NetZoo implementation); PMID 17542777.
- next step: Start a new task

## S099

Request (turn 1): We want one network of how TFs and miRNAs regulate genes in our 70 samples.

Requirements to judge (in the user's words):
R1: "one network of how TFs and miRNAs regulate genes"

Reply:

````
What I understood you are asking for:
1. "one network of how TFs and miRNAs regulate genes" -- available from PUMA.

**PUMA** fits the result you describe if you have a motif prior and a PPI network and a miRNA list.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale.

**PUMA** — Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Workflow-specific scientific notes:

- PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.

Ask for the workflow's controls and defaults if you want to set them.

**What your data allows.** PUMA also needs an expression matrix, a motif prior, a PPI network and a miRNA list. Do you also have a motif prior, a PPI network and a miRNA list?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: PUMA fits your goal if you have a motif prior and a PPI network and a miRNA list.
- point: Method: PANDA's message passing with miRNA regulators added.
- point: Needs: expression matrix, motif prior, PPI network, miRNA list.
- point: Produces: regulatory network (one cohort-level result).
- point: Your request names only the data I described; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior, a PPI network and a miRNA list?
- option: Only the data I described — Ask what the data you named can give instead
- option: I also have a motif prior, a PPI network and a miRNA list — Continues with the workflows this reply names
- next step: Plan PUMA with my data
- next step: Start a new task

## S100

Request (turn 1): We have Slide-seq data from 9,000 beads. We want TF-gene networks smoothed over neighbouring beads.

Requirements to judge (in the user's words):
R1: "TF-gene networks smoothed over neighbouring beads"

Reply:

````
What I understood you are asking for:
1. "TF-gene networks smoothed over neighbouring beads" -- not available here: no registered workflow produces this. OTTER does not give it: no per-sample OTTER is registered.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “TF-gene networks smoothed over neighbouring beads” — OTTER does not give it: no per-sample OTTER is registered.
- next step: Start a new task
