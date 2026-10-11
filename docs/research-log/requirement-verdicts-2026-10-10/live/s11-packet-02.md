## S043

Request (turn 1): With expression, motifs and PPI from 72 tumors, we want each TF's activity in each tumor, beyond what its own mRNA level shows.

Requirements to judge (in the user's words):
R1: "each TF's activity in each tumor"

Reply:

````
What I understood you are asking for:
1. "each TF's activity in each tumor, beyond what its own mRNA level shows" -- available from GIRAFFE.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **GIRAFFE** — produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: GIRAFFE — Not confirmed. Produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S044

Request (turn 1): Is there a method that finds the communities in our bipartite TF-gene network and then writes a narrative report on their biology automatically?

Requirements to judge (in the user's words):
R1: "finds the communities in our bipartite TF-gene network"
R2: "writes a narrative report on their biology automatically"

Reply:

````
What I understood you are asking for:
1. "a method that finds the communities in our bipartite TF-gene network" -- available from CONDOR.
2. "writes a narrative report on their biology automatically" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Selected path: **CONDOR**.

Your question asks for a cohort-level community assignment. **CONDOR** fits that result and scale.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: CONDOR fits your goal: cohort-level set of network communities (modules).
- point: Method: Finds TF-gene communities (modules) in a two-mode network.
- point: Needs: TF-gene (bipartite) network.
- point: Before running: threshold a PANDA or LIONESS network so its edge weights are non-negative; CONDOR then gives each node one community and a core score.
- point: Produces: set of network communities (modules) (one cohort-level result).
- not available: “writes a narrative report on their biology automatically” — The backup check matched no registered workflow to this (not confirmed).
- next step: Plan CONDOR with my data
- next step: Start a new task

## S045

Request (turn 1): We have somatic mutations for 260 tumors. Which method groups the patients into subtypes from pathway-level mutation scores?

Requirements to judge (in the user's words):
R1: "groups the patients into subtypes from pathway-level mutation scores"

Reply:

````
What I understood you are asking for:
1. "Which method groups the patients into subtypes from pathway-level mutation scores?" -- available from SAMBAR.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **SAMBAR** — produces: Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them -- with the scores, the cluster labels and the sample distance matrix.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: SAMBAR — Not confirmed. Produces: Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them -- with the scores, the cluster labels and the sample distance matrix.
- next step: Plan SAMBAR with my data
- next step: Start a new task

## S046

Request (turn 1): We have methylation, expression and proteomics from the same 95 donors. We want one network of direct partial-correlation links among all three layers jointly.

Requirements to judge (in the user's words):
R1: "one network of direct partial-correlation links among all three layers jointly"

Reply:

````
What I understood you are asking for:
1. "one network of direct partial-correlation links among all three layers jointly" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **DRAGON** — produces: One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples. A p-value and a Benjamini-Hochberg adjusted p-value for every edge (adjusted within each layer and across the layers), to filter edges by significance.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: DRAGON — Not confirmed. Produces: One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples. A p-value and a Benjamini-Hochberg adjusted p-value for every edge (adjusted…
- not available: “one network of direct partial-correlation links among all three layers jointly” — The backup check matched no registered workflow to this (not confirmed).
- next step: Plan DRAGON with my data
- next step: Start a new task

## S047

Request (turn 1): We have bulk RNA-seq of 50 tumors. Is there a method that estimates the proportion of each immune cell type in every tumor?

Requirements to judge (in the user's words):
R1: "estimates the proportion of each immune cell type in every tumor"

Reply:

````
What I understood you are asking for:
1. "Is there a method that estimates the proportion of each immune cell type in every tumor?" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
````

Card shown with the reply:
- headline: 
- next step: Start a new task

## S048

Request (turn 1): We have RNA-seq from 64 kidney biopsies plus TF motifs and a PPI network. We want one TF-gene regulatory network for the whole cohort.

Requirements to judge (in the user's words):
R1: "one TF-gene regulatory network for the whole cohort"

Reply:

````
What I understood you are asking for:
1. "one TF-gene regulatory network for the whole cohort" -- available from PANDA or OTTER.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

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

## S049

Request (turn 1): We have expression from 300 patients with drug response labels. We want a model that predicts the response of new patients.

Requirements to judge (in the user's words):
R1: "a model that predicts the response of new patients"

Reply:

````
What I understood you are asking for:
1. "a model that predicts the response of new patients" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

About "a model that predicts the response of new patients.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

If you want per-sample results to use as features, say which result you need -- per-sample networks, TF activities or subtypes -- and the data you have.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow can do this: predict outcomes for new samples.
- point: No registered workflow builds a predictive model; per-sample results can only be its features.
- not available: “a model that predicts the response of new patients” — The backup check matched no registered workflow to this (not confirmed).
- next step: Start a new task

## S050

Request (turn 1): We have a bipartite TF-gene network from an earlier PANDA run. Which method splits it into communities, with each gene in exactly one community, and finds each community's core genes?

Requirements to judge (in the user's words):
R1: "splits it into communities, with each gene in exactly one community"
R2: "finds each community's core genes"

Reply:

````
What I understood you are asking for:
1. "Which method splits it into communities, with each gene in exactly one community, and finds each community's core genes?" -- available from CONDOR.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **CONDOR** — produces: Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity. Each regulator's and gene's core score -- its share of its community's modularity -- to pick out each community's core nodes.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: CONDOR — Not confirmed. Produces: Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity. Each regulator's and gene's core score -- its share of its community's modularity -- to pick out each community's core nodes.
- next step: Plan CONDOR with my data
- next step: Start a new task

## S051

Request (turn 1): We have expression, motifs and PPI from 100 samples. We want a regulatory network.

Requirements to judge (in the user's words):
R1: "a regulatory network"
Also judge `ambiguity` for this session.

Reply:

````
What I understood you are asking for:
1. "We want a regulatory network." -- available from PANDA, PUMA, OTTER or GIRAFFE.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 6 registered methods can build a regulatory network; they differ in scale (one network for all samples or one per sample) and in their modeling assumptions.
- point: Understood goal: a regulatory network.
- point: LIONESS-PANDA and LIONESS-PUMA give one network per sample; PANDA, OTTER, GIRAFFE and PUMA give one across all samples.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: LIONESS-PANDA — One TF-gene network per sample, plus the cohort network · Lets you compare samples, or relate them to outcomes such as survival · Slower: it reruns PANDA once per sample
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- option: PUMA — One TF + miRNA network across all your samples · Pick it if the regulators include miRNAs · Also needs miRNA list
- option: LIONESS-PUMA — One TF + miRNA network per sample, plus the cohort network · Pick it if the regulators include miRNAs · Also needs miRNA list
- next step: Start a new task

## S052

Request (turn 1): We have CRISPR knockout screen counts from 18 samples. Which method scores how essential each gene is?

Requirements to judge (in the user's words):
R1: "scores how essential each gene is"

Reply:

````
What I understood you are asking for:
1. "Which method scores how essential each gene is?" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **SAMBAR** — produces: Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them -- with the scores, the cluster labels and the sample distance matrix.
- **PANDA** — produces: One weighted TF-to-gene regulatory network across all the samples given.
- **PUMA** — produces: One weighted network of how TFs and miRNAs regulate genes, across all samples.
- **LIONESS-PANDA** — produces: One TF-gene network per sample, plus the aggregate network.
- **LIONESS-PUMA** — produces: One TF/miRNA-gene network per sample, plus the aggregate network.
- **OTTER** — produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- **GIRAFFE** — produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: SAMBAR — Not confirmed. Produces: Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them -- with the scores, the cluster labels and the sample distance matrix.
- option: PANDA — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all the samples given.
- option: PUMA — Not confirmed. Produces: One weighted network of how TFs and miRNAs regulate genes, across all samples.
- option: LIONESS-PANDA — Not confirmed. Produces: One TF-gene network per sample, plus the aggregate network.
- option: LIONESS-PUMA — Not confirmed. Produces: One TF/miRNA-gene network per sample, plus the aggregate network.
- option: OTTER — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- option: GIRAFFE — Not confirmed. Produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.
- not available: “Which method scores how essential each gene is?” — The backup check matched no registered workflow to this (not confirmed).
- next step: Start a new task

## S053

Request (turn 1): From single-cell RNA-seq of 6,000 cells plus TF motifs and PPI, we want a separate TF-gene network for each cell.

Requirements to judge (in the user's words):
R1: "a separate TF-gene network for each cell"

Reply:

````
What I understood you are asking for:
1. "a separate TF-gene network for each cell" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: I could not validate an interpretation of this request, so nothing was selected.
- point: This does not mean your question is unclear; restating the result you want usually helps.
- not available: “a separate TF-gene network for each cell” — The backup check matched no registered workflow to this (not confirmed).
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task

## S054

Request (turn 1): We have ATAC-seq peaks from 30 samples. We want to discover de novo motifs enriched in the peaks.

Requirements to judge (in the user's words):
R1: "discover de novo motifs enriched in the peaks"

Reply:

````
What I understood you are asking for:
1. "discover de novo motifs enriched in the peaks" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: I could not validate an interpretation of this request, so nothing was selected.
- point: This does not mean your question is unclear; restating the result you want usually helps.
- not available: “discover de novo motifs enriched in the peaks” — The backup check matched no registered workflow to this (not confirmed).
- not available: SPIDER (chromatin-filtered prior) — Not registered here; SPIDER is in netZooR and netZooM. The filtered prior can then be used with PANDA or OTTER.
- next step: Start a new task

## S055

Request (turn 1): We have RNA-seq from 64 kidney biopsies plus motifs. We want one regulatory network in which long non-coding RNAs, not TFs, are the regulators of each gene.

Requirements to judge (in the user's words):
R1: "one regulatory network in which long non-coding RNAs, not TFs, are the regulators of each gene"

Reply:

````
What I understood you are asking for:
1. "one regulatory network in which long non-coding RNAs, not TFs, are the regulators of each gene" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Based on what you said — "We want one regulatory network in which long non-coding RNAs, not TFs, are the regulators of each gene." — **PUMA** fits better: the regulators include miRNAs or similar short non-coding RNAs that repress or degrade target transcripts after transcription.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale.

**PUMA** (recommend) — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list. Produces inferred regulator-to-target associations (one cohort-level result).

Conditional assumptions to confirm:
- This reads the molecules you describe as miRNAs. Confirm that, and that you have a miRNA-target prior and a list of the miRNAs, before analysis.

Other compatible option(s):
- If you need a TF-only regulatory network instead: **PANDA**, **OTTER**.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

Should I use PUMA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 4 registered methods can build a cohort-level regulatory network; they differ in their modeling assumptions.
- point: Understood goal: a cohort-level regulatory network from expression data, a motif prior and a PPI network.
- point: Recommended: PUMA, from what you said.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: PUMA — Fits what you said: the regulators include miRNAs · One TF + miRNA network across all your samples · Also needs miRNA list [Recommended]
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- not available: “one regulatory network in which long non-coding RNAs, not TFs, are the… — The backup check matched no registered workflow to this (not confirmed).
- next step: Start a new task

## S056

Request (turn 1): We have ATAC-seq peaks from 30 samples. We want to discover de novo motifs enriched in the peaks.

Requirements to judge (in the user's words):
R1: "discover de novo motifs enriched in the peaks"

Reply:

````
What I understood you are asking for:
1. "discover de novo motifs enriched in the peaks" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: I could not validate an interpretation of this request, so nothing was selected.
- point: This does not mean your question is unclear; restating the result you want usually helps.
- not available: “discover de novo motifs enriched in the peaks” — The backup check matched no registered workflow to this (not confirmed).
- not available: SPIDER (chromatin-filtered prior) — Not registered here; SPIDER is in netZooR and netZooM. The filtered prior can then be used with PANDA or OTTER.
- next step: Start a new task

## S057

Request (turn 1): OK, then pseudo-bulk per donor is fine: 24 donors, one TF-gene network per donor.

Requirements to judge (in the user's words):
R1: "one TF-gene network per donor"

Reply:

````
What I understood you are asking for:
1. "one TF-gene network per donor" -- available from LIONESS-PANDA.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **LIONESS-PANDA** — produces: One TF-gene network per sample, plus the aggregate network.
- **PANDA** — produces: One weighted TF-to-gene regulatory network across all the samples given.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: LIONESS-PANDA — Not confirmed. Produces: One TF-gene network per sample, plus the aggregate network.
- option: PANDA — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all the samples given.
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S058

Request (turn 1): We have a bipartite TF-gene network from an earlier PANDA run. We want overlapping communities, where a gene can belong to several communities at once.

Requirements to judge (in the user's words):
R1: "overlapping communities, where a gene can belong to several communities at once"

Reply:

````
What I understood you are asking for:
1. "overlapping communities, where a gene can belong to several communities at once" -- available from CONDOR.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

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

## S059

Request (turn 1): From expression, motifs and PPI of 60 tumors, we want each tumor's TF-gene network, and then a web dashboard where clinicians can browse them interactively.

Requirements to judge (in the user's words):
R1: "each tumor's TF-gene network"
R2: "a web dashboard where clinicians can browse them interactively"

Reply:

````
What I understood you are asking for:
1. "each tumor's TF-gene network" -- available from LIONESS-PANDA.
2. "a web dashboard where clinicians can browse them interactively" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 60 tumors, 61 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 60 tumors, 61 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- not available: “a web dashboard where clinicians can browse them interactively” — The backup check matched no registered workflow to this (not confirmed).
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S060

Request (turn 1): We have RNA-seq from 64 kidney biopsies plus TF motifs and a PPI network. Is there a method that infers one TF-gene regulatory network for the whole cohort?

Requirements to judge (in the user's words):
R1: "one TF-gene regulatory network for the whole cohort"

Reply:

````
What I understood you are asking for:
1. "one TF-gene regulatory network for the whole cohort" -- available from PANDA or OTTER.
2. "a method that infers one TF-gene regulatory network for the whole cohort" -- available from PANDA or OTTER.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **PANDA** — produces: One weighted TF-to-gene regulatory network across all the samples given.
- **OTTER** — produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- **GIRAFFE** — produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: PANDA — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all the samples given.
- option: OTTER — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- option: GIRAFFE — Not confirmed. Produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.
- next step: Start a new task

## S061

Request (turn 1): We have RNA-seq from 45 heart biopsies but no motif or PPI data at all. We want one TF-gene regulatory network.

Requirements to judge (in the user's words):
R1: "one TF-gene regulatory network"

Reply:

````
What I understood you are asking for:
1. "We want one TF-gene regulatory network." -- available from PANDA, PUMA, OTTER or GIRAFFE.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **PANDA** — produces: One weighted TF-to-gene regulatory network across all the samples given.
- **OTTER** — produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- **GIRAFFE** — produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

**Data your question needs.** A TF-level answer needs a motif prior and a PPI network, which you said you do not have ("no motif or PPI data at all").

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- point: Needs a motif prior and a PPI network, which you said you do not have.
- question: Which one do you want to look at?
- option: PANDA — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all the samples given.
- option: OTTER — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- option: GIRAFFE — Not confirmed. Produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.
- next step: Start a new task

## S062

Request (turn 1): We have RNA-seq from 45 heart biopsies but no motif or PPI data at all. We want one TF-gene regulatory network.

Requirements to judge (in the user's words):
R1: "one TF-gene regulatory network"

Reply:

````
What I understood you are asking for:
1. "We want one TF-gene regulatory network." -- available from PANDA, PUMA, OTTER or GIRAFFE.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **PANDA** — produces: One weighted TF-to-gene regulatory network across all the samples given.
- **OTTER** — produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- **GIRAFFE** — produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

**Data your question needs.** A TF-level answer needs a motif prior and a PPI network, which you said you do not have ("no motif or PPI data at all").

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- point: Needs a motif prior and a PPI network, which you said you do not have.
- question: Which one do you want to look at?
- option: PANDA — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all the samples given.
- option: OTTER — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- option: GIRAFFE — Not confirmed. Produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.
- next step: Start a new task

## S063

Request (turn 1): We have expression from 70 colon samples. We want a TF-gene network for each sample.

Requirements to judge (in the user's words):
R1: "a TF-gene network for each sample"

Reply:

````
What I understood you are asking for:
1. "a TF-gene network for each sample" -- available from LIONESS-PANDA.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **LIONESS-PANDA** — produces: One TF-gene network per sample, plus the aggregate network.
- **PANDA** — produces: One weighted TF-to-gene regulatory network across all the samples given.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

**Data your question needs.** A TF-level answer needs a motif prior and a PPI network, which you said you do not have ("We have expression from 70 colon samples.").

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- point: Needs a motif prior and a PPI network, which you said you do not have.
- question: Which one do you want to look at?
- option: LIONESS-PANDA — Not confirmed. Produces: One TF-gene network per sample, plus the aggregate network.
- option: PANDA — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all the samples given.
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S064

Request (turn 1): We have expression from 140 smokers and non-smokers. We want the co-expression with the smoking effect separated out, and also a differential expression table of smokers versus non-smokers.

Requirements to judge (in the user's words):
R1: "the co-expression with the smoking effect separated out"
R2: "a differential expression table of smokers versus non-smokers"

Reply:

````
What I understood you are asking for:
1. "the co-expression with the smoking effect separated out" -- the backup check matched no registered workflow to this (not confirmed).
2. "a differential expression table of smokers versus non-smokers" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **COBRA** — produces: The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: COBRA — Not confirmed. Produces: The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix.
- not available: “the co-expression with the smoking effect separated out” — The backup check matched no registered workflow to this (not confirmed).
- not available: “a differential expression table of smokers versus non-smokers” — The backup check matched no registered workflow to this (not confirmed).
- next step: Start a new task

## S065

Request (turn 1): Which method gives each TF's activity per sample from our expression, motifs and PPI, and also aligns our raw reads to the genome first?

Requirements to judge (in the user's words):
R1: "each TF's activity per sample"
R2: "aligns our raw reads to the genome"

Reply:

````
What I understood you are asking for:
1. "Which method gives each TF's activity per sample from our expression, motifs and PPI, and also aligns our raw reads to the genome first?" -- partly available: GIRAFFE gives part of it; no registered workflow produces the rest.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **GIRAFFE** — produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: GIRAFFE — Not confirmed. Produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S066

Request (turn 1): We want to compare regulatory networks between our responders and non-responders, using expression, motifs and PPI from 66 patients.

Requirements to judge (in the user's words):
R1: "compare regulatory networks between our responders and non-responders"
Also judge `ambiguity` for this session.

Reply:

````
What I understood you are asking for:
1. "compare regulatory networks between our responders and non-responders" -- available from PANDA, PUMA or OTTER's output plus a step you run outside NetZoo: One run per condition on the same genes and priors, then compare; two aggregate networks give no per-sample spread for a test.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **PANDA**, **PUMA**, **OTTER** — Targeting scores: a regulator's outdegree or a gene's indegree summarizes the network per regulator or per gene; comparing them between networks built separately for each condition shows regulators whose targeting changes. Comparing conditions needs one run per condition on matched inputs (the same genes and the same motif and PPI priors); edge weights are comparable only within that shared setup.
- **PANDA** — For per-sample scores to test against clinical variables, use LIONESS-PANDA instead.
- **PUMA** — For per-sample scores to test against clinical variables, use LIONESS-PUMA instead.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.
- **OTTER** — OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.
- **GIRAFFE** — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

For your question ("compare regulatory networks between our responders and non-responders"):
- **PANDA**, **PUMA** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use the per-sample (LIONESS) version and test between the groups.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each sample gets its own network, so each edge weight or targeting score can be tested between the groups across samples -- for example with a linear model such as limma.
- **OTTER** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use a per-sample method such as LIONESS-PANDA and test between the groups.
- **GIRAFFE** — The activity matrix compares TF activity, not network wiring, between the conditions; test each TF's activity between them (paired when the same individuals give both).
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 6 registered methods can build a TF-gene regulatory network; they differ in scale (one network for all samples or one per sample) and in their modeling assumptions.
- point: Understood goal: a TF-gene regulatory network.
- point: LIONESS-PANDA and LIONESS-PUMA give one network per sample; PANDA, OTTER, GIRAFFE and PUMA give one across all samples.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- point: Your stated concern is answered per method in the full explanation.
- point: Your question: whether the groups or time points differ; the reply says what PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, OTTER and GIRAFFE give toward it and the step after each.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: LIONESS-PANDA — One TF-gene network per sample, plus the cohort network · Lets you compare samples, or relate them to outcomes such as survival · Slower: it reruns PANDA once per sample
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- option: PUMA — One TF + miRNA network across all your samples · Also adds miRNA regulators · Pick it if the regulators include miRNAs · Also needs miRNA list
- option: LIONESS-PUMA — One TF + miRNA network per sample, plus the cohort network · Also adds miRNA regulators · Pick it if the regulators include miRNAs · Also needs miRNA list
- next step: Start a new task

## S067

Request (turn 1): We have methylation, expression and proteomics from the same 95 donors. We want one network of direct partial-correlation links among all three layers jointly.

Requirements to judge (in the user's words):
R1: "one network of direct partial-correlation links among all three layers jointly"

Reply:

````
What I understood you are asking for:
1. "one network of direct partial-correlation links among all three layers jointly" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

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
- not available: “one network of direct partial-correlation links among all three layers jointly” — The backup check matched no registered workflow to this (not confirmed).
- next step: Plan DRAGON with my data
- next step: Start a new task

## S068

Request (turn 1): We have expression from 140 smokers and non-smokers. We want the co-expression with the smoking effect separated out, and also a differential expression table of smokers versus non-smokers.

Requirements to judge (in the user's words):
R1: "the co-expression with the smoking effect separated out"
R2: "a differential expression table of smokers versus non-smokers"

Reply:

````
What I understood you are asking for:
1. "the co-expression with the smoking effect separated out" -- the backup check matched no registered workflow to this (not confirmed).
2. "a differential expression table of smokers versus non-smokers" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

For “differential expression table of smokers versus non-smokers”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

For your question ("a differential expression table of smokers versus non-smokers"):
- **COBRA** — Put the group label in COBRA's design matrix: it returns a co-expression component for that variable -- the part of each gene pair's co-expression associated with the group -- alongside components for any other covariates you include, such as batch.
Note: Some component values fall outside -1 to 1; read them as contributions, not correlations. Deciding which gene pairs differ beyond chance is a separate analysis.

No files were inspected and no analysis ran.

What measurement would let you distinguish the remaining explanation?
````

Card shown with the reply:
- headline: COBRA fits your goal: cohort-level co-expression network.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- point: Your question: whether the groups or time points differ; the reply says what COBRA give toward it and the step after each.
- not available: “the co-expression with the smoking effect separated out” — The backup check matched no registered workflow to this (not confirmed).
- not available: “a differential expression table of smokers versus non-smokers” — The backup check matched no registered workflow to this (not confirmed).
- not available: “differential expression table of smokers versus non-smokers” — No registered workflow meets this; it needs a clearer measurement or an external method.
- next step: Start a new task

## S069

Request (turn 1): We have RNA-seq from 64 kidney biopsies plus motifs. We want one regulatory network in which long non-coding RNAs, not TFs, are the regulators of each gene.

Requirements to judge (in the user's words):
R1: "one regulatory network in which long non-coding RNAs, not TFs, are the regulators of each gene"

Reply:

````
What I understood you are asking for:
1. "one regulatory network in which long non-coding RNAs, not TFs, are the regulators of each gene" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Based on what you said — "We want one regulatory network in which long non-coding RNAs, not TFs, are the regulators of each gene." — **PUMA** fits better: the regulators include miRNAs or similar short non-coding RNAs that repress or degrade target transcripts after transcription.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale.

**PUMA** (recommend) — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list. Produces inferred regulator-to-target associations (one cohort-level result).

Conditional assumptions to confirm:
- This reads the molecules you describe as miRNAs. Confirm that, and that you have a miRNA-target prior and a list of the miRNAs, before analysis.

Other compatible option(s):
- If you need a TF-only regulatory network instead: **PANDA**, **OTTER**.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

Should I use PUMA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 4 registered methods can build a cohort-level regulatory network; they differ in their modeling assumptions.
- point: Understood goal: a cohort-level regulatory network from expression data, a motif prior and a PPI network.
- point: Recommended: PUMA, from what you said.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: PUMA — Fits what you said: the regulators include miRNAs · One TF + miRNA network across all your samples · Also needs miRNA list [Recommended]
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- not available: “one regulatory network in which long non-coding RNAs, not TFs, are the… — The backup check matched no registered workflow to this (not confirmed).
- next step: Start a new task

## S070

Request (turn 1): From expression, motifs and PPI of 110 lymphoma samples, which method gives a separate TF-gene network for each sample?

Requirements to judge (in the user's words):
R1: "a separate TF-gene network for each sample"

Reply:

````
What I understood you are asking for:
1. "which method gives a separate TF-gene network for each sample?" -- available from LIONESS-PANDA, LIONESS-PUMA or LIONESS-DRAGON.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **LIONESS-PANDA** — produces: One TF-gene network per sample, plus the aggregate network.
- **PANDA** — produces: One weighted TF-to-gene regulatory network across all the samples given.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: LIONESS-PANDA — Not confirmed. Produces: One TF-gene network per sample, plus the aggregate network.
- option: PANDA — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all the samples given.
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S071

Request (turn 1): We have somatic mutations for 260 tumors. Which method groups the patients into subtypes from pathway-level mutation scores?

Requirements to judge (in the user's words):
R1: "groups the patients into subtypes from pathway-level mutation scores"

Reply:

````
What I understood you are asking for:
1. "Which method groups the patients into subtypes from pathway-level mutation scores?" -- available from SAMBAR.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **SAMBAR** — produces: Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them -- with the scores, the cluster labels and the sample distance matrix.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: SAMBAR — Not confirmed. Produces: Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them -- with the scores, the cluster labels and the sample distance matrix.
- next step: Plan SAMBAR with my data
- next step: Start a new task

## S072

Request (turn 1): Sorry, I meant a separate network for each patient.

Requirements to judge (in the user's words):
R1: "a separate network for each patient"

Reply:

````
What I understood you are asking for:
1. "a separate network for each patient" -- available from LIONESS-PANDA, LIONESS-PUMA, LIONESS-DRAGON or BONOBO.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files. Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**What your data allows.** LIONESS-PANDA and PANDA also need an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs.
- point: Produces: regulatory network (cohort-level and per-sample).
- point: Your request names only the data I described; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior and a PPI network?
- option: Only the data I described — Ask what the data you named can give instead
- option: I also have a motif prior and a PPI network — Continues with the workflows this reply names
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S073

Request (turn 1): We have a bipartite TF-gene network from an earlier PANDA run. We want to split it into communities, with each gene in exactly one community, and find each community's core genes.

Requirements to judge (in the user's words):
R1: "split it into communities, with each gene in exactly one community"
R2: "find each community's core genes"

Reply:

````
What I understood you are asking for:
1. "split it into communities" -- available from CONDOR.
2. "find each community's core genes" -- available from CONDOR.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

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

## S074

Request (turn 1): We have expression from 140 smokers and non-smokers. We want the co-expression with the smoking effect separated out, and also a differential expression table of smokers versus non-smokers.

Requirements to judge (in the user's words):
R1: "the co-expression with the smoking effect separated out"
R2: "a differential expression table of smokers versus non-smokers"

Reply:

````
What I understood you are asking for:
1. "the co-expression with the smoking effect separated out" -- the backup check matched no registered workflow to this (not confirmed).
2. "a differential expression table of smokers versus non-smokers" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **COBRA** — produces: The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: COBRA — Not confirmed. Produces: The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix.
- not available: “the co-expression with the smoking effect separated out” — The backup check matched no registered workflow to this (not confirmed).
- not available: “a differential expression table of smokers versus non-smokers” — The backup check matched no registered workflow to this (not confirmed).
- next step: Start a new task

## S075

Request (turn 1): Actually, each gene should be allowed to sit in several communities at once.

Requirements to judge (in the user's words):
R1: "each gene should be allowed to sit in several communities at once"

Reply:

````
What I understood you are asking for:
1. "each gene should be allowed to sit in several communities at once" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

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
- not available: “each gene should be allowed to sit in several communities at once” — The backup check matched no registered workflow to this (not confirmed).
- next step: Plan CONDOR with my data
- next step: Start a new task

## S076

Request (turn 1): We want gene modules from a TF-gene network, but we have not built the network yet; we only have expression, motifs and PPI from 55 samples.

Requirements to judge (in the user's words):
R1: "gene modules from a TF-gene network"

Reply:

````
What I understood you are asking for:
1. "We want gene modules from a TF-gene network" -- available from LIONESS-PANDA or LIONESS-PUMA.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

Your request does not say what the network should connect; the options above assume regulator-to-target associations. Every option above also needs a TF-motif prior and a protein-interaction prior. If you meant gene-to-gene associations, **BONOBO** and **LIONESS-COEXPRESSION** need only the input you named.

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

## S077

Request (turn 1): Is there a method that finds the communities in our bipartite TF-gene network and then writes a narrative report on their biology automatically?

Requirements to judge (in the user's words):
R1: "finds the communities in our bipartite TF-gene network"
R2: "writes a narrative report on their biology automatically"

Reply:

````
What I understood you are asking for:
1. "a method that finds the communities in our bipartite TF-gene network" -- available from CONDOR.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **CONDOR** — produces: Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity. Each regulator's and gene's core score -- its share of its community's modularity -- to pick out each community's core nodes.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: CONDOR — Not confirmed. Produces: Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity. Each regulator's and gene's core score -- its share of its community's modularity -- to pick out each community's core nodes.
- next step: Plan CONDOR with my data
- next step: Start a new task

## S078

Request (turn 1): We have somatic mutations for 260 tumors. Which method groups the patients into subtypes from pathway-level mutation scores?

Requirements to judge (in the user's words):
R1: "groups the patients into subtypes from pathway-level mutation scores"

Reply:

````
What I understood you are asking for:
1. "Which method groups the patients into subtypes from pathway-level mutation scores?" -- available from SAMBAR.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

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

## S079

Request (turn 1): We have RNA-seq from 64 kidney biopsies plus TF motifs and a PPI network. We want one TF-gene regulatory network for the whole cohort.

Requirements to judge (in the user's words):
R1: "one TF-gene regulatory network for the whole cohort"

Reply:

````
What I understood you are asking for:
1. "one TF-gene regulatory network for the whole cohort" -- available from PANDA or OTTER.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **PANDA** — produces: One weighted TF-to-gene regulatory network across all the samples given.
- **OTTER** — produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- **GIRAFFE** — produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: PANDA — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all the samples given.
- option: OTTER — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- option: GIRAFFE — Not confirmed. Produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.
- next step: Start a new task

## S080

Request (turn 1): We have ATAC-seq peaks from 30 samples. We want to discover de novo motifs enriched in the peaks.

Requirements to judge (in the user's words):
R1: "discover de novo motifs enriched in the peaks"

Reply:

````
What I understood you are asking for:
1. "discover de novo motifs enriched in the peaks" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: I could not validate an interpretation of this request, so nothing was selected.
- point: This does not mean your question is unclear; restating the result you want usually helps.
- not available: “discover de novo motifs enriched in the peaks” — The backup check matched no registered workflow to this (not confirmed).
- not available: SPIDER (chromatin-filtered prior) — Not registered here; SPIDER is in netZooR and netZooM. The filtered prior can then be used with PANDA or OTTER.
- next step: Start a new task

## S081

Request (turn 1): We have a bipartite TF-gene network from an earlier PANDA run. Is there a method that finds overlapping communities, where a gene can belong to several communities at once?

Requirements to judge (in the user's words):
R1: "overlapping communities, where a gene can belong to several communities at once"

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

## S082

Request (turn 1): With expression, motifs and PPI from 72 tumors, we want each TF's activity in each tumor, beyond what its own mRNA level shows.

Requirements to judge (in the user's words):
R1: "each TF's activity in each tumor"

Reply:

````
What I understood you are asking for:
1. "each TF's activity in each tumor, beyond what its own mRNA level shows." -- available from GIRAFFE.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "beyond what its own mRNA level shows" — GIRAFFE fits each TF's activity (`tf_activity_matrix`) from the expression of its target genes and the TF-TF protein interactions; the TF's own mRNA level is not an input to it. If the TF's gene is among the expression rows it still counts as an ordinary target, so its activity is not tied to its mRNA rather than independent of it.

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

## S083

Request (turn 1): We have RNA-seq from 64 kidney biopsies plus motifs. We want one regulatory network in which long non-coding RNAs, not TFs, are the regulators of each gene.

Requirements to judge (in the user's words):
R1: "one regulatory network in which long non-coding RNAs, not TFs, are the regulators of each gene"

Reply:

````
What I understood you are asking for:
1. "one regulatory network in which long non-coding RNAs, not TFs, are the regulators of each gene" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **PANDA** — produces: One weighted TF-to-gene regulatory network across all the samples given.
- **PUMA** — produces: One weighted network of how TFs and miRNAs regulate genes, across all samples.
- **OTTER** — produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- **GIRAFFE** — produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: PANDA — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all the samples given.
- option: PUMA — Not confirmed. Produces: One weighted network of how TFs and miRNAs regulate genes, across all samples.
- option: OTTER — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- option: GIRAFFE — Not confirmed. Produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.
- not available: “one regulatory network in which long non-coding RNAs, not TFs, are the… — The backup check matched no registered workflow to this (not confirmed).
- next step: Start a new task

## S084

Request (turn 1): From single-cell RNA-seq of 6,000 cells plus TF motifs and PPI, which method gives a separate TF-gene network for each cell?

Requirements to judge (in the user's words):
R1: "a separate TF-gene network for each cell"

Reply:

````
What I understood you are asking for:
1. "which method gives a separate TF-gene network for each cell?" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **PANDA** — produces: One weighted TF-to-gene regulatory network across all the samples given.
- **LIONESS-PANDA** — produces: One TF-gene network per sample, plus the aggregate network.
- **OTTER** — produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- **GIRAFFE** — produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: PANDA — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all the samples given.
- option: LIONESS-PANDA — Not confirmed. Produces: One TF-gene network per sample, plus the aggregate network.
- option: OTTER — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- option: GIRAFFE — Not confirmed. Produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.
- not available: “which method gives a separate TF-gene network for each cell?” — The backup check matched no registered workflow to this (not confirmed).
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task
