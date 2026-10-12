## S001

Request (turn 1): We have expression for 250 patients. We want a classifier that predicts treatment response.

Requirements to judge (in the user's words):
R1: "We want a classifier that predicts treatment response"

Reply:

````
What I understood you are asking for:
1. "a classifier that predicts treatment response" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a classifier that predicts treatment response” — No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.
- next step: Start a new task

## S002

Request (turn 1): We have expression, motifs and PPI for 80 tumors. We want each TF's activity per tumor. The activity must not simply be the TF's own mRNA level.

Requirements to judge (in the user's words):
R1: "We want each TF's activity per tumor"

Reply:

````
What I understood you are asking for:
1. "each TF's activity per tumor" -- available from GIRAFFE.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "The activity must not simply be the TF's own mRNA level." — GIRAFFE fits each TF's activity (`tf_activity_matrix`) from the expression of its target genes and the TF-TF protein interactions; the TF's own mRNA level is not an input to it. If the TF's gene is among the expression rows it still counts as an ordinary target, so its activity is not tied to its mRNA rather than independent of it.

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

## S003

Request (turn 1): We want a co-expression network per sample for 95 samples. The cohort-wide network should be produced as well.

Requirements to judge (in the user's words):
R1: "We want a co-expression network per sample for 95 samples"

Reply:

````
What I understood you are asking for:
1. "a co-expression network per sample" -- available from LIONESS-COEXPRESSION or BONOBO.
2. "cohort-wide network" -- available from LIONESS-COEXPRESSION.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “co-expression network per sample” and “cohort-wide network”:

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

For “co-expression network per sample”:

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
````

Card shown with the reply:
- headline: You described 2 approaches; each is tested with a different registered workflow.
- question: Which hypothesis should we start with?
- option: LIONESS-COEXPRESSION — For “co-expression network per sample” and “cohort-wide network” · One gene co-expression network per sample; needs only expression data
- option: BONOBO — For “co-expression network per sample” · Per-sample co-expression with Bayesian shrinkage and a p-value per edge
- next step: Start a new task

## S004

Request (turn 1): We want a co-expression network per sample for 95 samples. The cohort-wide network should be produced as well.

Requirements to judge (in the user's words):
R1: "We want a co-expression network per sample for 95 samples"

Reply:

````
What I understood you are asking for:
1. "a co-expression network per sample" -- available from LIONESS-COEXPRESSION or BONOBO.
2. "The cohort-wide network" -- available from LIONESS-COEXPRESSION.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “co-expression network per sample” and “cohort-wide network”:

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

For “co-expression network per sample”:

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
````

Card shown with the reply:
- headline: You described 2 approaches; each is tested with a different registered workflow.
- question: Which hypothesis should we start with?
- option: LIONESS-COEXPRESSION — For “co-expression network per sample” and “cohort-wide network” · One gene co-expression network per sample; needs only expression data
- option: BONOBO — For “co-expression network per sample” · Per-sample co-expression with Bayesian shrinkage and a p-value per edge
- next step: Start a new task

## S005

Request (turn 1): We want a co-expression network for each of our 85 samples. The edges have to point from regulator to target.

Requirements to judge (in the user's words):
R1: "We want a co-expression network for each of our 85 samples"

Reply:

````
What I understood you are asking for:
1. "We want a co-expression network for each of our 85 samples." -- available from LIONESS-PUMA.

Selected path: **LIONESS-PUMA**.

**LIONESS-PUMA** — Infer aggregate PUMA and sample-specific LIONESS-PUMA networks. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files. Plan the runtime and disk space, and filter edges before downstream statistics.

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PUMA produces a regulatory network (cohort-level and per-sample).
- point: Method: One TF + miRNA network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network, miRNA list.
- point: Cost: N samples take N+1 PUMA runs (for your 85 samples, 86 PUMA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- point: It also writes the cohort network, so PUMA need not run first.
- next step: Plan LIONESS-PUMA with my data
- next step: Start a new task

## S006

Request (turn 1): We have long-read RNA-seq for 12 samples. We want the transcription start sites of our genes re-annotated.

Requirements to judge (in the user's words):
R1: "We want the transcription start sites of our genes re-annotated"

Reply:

````
What I understood you are asking for:
1. "We want the transcription start sites of our genes re-annotated." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want the transcription start sites of our genes re-annotated.” — Not matched to any registered workflow.
- next step: Start a new task

## S007

Request (turn 1): We want a TF-gene network from expression, motifs and PPI of 66 samples.
Request (turn 2): It has to be learned without the motif prior.

Requirements to judge (in the user's words):
R1: "It has to be learned without the motif prior"

Reply:

````
What I understood you are asking for:
1. "We want a TF-gene network from expression, motifs and PPI of 66 samples." -- available from PANDA.

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

**What your data allows.** PANDA, LIONESS-PANDA, OTTER and GIRAFFE need a motif prior and a PPI network, which you said you do not have ("without the motif prior").

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

## S008

Request (turn 1): We want per-sample TF-gene networks for 50 samples from expression, motifs and PPI. Each sample's network must be estimated from that sample alone, without using the other samples.

Requirements to judge (in the user's words):
R1: "We want per-sample TF-gene networks for 50 samples"

Reply:

````
What I understood you are asking for:
1. "per-sample TF-gene networks" -- not available here: no registered workflow produces this. LIONESS-PANDA does not meet "Each sample's network must be estimated from that sample alone, without using the other samples.".

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “per-sample TF-gene networks” — LIONESS-PANDA does not meet "Each sample's network must be estimated from that sample alone, without using the other samples.".
- next step: Start a new task

## S009

Request (turn 1): We want the communities of our bipartite TF-gene network. They must keep TFs and genes as two separate node types.

Requirements to judge (in the user's words):
R1: "We want the communities of our bipartite TF-gene network"

Reply:

````
What I understood you are asking for:
1. "We want the communities of our bipartite TF-gene network." -- available from CONDOR.

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

## S010

Request (turn 1): We have expression and proteomics for 100 matched samples. We want a network linking them. Each link must be conditional on all other measured features.

Requirements to judge (in the user's words):
R1: "We want a network linking them"

Reply:

````
What I understood you are asking for:
1. "We want a network linking them." -- available from DRAGON.

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

## S011

Request (turn 1): We want the communities of our bipartite TF-gene network. They must be found with the Louvain algorithm.

Requirements to judge (in the user's words):
R1: "We want the communities of our bipartite TF-gene network"

Reply:

````
What I understood you are asking for:
1. "We want the communities of our bipartite TF-gene network." -- not available here: no registered workflow produces this. CONDOR does not meet "They must be found with the Louvain algorithm.".

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want the communities of our bipartite TF-gene network.” — CONDOR does not meet "They must be found with the Louvain algorithm.".
- next step: Start a new task

## S012

Request (turn 1): We have somatic mutations for 140 tumors with the usual annotation files. We want subtypes from pathway mutation scores. Only use the primary tumors, not the metastases.

Requirements to judge (in the user's words):
R1: "We want subtypes from pathway mutation scores"

Reply:

````
What I understood you are asking for:
1. "We want subtypes from pathway mutation scores." -- available from SAMBAR.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Your request can be read 2 ways, and they lead to different workflows.
- question: Which reading should we start with?
- option: Reading 1: “somatic mutations” — SAMBAR: a cohort-level pathway mutation score matrix · Pathway-level mutation scores, then patient subtypes by clustering
- option: Reading 2 — SAMBAR: a cohort-level set of sample subtypes · Pathway-level mutation scores, then patient subtypes by clustering
- next step: Plan SAMBAR with my data
- next step: Start a new task

## S013

Request (turn 1): We have expression, motifs, PPI and miRNA targets for 60 samples. We want a TF and miRNA regulatory network. The miRNA edges must be weighted by each miRNA's measured abundance.

Requirements to judge (in the user's words):
R1: "We want a TF and miRNA regulatory network"

Reply:

````
What I understood you are asking for:
1. "We want a TF and miRNA regulatory network." -- available from PUMA.

Selected path: **PUMA**.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale. PUMA extends PANDA's message passing to miRNA regulators.

Captured request parameters:

- `mirna_file`: targets

**PUMA**: Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA.

Routing-level input modality: gene expression, coexpression.

Method premise: iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow.

PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression.

Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Workflow-specific scientific notes:

- PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Distinct declared output artifacts (availability depends on workflow options):

- `regulatory_network`: Inferred regulator-to-target associations.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: PUMA fits your goal: cohort-level TF/miRNA-gene regulatory network.
- point: Method: PANDA's message passing with miRNA regulators added.
- point: Needs: expression matrix, motif prior, PPI network, miRNA list.
- point: Produces: regulatory network (one cohort-level result).
- next step: Plan PUMA with my data
- next step: Start a new task

## S014

Request (turn 1): We have mutation calls for 160 tumors. We want patient subtypes. The clustering has to be k-means with k chosen by silhouette.

Requirements to judge (in the user's words):
R1: "We want patient subtypes"

Reply:

````
What I understood you are asking for:
1. "We want patient subtypes." -- not available here: no registered workflow produces this. SAMBAR does not meet "The clustering has to be k-means with k chosen by silhouette.".

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want patient subtypes.” — SAMBAR does not meet "The clustering has to be k-means with k chosen by silhouette.".
- next step: Start a new task

## S015

Request (turn 1): We have expression, motifs and PPI for 90 samples. We want a TF-gene network. Its edge weights must be probabilities between 0 and 1.

Requirements to judge (in the user's words):
R1: "We want a TF-gene network"

Reply:

````
What I understood you are asking for:
1. "We want a TF-gene network." -- not available here: no registered workflow produces this. PANDA does not meet "Its edge weights must be probabilities between 0 and 1.".

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a TF-gene network.” — PANDA does not meet "Its edge weights must be probabilities between 0 and 1.".
- next step: Start a new task

## S016

Request (turn 1): We have expression and methylation for 80 matched samples. We want a network linking them. Each link must come with a bootstrap confidence interval.

Requirements to judge (in the user's words):
R1: "We want a network linking them"

Reply:

````
What I understood you are asking for:
1. "We want a network linking them." -- available from DRAGON.

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

## S017

Request (turn 1): We want a partial-correlation network between expression and metabolites in 90 matched samples.
Request (turn 2): Every edge should be conditioned on all other features of both layers.

Requirements to judge (in the user's words):
R1: "Every edge should be conditioned on all other features of both layers"

Reply:

````
What I understood you are asking for:
1. "We want a partial-correlation network between expression and metabolites" -- available from DRAGON.

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

## S018

Request (turn 1): We want per-sample co-expression networks for 70 samples.
Request (turn 2): We also need the aggregate network across all samples.

Requirements to judge (in the user's words):
R1: "We also need the aggregate network across all samples"

Reply:

````
What I understood you are asking for:
1. "per-sample co-expression networks" -- available from LIONESS-COEXPRESSION or BONOBO.
2. "aggregate network across all samples" -- available from LIONESS-COEXPRESSION.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “per-sample co-expression networks” and “aggregate network across all samples”:

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

For “per-sample co-expression networks”:

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
````

Card shown with the reply:
- headline: You described 2 approaches; each is tested with a different registered workflow.
- question: Which hypothesis should we start with?
- option: LIONESS-COEXPRESSION — For “per-sample co-expression networks” and “aggregate network across all samples” · One gene co-expression network per sample; needs only expression data
- option: BONOBO — For “per-sample co-expression networks” · Per-sample co-expression with Bayesian shrinkage and a p-value per edge
- next step: Start a new task

## S019

Request (turn 1): We have expression, motifs and PPI for 75 samples. We want one TF-gene network. The motif prior we provide must be part of the estimate.

Requirements to judge (in the user's words):
R1: "We want one TF-gene network"

Reply:

````
What I understood you are asking for:
1. "We want one TF-gene network." -- available from PANDA or LIONESS-PANDA.

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
- point: Understood goal: a cohort-level TF-gene regulatory network.
- point: The registered alternatives do not fulfil the requested modeling requirement.
- question: Would one of these, without that requirement, work for you?
- option: PANDA — Widely used baseline: message passing over motif, PPI and co-expression evidence
- option: OTTER — Explicit objective (graph matching), fitted by a fixed number of gradient steps; lighter on memory
- not available: TIGER — Not runnable here (netZooR, R); Chen & Padi 2024, doi:10.1038/s41540-024-00386-w.
- not available: Werhli & Husmeier (2007) — Not runnable here (published method, no NetZoo implementation); PMID 17542777.
- next step: Start a new task

## S020

Request (turn 1): We have a bipartite TF-gene network. We want its communities and each node's core score.

Requirements to judge (in the user's words):
R1: "We want its communities and each node's core score"

Reply:

````
What I understood you are asking for:
1. "its communities" -- available from CONDOR.
2. "each node's core score" -- available from CONDOR.

Assumptions behind this recommendation (not confirmed facts):

- The bipartite TF-gene network is well-defined and available for analysis.

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

## S021

Request (turn 1): We have expression and methylation for 80 matched samples. We want a network linking them. Each link must come with a bootstrap confidence interval.

Requirements to judge (in the user's words):
R1: "We want a network linking them"

Reply:

````
What I understood you are asking for:
1. "We want a network linking them." -- not available here: no registered workflow produces this. DRAGON does not meet "Each link must come with a bootstrap confidence interval.".

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a network linking them.” — DRAGON does not meet "Each link must come with a bootstrap confidence interval.".
- next step: Start a new task

## S022

Request (turn 1): We have expression and proteomics for 100 matched samples. We want a network linking them. Each link must be conditional on all other measured features.

Requirements to judge (in the user's words):
R1: "We want a network linking them"

Reply:

````
What I understood you are asking for:
1. "We want a network linking them." -- available from DRAGON.

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

## S023

Request (turn 1): We have expression, motifs, PPI and miRNA targets for 70 samples. We want one network with TF and miRNA regulators. The miRNA edges must start from the predicted target sites.

Requirements to judge (in the user's words):
R1: "We want one network with TF and miRNA regulators"

Reply:

````
What I understood you are asking for:
1. "We want one network with TF and miRNA regulators." -- available from PUMA or LIONESS-PUMA.

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

## S024

Request (turn 1): We want a TF-gene network from expression, motifs and PPI of 66 samples.
Request (turn 2): It has to be learned without the motif prior.

Requirements to judge (in the user's words):
R1: "It has to be learned without the motif prior"

Reply:

````
What I understood you are asking for:
1. "We want a TF-gene network" -- available from PANDA, OTTER or LIONESS-PANDA.

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

**What your data allows.** PANDA, LIONESS-PANDA, OTTER and GIRAFFE need a motif prior and a PPI network, which you said you do not have ("without the motif prior").

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

## S025

Request (turn 1): We have expression, motifs, PPI and miRNA targets for 60 samples. We want a TF and miRNA regulatory network. The miRNA edges must be weighted by each miRNA's measured abundance.

Requirements to judge (in the user's words):
R1: "We want a TF and miRNA regulatory network"

Reply:

````
What I understood you are asking for:
1. "We want a TF and miRNA regulatory network." -- not available here: no registered workflow produces this. PUMA does not meet "The miRNA edges must be weighted by each miRNA's measured abundance.".

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a TF and miRNA regulatory network.” — PUMA does not meet "The miRNA edges must be weighted by each miRNA's measured abundance.".
- next step: Start a new task
